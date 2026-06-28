from datetime import datetime, timedelta
import pandas as pd
from pykrx import stock

from .config import BACKTEST_YEARS


def _to_yyyymmdd(dt):
    return dt.strftime("%Y%m%d")


def get_date_range(years: int = BACKTEST_YEARS):
    end = datetime.now()
    start = end - timedelta(days=365 * years + 180)
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


def resolve_index_code(index_code: str) -> str:
    """
    pykrx 버전에 따라 KOSPI200 지수 코드 조회가 깨지는 경우가 있어서
    자동 탐색 + fallback 방식으로 처리한다.
    """
    if index_code and index_code != "auto":
        return index_code

    # 1) pykrx가 제공하는 지수 목록에서 코스피200 이름 탐색
    try:
        tickers = stock.get_index_ticker_list(market="KOSPI")
        for code in tickers:
            try:
                name = stock.get_index_ticker_name(code)
                normalized = name.replace(" ", "").upper()
                if "코스피200" in normalized or "KOSPI200" in normalized:
                    return code
            except Exception:
                continue
    except Exception:
        pass

    # 2) 많이 쓰이는 KOSPI200 코드 후보
    for code in ["1028", "2001"]:
        try:
            start, end = get_date_range(1)
            test = stock.get_index_ohlcv_by_date(start, end, code)
            if test is not None and not test.empty:
                return code
        except Exception:
            continue

    # 3) 최후 fallback: KOSPI 지수
    return "1001"


def get_index_ohlcv(index_code: str, years: int = BACKTEST_YEARS) -> pd.DataFrame:
    start, end = get_date_range(years)

    tried = []
    candidates = [resolve_index_code(index_code), "1028", "2001", "1001"]

    df = None
    used_code = None

    for code in candidates:
        if code in tried:
            continue
        tried.append(code)

        try:
            temp = stock.get_index_ohlcv_by_date(start, end, code)
            if temp is not None and not temp.empty:
                df = temp
                used_code = code
                break
        except Exception:
            continue

    if df is None or df.empty:
        raise RuntimeError(f"지수 데이터를 가져오지 못했습니다. 시도한 코드={tried}")

    df = df.reset_index()
    df = df.rename(columns={
        "날짜": "date",
        "시가": "open",
        "고가": "high",
        "저가": "low",
        "종가": "close",
        "거래량": "volume",
        "거래대금": "value",
        "상장시가총액": "market_cap",
    })

    if "date" not in df.columns:
        first_col = df.columns[0]
        df = df.rename(columns={first_col: "date"})

    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y%m%d")
    df["index_code"] = used_code

    for col in ["open", "high", "low", "close"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df.dropna(subset=["open", "high", "low", "close"]).reset_index(drop=True)
