# Korea AI Trader V1.0 Hybrid Sidecar Analyzer

## 반영 구조

```txt
① 공식/확인 매도 사이드카 발생
② 코스피 대형주 전체 스캔
③ AI 점수 100점 계산
   - 추세
   - RSI
   - 거래량
   - 거래대금
   - 변동성
   - 단기 낙폭
④ 70점 이상만 후보
⑤ 이벤트당 상위 3종목 진입
⑥ 다음날 시가 진입
⑦ +2%에서 50% 익절
⑧ 잔여는 +5% / MA20 이탈 / 매수 사이드카 / 최대 3일 / -2% 손절로 청산
⑨ 거래 분석기에서 진입 근거와 청산 이유 표시
```

## Railway Variables 추천

```txt
UNIVERSE_MODE=large_cap
BACKTEST_YEARS=10
MIN_AI_SCORE=70
MAX_PICKS_PER_EVENT=3
SIDECAR_ENTRY_TIMING=next_open
FIRST_TAKE_PROFIT=0.02
FIRST_TAKE_RATIO=0.50
FINAL_TAKE_PROFIT=0.05
STOP_LOSS=-0.02
MAX_HOLD_DAYS=3
EXIT_ON_MA20_BREAK=true
EXIT_ON_BUY_SIDECAR=true
USE_TREND_FILTER=false
```

기존 토스 변수는 남아 있어도 무시됩니다.
