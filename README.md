# Korea Auto Bot V0.2 Debug Center

## Railway Variables

```txt
TOSS_CLIENT_ID=토스증권 Client ID
TOSS_CLIENT_SECRET=토스증권 Client Secret
TOSS_BASE_URL=https://openapi.tossinvest.com
DRY_RUN=true
```

## 확인 순서

1. Railway에 배포
2. `/debug` 접속
3. `Railway Public IP` 확인
4. 토스 개발자센터 → 허용 IP 관리 → 해당 IP 추가
5. 다시 `/debug` 새로고침
6. OAuth Token Test가 성공인지 확인
