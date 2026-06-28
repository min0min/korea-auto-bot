from .config import (
    MIN_AI_SCORE,
    MAX_PICKS_PER_EVENT,
    SIDECAR_ENTRY_TIMING,
    PARTIAL_TAKE_PROFIT,
    PARTIAL_RATIO,
    STOP_LOSS,
    MAX_HOLD_DAYS,
    EXIT_ON_MA20_BREAK,
    EXIT_ON_BUY_SIDECAR,
)
from .sidecar_events import get_sell_events, get_buy_dates
from .ai_score import score_candidate


def get_row_by_date(df, date):
    rows = df.index[df["date"] == date].tolist()
    if not rows:
        return None, None
    i = rows[0]
    return i, df.iloc[i]


def get_entry_index_and_price(df, signal_i: int):
    if SIDECAR_ENTRY_TIMING == "next_open":
        entry_i = signal_i + 1
        if entry_i >= len(df):
            return None, None
        return entry_i, float(df.iloc[entry_i]["open"])
    return signal_i, float(df.iloc[signal_i]["close"])


def simulate_exit(df, entry_i: int, entry_price: float):
    exit_i = min(entry_i + MAX_HOLD_DAYS, len(df) - 1)

    partial_done = False
    partial_price = None
    final_price = float(df.iloc[exit_i]["close"])
    final_reason = "MAX_HOLD"

    for j in range(entry_i, exit_i + 1):
        row = df.iloc[j]
        date = str(row["date"])
        high = float(row["high"])
        low = float(row["low"])

        if EXIT_ON_BUY_SIDECAR and date in get_buy_dates():
            exit_i = j
            final_price = entry_price
            final_reason = "BUY_SIDECAR_BREAK_EVEN"
            break

        if not partial_done and low <= entry_price * (1 + STOP_LOSS):
            exit_i = j
            final_price = entry_price * (1 + STOP_LOSS)
            final_reason = "FULL_STOP_LOSS"
            break

        if not partial_done and high >= entry_price * (1 + PARTIAL_TAKE_PROFIT):
            partial_done = True
            partial_price = entry_price * (1 + PARTIAL_TAKE_PROFIT)

        if partial_done and EXIT_ON_MA20_BREAK and row["close"] < row["ma20"]:
            exit_i = j
            final_price = float(row["close"])
            final_reason = "REST_MA20_BREAK"
            break

        final_price = float(row["close"])

    if partial_done:
        pnl_partial = PARTIAL_RATIO * ((partial_price - entry_price) / entry_price)
        pnl_rest = (1 - PARTIAL_RATIO) * ((final_price - entry_price) / entry_price)
        total_pnl = pnl_partial + pnl_rest
        exit_reason = "PARTIAL_TP+" + final_reason
    else:
        total_pnl = (final_price - entry_price) / entry_price
        exit_reason = final_reason

    return {
        "exit_date": str(df.iloc[exit_i]["date"]),
        "entry_price": round(entry_price, 2),
        "partial_done": partial_done,
        "partial_price": round(partial_price, 2) if partial_price else None,
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


def monthly_summary(trades):
    bucket = {}
    for t in trades:
        month = str(t["exit_date"])[:6]
        bucket.setdefault(month, []).append(t)
    return [{"month":m, **summarize_trades(ts)} for m, ts in sorted(bucket.items(), reverse=True)]


def backtest_ai_sidecar(stock_data):
    """
    이벤트 1개당 전체 유니버스 점수 계산 → 상위 N개만 진입.
    기존처럼 종목마다 무조건 들어가는 방식 제거.
    """
    trades = []
    event_reports = []

    for event in sorted(get_sell_events(), key=lambda x: x["date"]):
        date = event["date"]
        candidates = []

        for ticker, item in stock_data.items():
            df = item["df"]
            name = item["name"]
            idx, row = get_row_by_date(df, date)
            if row is None or idx < 65:
                continue

            score_pack = score_candidate(row)

            candidates.append({
                "ticker": ticker,
                "name": name,
                "date": date,
                "score": score_pack["score"],
                "score_detail": score_pack,
                "index": idx,
            })

        candidates = sorted(candidates, key=lambda x: x["score"], reverse=True)
        selected = [c for c in candidates if c["score"] >= MIN_AI_SCORE][:MAX_PICKS_PER_EVENT]

        event_reports.append({
            "event": event,
            "top_candidates": candidates[:10],
            "selected": selected,
        })

        for c in selected:
            df = stock_data[c["ticker"]]["df"]
            entry_i, entry_price = get_entry_index_and_price(df, c["index"])
            if entry_i is None:
                continue

            result = simulate_exit(df, entry_i, entry_price)
            trades.append({
                "ticker": c["ticker"],
                "name": c["name"],
                "signal_date": date,
                "entry_date": str(df.iloc[entry_i]["date"]),
                "entry_type": "AI_SCORE_SIDE_CAR_PICK",
                "ai_score": c["score"],
                "score_detail": c["score_detail"],
                "event": c["date"],
                **result,
            })

    return trades, event_reports
