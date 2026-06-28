# 국장시봇 Starter - Token Fix

## Railway Variables

```txt
TOSS_CLIENT_ID=토스증권 Client ID
TOSS_CLIENT_SECRET=토스증권 Client Secret
TOSS_BASE_URL=https://openapi.tossinvest.com
DRY_RUN=true
```

`TOSS_ACCOUNT_SEQ`는 주문/계좌 조회 단계에서 필요합니다. 현재 대시보드/시세/백테스트 단계에서는 비워도 됩니다.

## Start

```txt
web: gunicorn backend.dashboard:app --bind 0.0.0.0:$PORT
```
