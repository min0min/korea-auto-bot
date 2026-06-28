from datetime import datetime, timedelta
import pandas as pd
from pykrx import stock

from .config import TICKERS, BACKTEST_YEARS


def _to_yyyymmdd(dt):
    return dt.strftime("%Y%m%d")


def get_ohlcv(ticker: str, years: int = BACKTEST_YEARS) -> pd.DataFrame:
    """
    pykrx에서 한국 주식 일봉을 가져온다.
    토스 API 사용 X.
    Railway IP 변경과 무관하게 백테스트 가능.
    """
    end = datetime.now()
    start = end - timedelta(days=365 * years + 120)

    df = stock.get_market_ohlcv_by_date(
        _to_yyyymmdd(start),
        _to_yyyymmdd(end),
        ticker,
    )

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
    })

    # pykrx 버전에 따라 날짜 컬럼명이 Date일 수 있음
    if "date" not in df.columns:
        first_col = df.columns[0]
        df = df.rename(columns={first_col: "date"})

    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y%m%d")

    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["open", "high", "low", "close", "volume"])
    return df.reset_index(drop=True)


def load_all():
    data = {}
    for ticker, name in TICKERS.items():
        data[ticker] = {
            "name": name,
            "df": get_ohlcv(ticker),
        }
    return data
