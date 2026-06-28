import os

TICKERS = {
    "005930": "삼성전자",
    "000660": "SK하이닉스",
    "000250": "삼천당제약",
    "012330": "현대모비스",
    "000270": "기아",
}

# 백테스트 기간. Railway Variables에서 바꿀 수 있음.
BACKTEST_YEARS = int(os.getenv("BACKTEST_YEARS", "3"))

# 전략 파라미터
MA20_SLOPE_DAYS = int(os.getenv("MA20_SLOPE_DAYS", "5"))
VOLUME_SPIKE_RATIO = float(os.getenv("VOLUME_SPIKE_RATIO", "2.0"))

GENERAL_TAKE_PROFIT = float(os.getenv("GENERAL_TAKE_PROFIT", "0.04"))
SIDECAR_TAKE_PROFIT = float(os.getenv("SIDECAR_TAKE_PROFIT", "0.02"))
STOP_LOSS = float(os.getenv("STOP_LOSS", "-0.02"))
MAX_HOLD_DAYS = int(os.getenv("MAX_HOLD_DAYS", "2"))

# 사이드카 발생일 수동 입력용.
# 예: SIDECAR_SELL_DATES=20200319,20200820
SIDECAR_SELL_DATES = [
    x.strip() for x in os.getenv("SIDECAR_SELL_DATES", "").split(",") if x.strip()
]
SIDECAR_BUY_DATES = [
    x.strip() for x in os.getenv("SIDECAR_BUY_DATES", "").split(",") if x.strip()
]
