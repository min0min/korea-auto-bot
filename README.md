# Korea AI Trader V0.8 Official Sidecar UI

## 핵심 변경

- V0.7의 부정확한 지수 일봉 자동감지 제거
- 확인된 사이드카 이벤트 DB 기반으로 백테스트
- UI 개선
- 토스 API 호출 없음
- 주문 기능 없음

## 전략

```txt
확인된 매도 사이드카 이벤트일
→ MA20 우상향 + 현재가 > MA60 필터
→ 역매수 진입
→ +2% 도달 시 50% 반익절
→ 잔여 50% 본절 스탑
→ 매수 사이드카 이벤트일 발생 시 본절 탈출
→ -2% 손절
→ 최대 2일 보유
```

## 기본 이벤트 DB

현재 파일에는 기사/보도 기준 확인 이벤트를 내장했습니다.

```txt
20251105 SELL
20260608 SELL
20260610 SELL
20260612 BUY
20260615 BUY
20260626 SELL
```

나중에 KRX 공시 수집기를 붙여 자동 업데이트할 예정입니다.

## Railway Variables

기존 토스 변수는 남아 있어도 사용하지 않습니다.

추천:

```txt
UNIVERSE_MODE=large_cap
BACKTEST_YEARS=10
USE_TREND_FILTER=true
SIDECAR_ENTRY_TIMING=close
SIDECAR_HALF_TAKE_PROFIT=0.02
SIDECAR_STOP_LOSS=-0.02
SIDECAR_MAX_HOLD_DAYS=2
SIDECAR_PARTIAL_RATIO=0.5
```

추가 이벤트를 넣고 싶을 때:

```txt
EXTRA_SELL_SIDECAR_DATES=20260102,20260203
EXTRA_BUY_SIDECAR_DATES=20260304
```

## 배포

1. GitHub 기존 파일 삭제
2. zip 압축 풀고 안의 파일들을 루트에 업로드
3. Railway 자동 배포
4. 메인 URL 접속
