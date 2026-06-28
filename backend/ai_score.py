from .config import USE_TREND_FILTER


def clamp(v, lo=0, hi=100):
    return max(lo, min(hi, v))


def score_candidate(row):
    """
    사이드카 패닉 역매수용 AI 점수.
    핵심 의도:
    - 추세가 완전히 죽은 종목은 제외
    - 패닉 당일 너무 약한 종목보다 회복 가능성이 있는 대형주 선호
    - 유동성/거래대금/변동성/RSI를 함께 반영
    """
    score = 0
    reasons = []

    ma20_up = row["ma20_slope"] > 0
    above_ma60 = row["close"] > row["ma60"]

    # 1) 추세 35점
    if ma20_up:
        score += 17
        reasons.append("MA20 우상향 +17")
    if above_ma60:
        score += 18
        reasons.append("MA60 위 +18")

    # 추세필터가 켜진 경우 둘 중 하나라도 실패하면 실전 후보로는 약하게 제한
    if USE_TREND_FILTER and not (ma20_up and above_ma60):
        reasons.append("추세필터 미통과")

    # 2) 패닉/RSI 20점
    rsi = float(row.get("rsi", 50))
    if 25 <= rsi <= 45:
        score += 20
        reasons.append(f"RSI 반등권 {rsi:.1f} +20")
    elif 20 <= rsi < 25:
        score += 14
        reasons.append(f"RSI 과매도 {rsi:.1f} +14")
    elif 45 < rsi <= 55:
        score += 10
        reasons.append(f"RSI 중립 {rsi:.1f} +10")

    # 3) 거래량/관심도 15점
    vol_ratio = float(row.get("volume_ratio", 1))
    if vol_ratio >= 2.0:
        score += 15
        reasons.append(f"거래량 {vol_ratio:.2f}배 +15")
    elif vol_ratio >= 1.3:
        score += 9
        reasons.append(f"거래량 {vol_ratio:.2f}배 +9")
    elif vol_ratio >= 1.0:
        score += 5
        reasons.append(f"거래량 {vol_ratio:.2f}배 +5")

    # 4) 유동성 15점
    trade_value = float(row.get("trade_value", 0))
    if trade_value >= 300_000_000_000:
        score += 15
        reasons.append("거래대금 3000억+ +15")
    elif trade_value >= 100_000_000_000:
        score += 10
        reasons.append("거래대금 1000억+ +10")
    elif trade_value >= 50_000_000_000:
        score += 6
        reasons.append("거래대금 500억+ +6")

    # 5) 변동성 10점: 너무 작으면 먹을 게 없고 너무 크면 위험
    atr_like = float(row.get("atr_like", 0))
    if 0.015 <= atr_like <= 0.06:
        score += 10
        reasons.append(f"변동성 적정 {atr_like*100:.1f}% +10")
    elif 0.006 <= atr_like < 0.015:
        score += 5
        reasons.append(f"변동성 낮음 {atr_like*100:.1f}% +5")

    # 6) 단기 낙폭 5점
    drop_3d = float(row.get("drop_3d", 0))
    if drop_3d <= -0.05:
        score += 5
        reasons.append(f"3일 낙폭 {drop_3d*100:.1f}% +5")
    elif drop_3d <= -0.025:
        score += 3
        reasons.append(f"3일 낙폭 {drop_3d*100:.1f}% +3")

    return {
        "score": round(clamp(score), 1),
        "reasons": reasons,
        "ma20_up": bool(ma20_up),
        "price_above_ma60": bool(above_ma60),
        "rsi": round(rsi, 1),
        "volume_ratio": round(vol_ratio, 2),
        "trade_value": round(trade_value),
        "atr_like_pct": round(atr_like * 100, 2),
        "drop_3d_pct": round(drop_3d * 100, 2),
        "trend_pass": bool(ma20_up and above_ma60),
    }
