from functools import lru_cache
from .config import EXTRA_SELL_SIDECAR_DATES, EXTRA_BUY_SIDECAR_DATES

# 공식/언론 보도 기반 내장 이벤트 DB.
# 주의: 실전에서는 KRX 공시/분봉 선물 데이터로 자동 보강 예정.
# 현재 버전은 "일봉 근사 감지"가 아니라 "확인된 이벤트일 기반"으로 백테스트한다.
DEFAULT_EVENTS = [
    {
        "date": "20250623",
        "market": "KOSPI",
        "side": "SELL",
        "time": "09:46",
        "source": "reported",
        "note": "KOSPI sell-side sidecar reported",
    },
    {
        "date": "20251105",
        "market": "KOSPI",
        "side": "SELL",
        "time": "09:46",
        "source": "reported",
        "note": "KOSPI sell-sidecar reported",
    },
    {
        "date": "20260608",
        "market": "KOSPI",
        "side": "SELL",
        "time": "09:34",
        "source": "reported",
        "note": "KOSPI sell-sidecar reported",
    },
    {
        "date": "20260610",
        "market": "KOSPI",
        "side": "SELL",
        "time": "13:17",
        "source": "reported",
        "note": "KOSPI sell-sidecar reported",
    },
    {
        "date": "20260612",
        "market": "KOSPI",
        "side": "BUY",
        "time": "-",
        "source": "reported",
        "note": "KOSPI buy-sidecar reported as previous trading day before Jun 15",
    },
    {
        "date": "20260615",
        "market": "KOSPI",
        "side": "BUY",
        "time": "09:06",
        "source": "reported",
        "note": "KOSPI buy-sidecar reported",
    },
    {
        "date": "20260626",
        "market": "KOSPI",
        "side": "SELL",
        "time": "11:12",
        "source": "reported",
        "note": "KOSPI sell-sidecar reported",
    },
]


@lru_cache(maxsize=1)
def get_events():
    events = list(DEFAULT_EVENTS)

    for d in EXTRA_SELL_SIDECAR_DATES:
        events.append({
            "date": d,
            "market": "KOSPI",
            "side": "SELL",
            "time": "-",
            "source": "extra_env",
            "note": "Extra sell-sidecar date from Railway Variables",
        })

    for d in EXTRA_BUY_SIDECAR_DATES:
        events.append({
            "date": d,
            "market": "KOSPI",
            "side": "BUY",
            "time": "-",
            "source": "extra_env",
            "note": "Extra buy-sidecar date from Railway Variables",
        })

    # 중복 제거
    seen = set()
    unique = []
    for e in sorted(events, key=lambda x: (x["date"], x["side"])):
        key = (e["date"], e["side"], e["market"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(e)

    return sorted(unique, key=lambda x: x["date"], reverse=True)


def get_sell_dates():
    return {e["date"] for e in get_events() if e["side"] == "SELL"}


def get_buy_dates():
    return {e["date"] for e in get_events() if e["side"] == "BUY"}


def get_event_by_date(date_value):
    date_value = str(date_value)
    return [e for e in get_events() if e["date"] == date_value]
