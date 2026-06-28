import os

# 기본은 코스피 대형주 중심.
# Railway Variables에서 UNIVERSE_MODE=custom 으로 바꾸면 CUSTOM_TICKERS 사용.
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

# 기존 관심 종목. 필요하면 여기 유지.
FOCUS_TICKERS = {
    "005930": "삼성전자",
    "000660": "SK하이닉스",
    "000250": "삼천당제약",
    "012330": "현대모비스",
    "000270": "기아",
}

# 커스텀 예시:
# CUSTOM_TICKERS=005930:삼성전자,000660:SK하이닉스
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

BACKTEST_YEARS = int(os.getenv("BACKTEST_YEARS", "3"))

MA20_SLOPE_DAYS = int(os.getenv("MA20_SLOPE_DAYS", "5"))
VOLUME_SPIKE_RATIO = float(os.getenv("VOLUME_SPIKE_RATIO", "2.0"))

GENERAL_TAKE_PROFIT = float(os.getenv("GENERAL_TAKE_PROFIT", "0.04"))
SIDECAR_TAKE_PROFIT = float(os.getenv("SIDECAR_TAKE_PROFIT", "0.02"))
STOP_LOSS = float(os.getenv("STOP_LOSS", "-0.02"))
MAX_HOLD_DAYS = int(os.getenv("MAX_HOLD_DAYS", "2"))

SIDECAR_SELL_DATES = [
    x.strip() for x in os.getenv("SIDECAR_SELL_DATES", "").split(",") if x.strip()
]
SIDECAR_BUY_DATES = [
    x.strip() for x in os.getenv("SIDECAR_BUY_DATES", "").split(",") if x.strip()
]
