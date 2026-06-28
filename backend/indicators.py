import pandas as pd


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss.replace(0, 1e-9)
    return 100 - (100 / (1 + rs))


def add_indicators(df: pd.DataFrame, ma_slope_days: int = 5, rsi_period: int = 14) -> pd.DataFrame:
    df = df.copy()
    df["ma5"] = df["close"].rolling(5).mean()
    df["ma20"] = df["close"].rolling(20).mean()
    df["ma60"] = df["close"].rolling(60).mean()
    df["ma20_slope"] = df["ma20"] - df["ma20"].shift(ma_slope_days)
    df["volume_ratio"] = df["volume"] / df["volume"].shift(1)
    df["trade_value"] = df["close"] * df["volume"]
    df["rsi"] = rsi(df["close"], rsi_period)
    df["atr_like"] = (df["high"] - df["low"]) / df["close"]
    df["drop_3d"] = df["close"] / df["close"].shift(3) - 1
    df["dist_ma20"] = df["close"] / df["ma20"] - 1
    df["dist_ma60"] = df["close"] / df["ma60"] - 1
    return df
