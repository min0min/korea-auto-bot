import os

UNIVERSE_MODE = os.getenv("UNIVERSE_MODE", "large_cap").lower()

LARGE_CAP_TICKERS = {
    "005930": "삼성전자",
    "000660": "SK하이닉스",
    "005380": "현대차",
    "000270": "기아",
    "012330": "현대모비스",
    "068270": "셀트리온",
    "005490": "POSCO홀딩스",
    "035420": "NAVER",
    "051910": "LG화학",
    "006400": "삼성SDI",
    "207940": "삼성바이오로직스",
    "028260": "삼성물산",
    "105560": "KB금융",
    "055550": "신한지주",
    "086790": "하나금융지주",
    "003550": "LG",
    "066570": "LG전자",
    "096770": "SK이노베이션",
    "034730": "SK",
    "032830": "삼성생명",
}

FOCUS_TICKERS = {
    "005930": "삼성전자",
    "000660": "SK하이닉스",
    "000250": "삼천당제약",
    "012330": "현대모비스",
    "000270": "기아",
}

def parse_custom_tickers():
    raw = os.getenv("CUSTOM_TICKERS", "")
    result = {}
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        if ":" in item:
            code, name = item.split(":", 1)
            result[code.strip()] = name.strip()
        else:
            result[item] = item
    return result

if UNIVERSE_MODE == "focus":
    TICKERS = FOCUS_TICKERS
elif UNIVERSE_MODE == "custom":
    TICKERS = parse_custom_tickers() or LARGE_CAP_TICKERS
else:
    TICKERS = LARGE_CAP_TICKERS

BACKTEST_YEARS = int(os.getenv("BACKTEST_YEARS", "10"))
MA20_SLOPE_DAYS = int(os.getenv("MA20_SLOPE_DAYS", "5"))
RSI_PERIOD = int(os.getenv("RSI_PERIOD", "14"))

EXTRA_SELL_SIDECAR_DATES = [
    x.strip() for x in os.getenv("EXTRA_SELL_SIDECAR_DATES", "").split(",") if x.strip()
]
EXTRA_BUY_SIDECAR_DATES = [
    x.strip() for x in os.getenv("EXTRA_BUY_SIDECAR_DATES", "").split(",") if x.strip()
]
