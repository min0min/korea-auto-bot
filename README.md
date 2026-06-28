# 국장시봇 Starter

## Railway Variables

아래 환경변수를 Railway에 넣으세요.

```txt
TOSS_CLIENT_ID=토스에서 발급받은 값
TOSS_CLIENT_SECRET=토스에서 발급받은 값
TOSS_ACCOUNT_SEQ=계좌 seq
DRY_RUN=true
```

## 실행 구조

- `backend/dashboard.py` : 웹 대시보드
- `backend/toss_api.py` : 토스 API 토큰/시세/캔들
- `backend/strategy.py` : MA20/MA60/거래량/백테스트 로직

## Railway Start

Procfile:

```txt
web: gunicorn backend.dashboard:app --bind 0.0.0.0:$PORT
```
