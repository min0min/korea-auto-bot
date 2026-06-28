import math
import pandas as pd

from .config import (
    MA20_SLOPE_DAYS,
    VOLUME_SPIKE_RATIO,
    GENERAL_TAKE_PROFIT,
    SIDECAR_TAKE_PROFIT,
    STOP_LOSS,
    MAX_HOLD_DAYS,
    SIDECAR_SELL_DATES,
    SIDECAR_BUY_DATES,
)


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["ma20"] = df["close"].rolling(20).mean()
    df["ma60"] = df["close"].rolling(60).mean()
    df["ma20_slope"] = df["ma20"] - df["ma20"].shift(MA20_SLOPE_DAYS)
    df["volume_ratio"] = df["volume"] / df["volume"].shift(1)
    df["trade_value"] = df["close"] * df["volume"]
    df["atr_like"] = (df["high"] - df["low"]) / df["close"]
    return df


def is_trend_alive(row) -> bool:
    return bool(row["ma20_slope"] > 0 and row["close"] > row["ma60"])


def is_general_buy(row) -> bool:
    return bool(
        is_trend_alive(row)
        and row["volume_ratio"] >= VOLUME_SPIKE_RATIO
    )


def is_sell_sidecar_date(date_value: str) -> bool:
    return str(date_value) in SIDECAR_SELL_DATES


def is_buy_sidecar_date(date_value: str) -> bool:
    return str(date_value) in SIDECAR_BUY_DATES


def is_sidecar_buy(row) -> bool:
    return bool(is_sell_sidecar_date(row["date"]) and is_trend_alive(row))


def latest_status(df: pd.DataFrame) -> dict:
    df = add_indicators(df)

    if len(df) < 65:
        return {"ready": False, "error": "데이터 부족"}

    row = df.iloc[-1]
    ma20_up = bool(row["ma20_slope"] > 0)
    above_ma60 = bool(row["close"] > row["ma60"])
    volume_spike = bool(row["volume_ratio"] >= VOLUME_SPIKE_RATIO)
    trend_alive = bool(ma20_up and above_ma60)
    general_buy = bool(trend_alive and volume_spike)
    sidecar_buy = bool(is_sell_sidecar_date(row["date"]) and trend_alive)

    return {
        "ready": True,
        "date": str(row["date"]),
        "close": float(row["close"]),
        "ma20": float(row["ma20"]),
        "ma60": float(row["ma60"]),
        "ma20_up": ma20_up,
        "price_above_ma60": above_ma60,
        "volume_ratio": float(row["volume_ratio"]) if not math.isnan(row["volume_ratio"]) else 0,
        "volume_spike": volume_spike,
        "trade_value": float(row["trade_value"]),
        "trend_alive": trend_alive,
        "general_buy": general_buy,
        "sidecar_buy": sidecar_buy,
        "signal": general_buy or sidecar_buy,
    }


def entry_reasons(row, entry_type):
    return {
        "entry_type": entry_type,
        "ma20_up": bool(row["ma20_slope"] > 0),
        "price_above_ma60": bool(row["close"] > row["ma60"]),
        "volume_ratio": round(float(row["volume_ratio"]), 2),
        "volume_spike": bool(row["volume_ratio"] >= VOLUME_SPIKE_RATIO),
        "sell_sidecar": is_sell_sidecar_date(row["date"]),
    }


def simulate_exit(df, entry_i: int, entry_type: str):
    entry = float(df.iloc[entry_i]["open"])
    take_profit = SIDECAR_TAKE_PROFIT if entry_type == "SIDECAR_BUY" else GENERAL_TAKE_PROFIT

    exit_i = min(entry_i + MAX_HOLD_DAYS, len(df) - 1)
    exit_price = float(df.iloc[exit_i]["close"])
    reason = "MAX_HOLD"

    for j in range(entry_i, exit_i + 1):
        row = df.iloc[j]
        high = float(row["high"])
        low = float(row["low"])
        date = str(row["date"])

        if is_buy_sidecar_date(date):
            exit_i = j
            exit_price = entry
            reason = "BUY_SIDECAR_BREAK_EVEN"
            break

        if low <= entry * (1 + STOP_LOSS):
            exit_i = j
            exit_price = entry * (1 + STOP_LOSS)
            reason = "STOP_LOSS"
            break

        if high >= entry * (1 + take_profit):
            exit_i = j
            exit_price = entry * (1 + take_profit)
            reason = "TAKE_PROFIT"
            break

    pnl = (exit_price - entry) / entry

    return {
        "entry_date": str(df.iloc[entry_i]["date"]),
        "exit_date": str(df.iloc[exit_i]["date"]),
        "entry_price": round(entry, 2),
        "exit_price": round(exit_price, 2),
        "pnl_pct": round(pnl * 100, 2),
        "exit_reason": reason,
        "hold_days": int(exit_i - entry_i + 1),
    }


def backtest_strategy(df: pd.DataFrame) -> list:
    df = add_indicators(df)
    trades = []
    last_exit_i = -1

    for i in range(65, len(df) - 1):
        if i <= last_exit_i:
            continue

        row = df.iloc[i]
        entry_type = None

        if is_sidecar_buy(row):
            entry_type = "SIDECAR_BUY"
        elif is_general_buy(row):
            entry_type = "GENERAL_BUY"

        if entry_type is None:
            continue

        entry_i = i + 1
        result = simulate_exit(df, entry_i, entry_type)

        trade = {
            "signal_date": str(row["date"]),
            "entry_type": entry_type,
            "reasons": entry_reasons(row, entry_type),
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


def equity_curve(trades: list) -> list:
    cur = 0
    result = []
    for t in sorted(trades, key=lambda x: x["exit_date"]):
        cur += float(t["pnl_pct"])
        result.append({
            "date": t["exit_date"],
            "equity": round(cur, 2),
            "pnl": float(t["pnl_pct"]),
        })
    return result


def monthly_summary(trades: list) -> list:
    bucket = {}
    for t in trades:
        month = str(t["exit_date"])[:6]
        bucket.setdefault(month, []).append(t)

    rows = []
    for month, ts in sorted(bucket.items(), reverse=True):
        s = summarize_trades(ts)
        rows.append({
            "month": month,
            **s,
        })
    return rows
