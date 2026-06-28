from functools import lru_cache

from .config import (
    AUTO_SIDECAR,
    KOSPI200_INDEX_CODE,
    SIDECAR_SELL_THRESHOLD,
    SIDECAR_BUY_THRESHOLD,
    MANUAL_SIDECAR_SELL_DATES,
    MANUAL_SIDECAR_BUY_DATES,
)
from .data_source import get_index_ohlcv


@lru_cache(maxsize=1)
def detect_sidecar_dates():
    """
    자동 사이드카 후보일 감지.

    공식 사이드카:
    - 코스피는 KOSPI200 선물 가격이 ±5% 이상 상태로 1분 지속 시 발동.
    - 여기서는 무료 일봉 데이터 기반 백테스트용으로 KOSPI200 지수 저가/고가가 전일 종가 대비 ±5%를 넘은 날을 후보일로 자동 감지.

    나중에 KRX 공시/선물 1분봉으로 교체 가능.
    """
    sell_dates = set(MANUAL_SIDECAR_SELL_DATES)
    buy_dates = set(MANUAL_SIDECAR_BUY_DATES)
    rows = []

    if AUTO_SIDECAR:
        df = get_index_ohlcv(KOSPI200_INDEX_CODE)

        df["prev_close"] = df["close"].shift(1)
        df["low_change"] = df["low"] / df["prev_close"] - 1
        df["high_change"] = df["high"] / df["prev_close"] - 1

        for _, row in df.dropna().iterrows():
            date = str(row["date"])
            low_change = float(row["low_change"])
            high_change = float(row["high_change"])

            sell = low_change <= SIDECAR_SELL_THRESHOLD
            buy = high_change >= SIDECAR_BUY_THRESHOLD

            if sell:
                sell_dates.add(date)

            if buy:
                buy_dates.add(date)

            if sell or buy:
                rows.append({
                    "date": date,
                    "type": "SELL" if sell else "BUY",
                    "low_change_pct": round(low_change * 100, 2),
                    "high_change_pct": round(high_change * 100, 2),
                    "close": round(float(row["close"]), 2),
                })

    return {
        "sell_dates": sorted(sell_dates),
        "buy_dates": sorted(buy_dates),
        "events": sorted(rows, key=lambda x: x["date"], reverse=True),
    }


def get_sell_sidecar_dates():
    return set(detect_sidecar_dates()["sell_dates"])


def get_buy_sidecar_dates():
    return set(detect_sidecar_dates()["buy_dates"])


def get_sidecar_events():
    return detect_sidecar_dates()["events"]
