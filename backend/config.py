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

# 자동 사이드카 감지 설정
AUTO_SIDECAR = os.getenv("AUTO_SIDECAR", "true").lower() == "true"
SIDECAR_DETECTOR = os.getenv("SIDECAR_DETECTOR", "kospi200_daily_proxy")

# KOSPI200 지수 일봉 기반 근사 감지
# 공식 발동은 선물 1분 지속 조건이지만, 백테스트 단계에서는 일봉 저가/고가로 후보일 자동 감지
SIDECAR_SELL_THRESHOLD = float(os.getenv("SIDECAR_SELL_THRESHOLD", "-0.05"))
SIDECAR_BUY_THRESHOLD = float(os.getenv("SIDECAR_BUY_THRESHOLD", "0.05"))

# pykrx KOSPI200 index ticker
KOSPI200_INDEX_CODE = os.getenv("KOSPI200_INDEX_CODE", "auto")

MA20_SLOPE_DAYS = int(os.getenv("MA20_SLOPE_DAYS", "5"))
USE_TREND_FILTER = os.getenv("USE_TREND_FILTER", "true").lower() == "true"

SIDECAR_ENTRY_TIMING = os.getenv("SIDECAR_ENTRY_TIMING", "close").lower()
SIDECAR_HALF_TAKE_PROFIT = float(os.getenv("SIDECAR_HALF_TAKE_PROFIT", "0.02"))
SIDECAR_STOP_LOSS = float(os.getenv("SIDECAR_STOP_LOSS", "-0.02"))
SIDECAR_MAX_HOLD_DAYS = int(os.getenv("SIDECAR_MAX_HOLD_DAYS", "2"))
SIDECAR_PARTIAL_RATIO = float(os.getenv("SIDECAR_PARTIAL_RATIO", "0.5"))

# 수동 보정용. 자동 감지에 추가로 합쳐짐.
MANUAL_SIDECAR_SELL_DATES = [
    x.strip() for x in os.getenv("SIDECAR_SELL_DATES", "").split(",") if x.strip()
]
MANUAL_SIDECAR_BUY_DATES = [
    x.strip() for x in os.getenv("SIDECAR_BUY_DATES", "").split(",") if x.strip()
]
