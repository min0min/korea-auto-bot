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

# 전략 핵심
USE_TREND_FILTER = os.getenv("USE_TREND_FILTER", "true").lower() == "true"
MIN_AI_SCORE = float(os.getenv("MIN_AI_SCORE", "80"))
MAX_PICKS_PER_EVENT = int(os.getenv("MAX_PICKS_PER_EVENT", "1"))

MA20_SLOPE_DAYS = int(os.getenv("MA20_SLOPE_DAYS", "5"))
RSI_PERIOD = int(os.getenv("RSI_PERIOD", "14"))

# 진입
SIDECAR_ENTRY_TIMING = os.getenv("SIDECAR_ENTRY_TIMING", "close").lower()  # close / next_open

# 청산: +2% 30% 익절, 잔여는 추세 종료까지
PARTIAL_TAKE_PROFIT = float(os.getenv("PARTIAL_TAKE_PROFIT", "0.02"))
PARTIAL_RATIO = float(os.getenv("PARTIAL_RATIO", "0.30"))
STOP_LOSS = float(os.getenv("STOP_LOSS", "-0.02"))
MAX_HOLD_DAYS = int(os.getenv("MAX_HOLD_DAYS", "5"))

# 잔여 청산 조건
EXIT_ON_MA20_BREAK = os.getenv("EXIT_ON_MA20_BREAK", "true").lower() == "true"
EXIT_ON_BUY_SIDECAR = os.getenv("EXIT_ON_BUY_SIDECAR", "true").lower() == "true"

# 기본 이벤트 DB에 수동 보정 가능
EXTRA_SELL_SIDECAR_DATES = [
    x.strip() for x in os.getenv("EXTRA_SELL_SIDECAR_DATES", "").split(",") if x.strip()
]
EXTRA_BUY_SIDECAR_DATES = [
    x.strip() for x in os.getenv("EXTRA_BUY_SIDECAR_DATES", "").split(",") if x.strip()
]
