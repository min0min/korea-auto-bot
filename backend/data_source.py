from datetime import datetime, timedelta
import pandas as pd
from pykrx import stock

from .config import BACKTEST_YEARS


def _to_yyyymmdd(dt):
    return dt.strftime("%Y%m%d")


def get_date_range(years: int = BACKTEST_YEARS):
    end = datetime.now()
    start = end - timedelta(days=365 * years + 240)
    return _to_yyyymmdd(start), _to_yyyymmdd(end)


def get_ohlcv(ticker: str, years: int = BACKTEST_YEARS) -> pd.DataFrame:
    start, end = get_date_range(years)
    df = stock.get_market_ohlcv_by_date(start, end, ticker)

    if df is None or df.empty:
        raise RuntimeError(f"{ticker} 일봉 데이터를 가져오지 못했습니다.")

    df = df.reset_index()
    df = df.rename(columns={
        "날짜": "date",
        "시가": "open",
        "고가": "high",
        "저가": "low",
        "종가": "close",
        "거래량": "volume",
        "거래대금": "value",
        "등락률": "change_pct",
    })

    if "date" not in df.columns:
        first_col = df.columns[0]
        df = df.rename(columns={first_col: "date"})

    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y%m%d")

    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    if "value" in df.columns:
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
    else:
        df["value"] = df["close"] * df["volume"]

    return df.dropna(subset=["open", "high", "low", "close", "volume"]).reset_index(drop=True)
