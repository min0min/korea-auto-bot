import pandas as pd


def _first_col(df, candidates):
    for c in candidates:
        if c in df.columns:
            return c
    return None


def normalize_candles(raw):
    candles = raw.get("candles") or raw.get("data") or raw.get("result") or raw.get("items") or raw
    df = pd.DataFrame(candles)

    date_col = _first_col(df, ["date", "tradingDate", "baseDate", "localDate", "time"])
    open_col = _first_col(df, ["open", "openPrice", "openingPrice"])
    high_col = _first_col(df, ["high", "highPrice", "highestPrice"])
    low_col = _first_col(df, ["low", "lowPrice", "lowestPrice"])
    close_col = _first_col(df, ["close", "closePrice", "tradePrice", "currentPrice", "lastPrice"])
    volume_col = _first_col(df, ["volume", "tradeVolume", "accumulatedTradingVolume", "accTradeVolume"])

    missing = []
    for name, col in {
        "open": open_col,
        "high": high_col,
        "low": low_col,
        "close": close_col,
        "volume": volume_col,
    }.items():
        if col is None:
            missing.append(name)

    if missing:
        raise ValueError(f"캔들 필드명 매핑 실패: {missing} / 실제 컬럼={list(df.columns)}")

    out = pd.DataFrame({
        "date": df[date_col] if date_col else range(len(df)),
        "open": pd.to_numeric(df[open_col], errors="coerce"),
        "high": pd.to_numeric(df[high_col], errors="coerce"),
        "low": pd.to_numeric(df[low_col], errors="coerce"),
        "close": pd.to_numeric(df[close_col], errors="coerce"),
        "volume": pd.to_numeric(df[volume_col], errors="coerce"),
    })

    return out.dropna().reset_index(drop=True)


def add_indicators(df):
    df = df.copy()
    df["ma20"] = df["close"].rolling(20).mean()
    df["ma60"] = df["close"].rolling(60).mean()
    df["ma20_slope_5"] = df["ma20"] - df["ma20"].shift(5)
    df["volume_ratio"] = df["volume"] / df["volume"].shift(1)
    return df


def latest_status(df):
    df = add_indicators(df)
    if len(df) < 65:
        return {"ready": False}

    last = df.iloc[-1]
    ma20_up = bool(last["ma20_slope_5"] > 0)
    above_ma60 = bool(last["close"] > last["ma60"])
    volume_spike = bool(last["volume_ratio"] >= 2.0)

    return {
        "ready": True,
        "date": str(last["date"]),
        "close": float(last["close"]),
        "ma20": float(last["ma20"]),
        "ma60": float(last["ma60"]),
        "volume_ratio": float(last["volume_ratio"]),
        "ma20_up": ma20_up,
        "price_above_ma60": above_ma60,
        "volume_spike": volume_spike,
        "signal": ma20_up and above_ma60 and volume_spike,
    }


def backtest_general(df, max_hold_days=2, take_profit=0.04, stop_loss=-0.02):
    df = add_indicators(df)
    trades = []

    for i in range(65, len(df) - 1):
        row = df.iloc[i]
        signal = (
            row["ma20_slope_5"] > 0
            and row["close"] > row["ma60"]
            and row["volume_ratio"] >= 2.0
        )

        if not signal:
            continue

        entry_i = i + 1
        entry_price = float(df.iloc[entry_i]["open"])
        exit_price = float(entry_price)
        exit_reason = "MAX_HOLD"
        exit_i = min(entry_i + max_hold_days, len(df) - 1)

        for j in range(entry_i, exit_i + 1):
            high = float(df.iloc[j]["high"])
            low = float(df.iloc[j]["low"])

            if low <= entry_price * (1 + stop_loss):
                exit_price = entry_price * (1 + stop_loss)
                exit_reason = "STOP_LOSS"
                exit_i = j
                break

            if high >= entry_price * (1 + take_profit):
                exit_price = entry_price * (1 + take_profit)
                exit_reason = "TAKE_PROFIT"
                exit_i = j
                break

            exit_price = float(df.iloc[j]["close"])

        pnl = (exit_price - entry_price) / entry_price

        trades.append({
            "signal_date": str(df.iloc[i]["date"]),
            "entry_date": str(df.iloc[entry_i]["date"]),
            "exit_date": str(df.iloc[exit_i]["date"]),
            "entry_price": round(entry_price, 2),
            "exit_price": round(exit_price, 2),
            "pnl_pct": round(pnl * 100, 2),
            "reason": exit_reason,
        })

    return trades


def summarize_trades(trades):
    if not trades:
        return {"total": 0, "win_rate": 0, "total_pnl": 0, "avg_pnl": 0}

    pnls = [t["pnl_pct"] for t in trades]
    wins = [p for p in pnls if p > 0]
    return {
        "total": len(trades),
        "win_rate": round(len(wins) / len(trades) * 100, 1),
        "total_pnl": round(sum(pnls), 2),
        "avg_pnl": round(sum(pnls) / len(pnls), 2),
    }
