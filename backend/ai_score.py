def clamp(v, lo=0, hi=100):
    return max(lo, min(hi, v))


def score_candidate(row, use_trend_filter=False):
    score = 0
    reasons = []

    ma20_up = bool(row["ma20_slope"] > 0)
    above_ma60 = bool(row["close"] > row["ma60"])
    above_ma120 = bool(row["close"] > row["ma120"]) if row["ma120"] == row["ma120"] else False

    if ma20_up:
        score += 12
        reasons.append("MA20 우상향 +12")
    if above_ma60:
        score += 13
        reasons.append("MA60 위 +13")
    if above_ma120:
        score += 5
        reasons.append("MA120 위 +5")
    if use_trend_filter and not (ma20_up and above_ma60):
        score -= 25
        reasons.append("추세필터 미통과 -25")

    rsi = float(row.get("rsi", 50))
    if 25 <= rsi <= 42:
        score += 20
        reasons.append(f"RSI 반등권 {rsi:.1f} +20")
    elif 20 <= rsi < 25:
        score += 14
        reasons.append(f"RSI 과매도 {rsi:.1f} +14")
    elif 42 < rsi <= 55:
        score += 11
        reasons.append(f"RSI 중립 {rsi:.1f} +11")
    elif 55 < rsi <= 65:
        score += 4
        reasons.append(f"RSI 다소 높음 {rsi:.1f} +4")

    vol_ratio = float(row.get("volume_ratio", 1))
    if vol_ratio >= 2.0:
        score += 15
        reasons.append(f"거래량 {vol_ratio:.2f}배 +15")
    elif vol_ratio >= 1.5:
        score += 11
        reasons.append(f"거래량 {vol_ratio:.2f}배 +11")
    elif vol_ratio >= 1.0:
        score += 6
        reasons.append(f"거래량 {vol_ratio:.2f}배 +6")

    trade_value = float(row.get("trade_value", 0))
    if trade_value >= 500_000_000_000:
        score += 15
        reasons.append("거래대금 5000억+ +15")
    elif trade_value >= 300_000_000_000:
        score += 12
        reasons.append("거래대금 3000억+ +12")
    elif trade_value >= 100_000_000_000:
        score += 8
        reasons.append("거래대금 1000억+ +8")
    elif trade_value >= 50_000_000_000:
        score += 5
        reasons.append("거래대금 500억+ +5")

    atr_like = float(row.get("atr_like", 0))
    if 0.015 <= atr_like <= 0.055:
        score += 10
        reasons.append(f"변동성 적정 {atr_like*100:.1f}% +10")
    elif 0.008 <= atr_like < 0.015:
        score += 5
        reasons.append(f"변동성 낮음 {atr_like*100:.1f}% +5")
    elif atr_like > 0.08:
        score -= 8
        reasons.append(f"변동성 과열 {atr_like*100:.1f}% -8")

    drop_3d = float(row.get("drop_3d", 0))
    drop_5d = float(row.get("drop_5d", 0))
    if drop_3d <= -0.045 or drop_5d <= -0.07:
        score += 10
        reasons.append("단기 낙폭 충분 +10")
    elif drop_3d <= -0.025 or drop_5d <= -0.04:
        score += 6
        reasons.append("단기 낙폭 일부 +6")

    return {
        "score": round(clamp(score), 1),
        "reasons": reasons,
        "ma20_up": ma20_up,
        "price_above_ma60": above_ma60,
        "price_above_ma120": above_ma120,
        "rsi": round(rsi, 1),
        "volume_ratio": round(vol_ratio, 2),
        "trade_value": round(trade_value),
        "atr_like_pct": round(atr_like * 100, 2),
        "drop_3d_pct": round(drop_3d * 100, 2),
        "drop_5d_pct": round(drop_5d * 100, 2),
        "trend_pass": bool(ma20_up and above_ma60),
    }
