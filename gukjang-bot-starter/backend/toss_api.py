import time
import requests
from .config import TOSS_BASE_URL, TOSS_CLIENT_ID, TOSS_CLIENT_SECRET, TOSS_ACCOUNT_SEQ


class TossAPI:
    def __init__(self):
        self.access_token = None
        self.token_expire_at = 0

    def ensure_token(self):
        if self.access_token and time.time() < self.token_expire_at - 60:
            return

        if not TOSS_CLIENT_ID or not TOSS_CLIENT_SECRET:
            raise RuntimeError("TOSS_CLIENT_ID / TOSS_CLIENT_SECRET 환경변수가 없습니다.")

        url = f"{TOSS_BASE_URL}/oauth2/token"
        payload = {
            "grant_type": "client_credentials",
            "client_id": TOSS_CLIENT_ID,
            "client_secret": TOSS_CLIENT_SECRET,
        }

        res = requests.post(url, json=payload, timeout=10)
        if res.status_code >= 400:
            raise RuntimeError(f"토큰 발급 실패: {res.status_code} {res.text}")

        data = res.json()
        self.access_token = data["access_token"]
        self.token_expire_at = time.time() + int(data.get("expires_in", 3600))

    def headers(self):
        self.ensure_token()
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    def get_quote(self, ticker):
        url = f"{TOSS_BASE_URL}/api/v1/market-data/stocks/{ticker}/quote"
        res = requests.get(url, headers=self.headers(), timeout=10)
        res.raise_for_status()
        return res.json()

    def get_candles(self, ticker, count=120):
        url = f"{TOSS_BASE_URL}/api/v1/market-data/stocks/{ticker}/candles"
        params = {"interval": "1d", "count": count}
        res = requests.get(url, headers=self.headers(), params=params, timeout=10)
        res.raise_for_status()
        return res.json()
