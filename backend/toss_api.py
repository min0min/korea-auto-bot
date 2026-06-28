import time
import requests
from requests.auth import HTTPBasicAuth
from .config import TOSS_BASE_URL, TOSS_CLIENT_ID, TOSS_CLIENT_SECRET


class TossAPI:
    def __init__(self):
        self.access_token = None
        self.token_expire_at = 0
        self.last_token_status = None

    def ensure_token(self):
        if self.access_token and time.time() < self.token_expire_at - 60:
            return

        if not TOSS_CLIENT_ID or not TOSS_CLIENT_SECRET:
            raise RuntimeError("TOSS_CLIENT_ID / TOSS_CLIENT_SECRET 환경변수가 없습니다.")

        url = f"{TOSS_BASE_URL}/oauth2/token"

        res = requests.post(
            url,
            data={"grant_type": "client_credentials"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            auth=HTTPBasicAuth(TOSS_CLIENT_ID, TOSS_CLIENT_SECRET),
            timeout=10,
        )

        self.last_token_status = {"status_code": res.status_code, "text": res.text[:500]}

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

    def _get_first_success(self, paths, params=None):
        errors = []
        headers = self.headers()

        for path in paths:
            url = f"{TOSS_BASE_URL}{path}"
            try:
                res = requests.get(url, headers=headers, params=params or {}, timeout=10)
                if res.status_code < 400:
                    data = res.json()
                    return {
                        "ok": True,
                        "url": url,
                        "status_code": res.status_code,
                        "data": data,
                    }
                errors.append(f"{res.status_code} {path}: {res.text[:300]}")
            except Exception as e:
                errors.append(f"{path}: {e}")

        raise RuntimeError("모든 API 후보 실패: " + " | ".join(errors))

    def get_quote(self, ticker):
        # 토스 문서/버전 차이를 대비해 후보 경로를 순차 테스트
        paths = [
            f"/api/v1/market-data/stocks/{ticker}/quote",
            f"/api/v1/market-data/stocks/{ticker}/price",
            f"/api/v1/market/stocks/{ticker}/quote",
            f"/api/v1/stocks/{ticker}/quote",
        ]
        return self._get_first_success(paths)

    def get_candles(self, ticker, count=300):
        params = {"interval": "1d", "count": count}
        paths = [
            f"/api/v1/market-data/stocks/{ticker}/candles",
            f"/api/v1/market-data/stocks/{ticker}/candles/days",
            f"/api/v1/market/stocks/{ticker}/candles",
            f"/api/v1/stocks/{ticker}/candles",
        ]
        return self._get_first_success(paths, params=params)
