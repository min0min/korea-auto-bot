from dataclasses import dataclass
from .sidecar_events import get_sell_events, get_buy_dates
from .ai_score import score_candidate


@dataclass
class Params:
    min_ai_score: float = 60
    max_picks: int = 3
    entry_timing: str = "next_open"
    first_tp: float = 0.02
    first_ratio: float = 0.50
    final_tp: float = 0.04
    stop_loss: float = -0.02
    max_hold_days: int = 3
    exit_on_ma20: bool = True
    exit_on_buy_sidecar: bool = True
    use_trend_filter: bool = False


def get_row_by_date(df, date):
    rows = df.index[df["date"] == date].tolist()
    if not rows:
        return None, None
    i = rows[0]
    return i, df.iloc[i]


def get_entry_index_and_price(df, signal_i: int, params: Params):
    if params.entry_timing == "next_open":
        entry_i = signal_i + 1
        if entry_i >= len(df):
            return None, None
        return entry_i, float(df.iloc[entry_i]["open"])
    return signal_i, float(df.iloc[signal_i]["close"])


def simulate_exit(df, entry_i: int, entry_price: float, params: Params):
    exit_i = min(entry_i + params.max_hold_days, len(df) - 1)
    first_tp_done = False
    first_tp_price = None
    final_price = float(df.iloc[exit_i]["close"])
    final_reason = "MAX_HOLD"

    for j in range(entry_i, exit_i + 1):
        row = df.iloc[j]
        date = str(row["date"])
        high = float(row["high"])
        low = float(row["low"])
        close = float(row["close"])

        if params.exit_on_buy_sidecar and date in get_buy_dates():
            exit_i = j
            final_price = entry_price
            final_reason = "BUY_SIDECAR_BREAK_EVEN"
            break

        if not first_tp_done and low <= entry_price * (1 + params.stop_loss):
            exit_i = j
            final_price = entry_price * (1 + params.stop_loss)
            final_reason = "FULL_STOP_LOSS"
            break

        if not first_tp_done and high >= entry_price * (1 + params.first_tp):
            first_tp_done = True
            first_tp_price = entry_price * (1 + params.first_tp)

        if first_tp_done and high >= entry_price * (1 + params.final_tp):
            exit_i = j
            final_price = entry_price * (1 + params.final_tp)
            final_reason = "FINAL_TAKE_PROFIT"
            break

        if first_tp_done and params.exit_on_ma20 and close < float(row["ma20"]):
            exit_i = j
            final_price = close
            final_reason = "REST_MA20_BREAK"
            break

        final_price = close

    if first_tp_done:
        pnl_first = params.first_ratio * ((first_tp_price - entry_price) / entry_price)
        pnl_rest = (1 - params.first_ratio) * ((final_price - entry_price) / entry_price)
        total_pnl = pnl_first + pnl_rest
        exit_reason = "FIRST_TP+" + final_reason
    else:
        total_pnl = (final_price - entry_price) / entry_price
        exit_reason = final_reason

    return {
        "exit_date": str(df.iloc[exit_i]["date"]),
        "entry_price": round(entry_price, 2),
        "first_tp_done": first_tp_done,
        "first_tp_price": round(first_tp_price, 2) if first_tp_price else None,
        "final_price": round(final_price, 2),
        "pnl_pct": round(total_pnl * 100, 2),
        "exit_reason": exit_reason,
        "hold_days": int(exit_i - entry_i + 1),
    }


def summarize_trades(trades):
    if not trades:
        return {"total":0,"wins":0,"losses":0,"win_rate":0,"total_pnl":0,"avg_pnl":0,"profit_factor":0,"mdd":0,"best":0,"worst":0}

    pnls = [float(t["pnl_pct"]) for t in trades]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p <= 0]
    gp = sum(wins)
    gl = abs(sum(losses))
    pf = gp / gl if gl > 0 else 999

    cur, peak, mdd = 0, -10**9, 0
    for p in pnls:
        cur += p
        peak = max(peak, cur)
        mdd = min(mdd, cur - peak)

    return {
        "total": len(trades),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": round(len(wins)/len(trades)*100, 1),
        "total_pnl": round(sum(pnls), 2),
        "avg_pnl": round(sum(pnls)/len(pnls), 2),
        "profit_factor": round(pf, 2),
        "mdd": round(mdd, 2),
        "best": round(max(pnls), 2),
        "worst": round(min(pnls), 2),
    }


def equity_curve(trades):
    cur = 0
    curve = []
    for t in sorted(trades, key=lambda x: x["exit_date"]):
        cur += float(t["pnl_pct"])
        curve.append({"date": t["exit_date"], "equity": round(cur, 2), "pnl": float(t["pnl_pct"])})
    return curve


def monthly_summary(trades):
    bucket = {}
    for t in trades:
        month = str(t["exit_date"])[:6]
        bucket.setdefault(month, []).append(t)
    return [{"month":m, **summarize_trades(ts)} for m, ts in sorted(bucket.items(), reverse=True)]


def run_backtest(stock_data, params: Params):
    trades = []
    event_reports = []

    for event in sorted(get_sell_events(), key=lambda x: x["date"]):
        date = event["date"]
        candidates = []

        for ticker, item in stock_data.items():
            df = item["df"]
            name = item["name"]
            idx, row = get_row_by_date(df, date)
            if row is None or idx < 130:
                continue

            score_pack = score_candidate(row, use_trend_filter=params.use_trend_filter)
            candidates.append({
                "ticker": ticker,
                "name": name,
                "date": date,
                "score": score_pack["score"],
                "score_detail": score_pack,
                "index": idx,
            })

        candidates = sorted(candidates, key=lambda x: x["score"], reverse=True)
        selected = [c for c in candidates if c["score"] >= params.min_ai_score][:params.max_picks]

        event_reports.append({
            "event": event,
            "top_candidates": candidates[:10],
            "selected": selected,
        })

        for c in selected:
            df = stock_data[c["ticker"]]["df"]
            entry_i, entry_price = get_entry_index_and_price(df, c["index"], params)
            if entry_i is None:
                continue
            result = simulate_exit(df, entry_i, entry_price, params)
            trades.append({
                "ticker": c["ticker"],
                "name": c["name"],
                "signal_date": date,
                "entry_date": str(df.iloc[entry_i]["date"]),
                "entry_type": "BACKTEST_LAB_SIDE_CAR_AI",
                "ai_score": c["score"],
                "score_detail": c["score_detail"],
                "event": event,
                **result,
            })

    trades = sorted(trades, key=lambda x: x["entry_date"], reverse=True)
    return trades, event_reports, summarize_trades(trades), equity_curve(trades), monthly_summary(trades)
