from .config import USE_TREND_FILTER

def clamp(v, lo=0, hi=100): return max(lo, min(hi, v))

def score_candidate(row):
    score, reasons = 0, []
    ma20_up = bool(row["ma20_slope"] > 0)
    above_ma60 = bool(row["close"] > row["ma60"])
    above_ma120 = bool(row["close"] > row["ma120"]) if row["ma120"] == row["ma120"] else False
    if ma20_up: score += 12; reasons.append("MA20 우상향 +12")
    if above_ma60: score += 13; reasons.append("MA60 위 +13")
    if above_ma120: score += 5; reasons.append("MA120 위 +5")
    if USE_TREND_FILTER and not (ma20_up and above_ma60): score -= 25; reasons.append("추세필터 미통과 -25")
    r = float(row.get("rsi", 50))
    if 25 <= r <= 42: score += 20; reasons.append(f"RSI 반등권 {r:.1f} +20")
    elif 20 <= r < 25: score += 14; reasons.append(f"RSI 과매도 {r:.1f} +14")
    elif 42 < r <= 55: score += 11; reasons.append(f"RSI 중립 {r:.1f} +11")
    elif 55 < r <= 65: score += 4; reasons.append(f"RSI 다소 높음 {r:.1f} +4")
    vr = float(row.get("volume_ratio", 1))
    if vr >= 2.0: score += 15; reasons.append(f"거래량 {vr:.2f}배 +15")
    elif vr >= 1.5: score += 11; reasons.append(f"거래량 {vr:.2f}배 +11")
    elif vr >= 1.0: score += 6; reasons.append(f"거래량 {vr:.2f}배 +6")
    tv = float(row.get("trade_value", 0))
    if tv >= 500_000_000_000: score += 15; reasons.append("거래대금 5000억+ +15")
    elif tv >= 300_000_000_000: score += 12; reasons.append("거래대금 3000억+ +12")
    elif tv >= 100_000_000_000: score += 8; reasons.append("거래대금 1000억+ +8")
    elif tv >= 50_000_000_000: score += 5; reasons.append("거래대금 500억+ +5")
    atr = float(row.get("atr_like", 0))
    if 0.015 <= atr <= 0.055: score += 10; reasons.append(f"변동성 적정 {atr*100:.1f}% +10")
    elif 0.008 <= atr < 0.015: score += 5; reasons.append(f"변동성 낮음 {atr*100:.1f}% +5")
    elif atr > 0.08: score -= 8; reasons.append(f"변동성 과열 {atr*100:.1f}% -8")
    d3 = float(row.get("drop_3d", 0)); d5 = float(row.get("drop_5d", 0))
    if d3 <= -0.045 or d5 <= -0.07: score += 10; reasons.append("단기 낙폭 충분 +10")
    elif d3 <= -0.025 or d5 <= -0.04: score += 6; reasons.append("단기 낙폭 일부 +6")
    return {"score": round(clamp(score),1), "reasons": reasons, "ma20_up": ma20_up, "price_above_ma60": above_ma60, "rsi": round(r,1), "volume_ratio": round(vr,2), "trade_value": round(tv), "atr_like_pct": round(atr*100,2), "drop_3d_pct": round(d3*100,2), "drop_5d_pct": round(d5*100,2), "trend_pass": bool(ma20_up and above_ma60)}
