import pandas as pd


def normalize_candles(raw):
    candles = raw.get("candles") or raw.get("data") or raw.get("result") or raw
    df = pd.DataFrame(candles)

    rename_map = {
        "date": "date",
        "tradingDate": "date",
        "baseDate": "date",
        "open": "open",
        "openPrice": "open",
        "high": "high",
        "highPrice": "high",
        "low": "low",
        "lowPrice": "low",
        "close": "close",
        "closePrice": "close",
        "volume": "volume",
        "tradeVolume": "volume",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    required = ["open", "high", "low", "close", "volume"]
    for col in required:
        if col not in df.columns:
            raise ValueError(f"캔들 데이터에 {col} 컬럼이 없습니다. 실제 응답 필드명 확인 필요.")

    for col in required:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    if "date" not in df.columns:
        df["date"] = range(len(df))

    return df.dropna(subset=required).reset_index(drop=True)


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
        return {
            "ready": False,
            "ma20_up": False,
            "price_above_ma60": False,
            "volume_spike": False,
            "signal": False,
        }

    last = df.iloc[-1]
    ma20_up = bool(last["ma20_slope_5"] > 0)
    price_above_ma60 = bool(last["close"] > last["ma60"])
    volume_spike = bool(last["volume_ratio"] >= 2.0)

    return {
        "ready": True,
        "close": float(last["close"]),
        "ma20": float(last["ma20"]),
        "ma60": float(last["ma60"]),
        "volume_ratio": float(last["volume_ratio"]),
        "ma20_up": ma20_up,
        "price_above_ma60": price_above_ma60,
        "volume_spike": volume_spike,
        "signal": ma20_up and price_above_ma60 and volume_spike,
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
            "signal_date": df.iloc[i].get("date", i),
            "entry_date": df.iloc[entry_i].get("date", entry_i),
            "exit_date": df.iloc[exit_i].get("date", exit_i),
            "entry_price": round(entry_price, 2),
            "exit_price": round(exit_price, 2),
            "pnl_pct": round(pnl * 100, 2),
            "reason": exit_reason,
        })

    return trades
