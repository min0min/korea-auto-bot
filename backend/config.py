import os

TICKERS = {
    "005930": "삼성전자",
    "000660": "SK하이닉스",
    "000250": "삼천당제약",
    "012330": "현대모비스",
    "000270": "기아",
}

DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"

TOSS_BASE_URL = os.getenv("TOSS_BASE_URL", "https://open-api.tossinvest.com")
TOSS_CLIENT_ID = os.getenv("TOSS_CLIENT_ID")
TOSS_CLIENT_SECRET = os.getenv("TOSS_CLIENT_SECRET")
TOSS_ACCOUNT_SEQ = os.getenv("TOSS_ACCOUNT_SEQ")

DATA_DIR = os.getenv("DATA_DIR", "data")
