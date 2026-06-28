# Korea Auto Bot V0.3 Collector

## 이번 버전

- OAuth Token Test 유지
- Railway Public IP Debug 유지
- 5종목 현재가/일봉 API 후보 경로 테스트
- MA20 / MA60 / 거래량 200% 계산
- 일반 매수 전략 백테스트 기초 계산

## Railway Variables

```txt
TOSS_CLIENT_ID=토스증권 Client ID
TOSS_CLIENT_SECRET=토스증권 Client Secret
TOSS_BASE_URL=https://openapi.tossinvest.com
DRY_RUN=true
```

## 확인 순서

1. GitHub 파일 덮어쓰기
2. Railway Redeploy
3. `/debug`에서 OAuth 성공 확인
4. `/` 대시보드에서 API 경로/필드명 오류 확인
5. 오류가 뜨면 화면 캡처
