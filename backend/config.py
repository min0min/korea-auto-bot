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

# 공식/뉴스 기반 이벤트 DB 모드
SIDECAR_EVENT_MODE = os.getenv("SIDECAR_EVENT_MODE", "official_db").lower()

# sidecar 전략 설정
MA20_SLOPE_DAYS = int(os.getenv("MA20_SLOPE_DAYS", "5"))

# 원래 전략 필터. true면 MA20 우상향 + 현재가 > MA60만 매수.
USE_TREND_FILTER = os.getenv("USE_TREND_FILTER", "true").lower() == "true"

# 패닉일 진입 가격 근사
# close: 사이드카 당일 종가 진입
# next_open: 다음 거래일 시가 진입
SIDECAR_ENTRY_TIMING = os.getenv("SIDECAR_ENTRY_TIMING", "close").lower()

# 매도/청산
SIDECAR_HALF_TAKE_PROFIT = float(os.getenv("SIDECAR_HALF_TAKE_PROFIT", "0.02"))
SIDECAR_STOP_LOSS = float(os.getenv("SIDECAR_STOP_LOSS", "-0.02"))
SIDECAR_MAX_HOLD_DAYS = int(os.getenv("SIDECAR_MAX_HOLD_DAYS", "2"))
SIDECAR_PARTIAL_RATIO = float(os.getenv("SIDECAR_PARTIAL_RATIO", "0.5"))

# 선택: 기본 이벤트 DB에 추가할 수 있는 보정값
EXTRA_SELL_SIDECAR_DATES = [
    x.strip() for x in os.getenv("EXTRA_SELL_SIDECAR_DATES", "").split(",") if x.strip()
]
EXTRA_BUY_SIDECAR_DATES = [
    x.strip() for x in os.getenv("EXTRA_BUY_SIDECAR_DATES", "").split(",") if x.strip()
]
