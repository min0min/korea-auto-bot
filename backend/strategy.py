import pandas as pd

from .config import (
    MA20_SLOPE_DAYS,
    USE_TREND_FILTER,
    SIDECAR_ENTRY_TIMING,
    SIDECAR_HALF_TAKE_PROFIT,
    SIDECAR_STOP_LOSS,
    SIDECAR_MAX_HOLD_DAYS,
    SIDECAR_PARTIAL_RATIO,
)
from .sidecar_events import get_sell_dates, get_buy_dates, get_event_by_date


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["ma20"] = df["close"].rolling(20).mean()
    df["ma60"] = df["close"].rolling(60).mean()
    df["ma20_slope"] = df["ma20"] - df["ma20"].shift(MA20_SLOPE_DAYS)
    df["volume_ratio"] = df["volume"] / df["volume"].shift(1)
    df["trade_value"] = df["close"] * df["volume"]
    return df


def is_sell_sidecar_date(date_value: str) -> bool:
    return str(date_value) in get_sell_dates()


def is_buy_sidecar_date(date_value: str) -> bool:
    return str(date_value) in get_buy_dates()


def trend_alive(row) -> bool:
    return bool(row["ma20_slope"] > 0 and row["close"] > row["ma60"])


def sidecar_entry_signal(row) -> bool:
    if not is_sell_sidecar_date(row["date"]):
        return False

    if USE_TREND_FILTER:
        return trend_alive(row)

    return True


def latest_status(df: pd.DataFrame) -> dict:
    df = add_indicators(df)

    if len(df) < 65:
        return {"ready": False, "error": "데이터 부족"}

    row = df.iloc[-1]
    date = str(row["date"])
    ma20_up = bool(row["ma20_slope"] > 0)
    above_ma60 = bool(row["close"] > row["ma60"])
    sell_today = is_sell_sidecar_date(date)
    buy_today = is_buy_sidecar_date(date)
    signal = sidecar_entry_signal(row)

    return {
        "ready": True,
        "date": date,
        "close": float(row["close"]),
        "ma20": float(row["ma20"]),
        "ma60": float(row["ma60"]),
        "ma20_up": ma20_up,
        "price_above_ma60": above_ma60,
        "trend_alive": bool(ma20_up and above_ma60),
        "volume_ratio": float(row["volume_ratio"]) if pd.notna(row["volume_ratio"]) else 0,
        "sell_sidecar_today": sell_today,
        "buy_sidecar_today": buy_today,
        "sidecar_signal": signal,
        "event": get_event_by_date(date),
        "signal": signal,
    }


def get_entry_index_and_price(df, signal_i: int):
    if SIDECAR_ENTRY_TIMING == "next_open":
        entry_i = signal_i + 1
        entry_price = float(df.iloc[entry_i]["open"])
    else:
        entry_i = signal_i
        entry_price = float(df.iloc[entry_i]["close"])

    return entry_i, entry_price


def simulate_sidecar_exit(df, entry_i: int, entry_price: float):
    exit_i = min(entry_i + SIDECAR_MAX_HOLD_DAYS, len(df) - 1)

    partial_done = False
    partial_price = None
    final_price = float(df.iloc[exit_i]["close"])
    final_reason = "MAX_HOLD"
    partial_reason = None

    for j in range(entry_i, exit_i + 1):
        row = df.iloc[j]
        date = str(row["date"])
        high = float(row["high"])
        low = float(row["low"])

        if is_buy_sidecar_date(date):
            exit_i = j
            final_price = entry_price
            final_reason = "BUY_SIDECAR_BREAK_EVEN"
            break

        if not partial_done and low <= entry_price * (1 + SIDECAR_STOP_LOSS):
            exit_i = j
            final_price = entry_price * (1 + SIDECAR_STOP_LOSS)
            final_reason = "FULL_STOP_LOSS"
            break

        if not partial_done and high >= entry_price * (1 + SIDECAR_HALF_TAKE_PROFIT):
            partial_done = True
            partial_price = entry_price * (1 + SIDECAR_HALF_TAKE_PROFIT)
            partial_reason = "HALF_TAKE_PROFIT"

        if partial_done and low <= entry_price:
            exit_i = j
            final_price = entry_price
            final_reason = "REST_BREAK_EVEN"
            break

        final_price = float(row["close"])

    if partial_done:
        pnl_half = SIDECAR_PARTIAL_RATIO * ((partial_price - entry_price) / entry_price)
        pnl_rest = (1 - SIDECAR_PARTIAL_RATIO) * ((final_price - entry_price) / entry_price)
        total_pnl = pnl_half + pnl_rest
        exit_reason = f"{partial_reason}+{final_reason}"
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


def backtest_strategy(df: pd.DataFrame) -> list:
    df = add_indicators(df)
    trades = []
    last_exit_i = -1

    for i in range(65, len(df)):
        if i <= last_exit_i:
            continue

        row = df.iloc[i]

        if not sidecar_entry_signal(row):
            continue

        if SIDECAR_ENTRY_TIMING == "next_open" and i >= len(df) - 1:
            continue

        entry_i, entry_price = get_entry_index_and_price(df, i)
        result = simulate_sidecar_exit(df, entry_i, entry_price)

        trade = {
            "signal_date": str(row["date"]),
            "entry_date": str(df.iloc[entry_i]["date"]),
            "entry_type": "OFFICIAL_SELL_SIDECAR_REVERSE_BUY",
            "ma20_up": bool(row["ma20_slope"] > 0),
            "price_above_ma60": bool(row["close"] > row["ma60"]),
            "trend_filter_pass": bool(trend_alive(row)),
            "sidecar_event": get_event_by_date(row["date"]),
            "sell_sidecar": True,
            **result,
        }

        trades.append(trade)

        exit_indices = df.index[df["date"] == trade["exit_date"]].tolist()
        if exit_indices:
            last_exit_i = exit_indices[0]

    return trades


def summarize_trades(trades: list) -> dict:
    if not trades:
        return {
            "total": 0,
            "wins": 0,
            "losses": 0,
            "win_rate": 0,
            "total_pnl": 0,
            "avg_pnl": 0,
            "profit_factor": 0,
            "mdd": 0,
            "best": 0,
            "worst": 0,
        }

    pnls = [float(t["pnl_pct"]) for t in trades]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p <= 0]

    gross_profit = sum(wins)
    gross_loss = abs(sum(losses))
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else 999

    equity = []
    cur = 0
    for p in pnls:
        cur += p
        equity.append(cur)

    peak = -10**9
    mdd = 0
    for e in equity:
        peak = max(peak, e)
        dd = e - peak
        mdd = min(mdd, dd)

    return {
        "total": len(trades),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": round(len(wins) / len(trades) * 100, 1),
        "total_pnl": round(sum(pnls), 2),
        "avg_pnl": round(sum(pnls) / len(pnls), 2),
        "profit_factor": round(profit_factor, 2),
        "mdd": round(mdd, 2),
        "best": round(max(pnls), 2),
        "worst": round(min(pnls), 2),
    }


def monthly_summary(trades: list) -> list:
    bucket = {}
    for t in trades:
        month = str(t["exit_date"])[:6]
        bucket.setdefault(month, []).append(t)

    rows = []
    for month, ts in sorted(bucket.items(), reverse=True):
        s = summarize_trades(ts)
        rows.append({"month": month, **s})
    return rows
