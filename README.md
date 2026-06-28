# Korea AI Trader V0.7 Auto Sidecar

## 핵심 변경

수동 사이드카 날짜 입력 방식 제거.
이제 기본값으로 자동 감지합니다.

## 자동 감지 방식

공식 사이드카는 KOSPI200 선물 ±5%가 1분 지속될 때 발동합니다.
현재 버전은 무료 데이터 기반 백테스트용으로 아래처럼 근사 감지합니다.

```txt
KOSPI200 지수 일봉 기준
당일 저가 / 전일 종가 - 1 <= -5%  → 매도 사이드카 후보일
당일 고가 / 전일 종가 - 1 >= +5%  → 매수 사이드카 후보일
```

## 전략

```txt
자동 감지된 매도 사이드카 후보일
→ MA20 우상향 + 현재가 > MA60
→ 역매수 진입
→ +2% 도달 시 50% 반익절
→ 남은 50% 본절 스탑
→ 매수 사이드카 후보일 발생 시 본절 탈출
→ -2% 손절
→ 최대 2일 보유
```

## Railway Variables

기존 토스 변수는 필요 없습니다. 남아 있어도 사용하지 않습니다.

추천:

```txt
UNIVERSE_MODE=large_cap
BACKTEST_YEARS=10
AUTO_SIDECAR=true
SIDECAR_DETECTOR=kospi200_daily_proxy
SIDECAR_SELL_THRESHOLD=-0.05
SIDECAR_BUY_THRESHOLD=0.05
USE_TREND_FILTER=true
SIDECAR_ENTRY_TIMING=close
SIDECAR_HALF_TAKE_PROFIT=0.02
SIDECAR_STOP_LOSS=-0.02
SIDECAR_MAX_HOLD_DAYS=2
SIDECAR_PARTIAL_RATIO=0.5
```

## 배포

1. GitHub 기존 파일 삭제
2. zip 압축 풀고 안의 파일들을 루트에 업로드
3. Railway 자동 배포
4. 메인 URL 접속
