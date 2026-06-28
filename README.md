# Korea AI Trader V0.9 AI Score Sidecar

## 핵심 구조

이 버전은 네가 요청한 다음 구조를 반영합니다.

```txt
① 공식/확인 사이드카 발생 확인
② 코스피 대형주 스캔
③ AI 점수 100점 계산
   - 추세
   - RSI
   - 거래량
   - 거래대금
   - 변동성
   - 단기 낙폭
④ 80점 이상만 진입
⑤ 이벤트당 상위 1개만 진입
⑥ +2%에서 30% 익절
⑦ 잔여는 MA20 이탈 / 매수 사이드카 / 최대 보유일 / 손절로 청산
```

## Railway Variables

```txt
UNIVERSE_MODE=large_cap
BACKTEST_YEARS=10
MIN_AI_SCORE=80
MAX_PICKS_PER_EVENT=1
PARTIAL_TAKE_PROFIT=0.02
PARTIAL_RATIO=0.30
STOP_LOSS=-0.02
MAX_HOLD_DAYS=5
EXIT_ON_MA20_BREAK=true
EXIT_ON_BUY_SIDECAR=true
SIDECAR_ENTRY_TIMING=close
USE_TREND_FILTER=true
```

## 배포

1. GitHub 기존 파일 삭제
2. zip 압축 풀고 안의 파일들을 루트에 업로드
3. Railway 자동 배포
4. 메인 URL 접속
