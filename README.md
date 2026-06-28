# Korea AI Trader V0.4 Backtest Core

## 핵심 변경

- 토스 API 호출 제거
- Railway IP 변경 문제 회피
- pykrx 기반 한국 주식 일봉 수집
- 기존 전략 반영:
  - MA20 최근 5일 기울기 양수
  - 현재가 > MA60
  - 거래량 전일 대비 200% 이상
  - 일반 진입 +4% 익절
  - 사이드카 진입 +2% 익절
  - 공통 -2% 손절
  - 최대 1~2일 보유
  - 매수 사이드카 발생일은 본절 탈출 처리
- 사이드카 날짜는 환경변수로 수동 입력 가능

## Railway Variables

기존 토스 변수는 삭제하지 않아도 됩니다. 이 버전에서는 사용하지 않습니다.

필수 변수 없음.

선택 변수:

```txt
DRY_RUN=true
BACKTEST_YEARS=3
MA20_SLOPE_DAYS=5
VOLUME_SPIKE_RATIO=2.0
GENERAL_TAKE_PROFIT=0.04
SIDECAR_TAKE_PROFIT=0.02
STOP_LOSS=-0.02
MAX_HOLD_DAYS=2
SIDECAR_SELL_DATES=
SIDECAR_BUY_DATES=
```

사이드카 날짜 예시:

```txt
SIDECAR_SELL_DATES=20200319,20200820
SIDECAR_BUY_DATES=20200324
```

## 배포

1. GitHub 기존 파일 삭제
2. 이 zip 압축 풀고 안의 파일들을 루트에 업로드
3. Railway 자동 배포
4. 메인 URL 접속
