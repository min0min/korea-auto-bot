# Korea AI Trader V0.5 Research

## 이번 버전

- 코스피 대형주 중심 유니버스 추가
- 종목별 상세 리포트 페이지 `/stock/<ticker>`
- 전체 거래 내역 표시
- 월별 성과 표시
- 진입 이유 표시
- 토스 API 호출 없음

## 기본 대상

기본 `UNIVERSE_MODE=large_cap`

```txt
005930 삼성전자
000660 SK하이닉스
005380 현대차
000270 기아
012330 현대모비스
068270 셀트리온
005490 POSCO홀딩스
035420 NAVER
051910 LG화학
006400 삼성SDI
```

## Railway Variables

토스 변수는 유지해도 되고 삭제해도 됩니다. 이 버전에서는 사용하지 않습니다.

선택 변수:

```txt
UNIVERSE_MODE=large_cap
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

기존 5종목만 보려면:

```txt
UNIVERSE_MODE=focus
```

직접 종목 지정:

```txt
UNIVERSE_MODE=custom
CUSTOM_TICKERS=005930:삼성전자,000660:SK하이닉스
```

## 배포

1. GitHub 기존 파일 삭제
2. zip 압축 풀고 안의 파일들을 루트에 업로드
3. Railway 자동 배포
4. 메인 URL 접속
