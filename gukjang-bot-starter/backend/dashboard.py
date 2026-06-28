from flask import Flask, jsonify, render_template_string
import pandas as pd
from .config import TICKERS
from .toss_api import TossAPI
from .strategy import normalize_candles, latest_status, backtest_general

app = Flask(__name__)
api = TossAPI()

HTML = """
<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>국장시봇</title>
  <style>
    body { background:#0f1014; color:#fff; font-family:Arial, sans-serif; margin:0; padding:28px; }
    h1 { margin:0 0 18px; }
    .badge { background:#163f1f; color:#79ef8c; padding:8px 14px; border-radius:20px; font-size:14px; }
    .grid { display:grid; grid-template-columns:repeat(4,1fr); gap:16px; margin:22px 0; }
    .card { background:#171821; border:1px solid #252735; border-radius:14px; padding:20px; }
    .big { font-size:30px; font-weight:800; color:#79ef8c; margin-top:10px; }
    table { width:100%; border-collapse:collapse; margin-top:12px; }
    th,td { padding:12px; border-bottom:1px solid #2a2d3a; text-align:left; }
    th { color:#8992ad; }
    .ok { color:#79ef8c; font-weight:700; }
    .wait { color:#ffbd4a; font-weight:700; }
    .bad { color:#ff6b6b; font-weight:700; }
    button { background:#4058d8; color:white; border:0; border-radius:10px; padding:12px 18px; font-weight:700; }
    .top { display:flex; align-items:center; justify-content:space-between; border-bottom:1px solid #272934; padding-bottom:18px; }
  </style>
</head>
<body>
  <div class="top">
    <div><h1>국장시봇 <span class="badge">대시보드 실행중</span></h1></div>
    <button onclick="location.reload()">새로고침</button>
  </div>

  <div class="grid">
    <div class="card"><div>총 백테스트 손익</div><div class="big">{{ total_pnl }}%</div></div>
    <div class="card"><div>승률</div><div class="big">{{ win_rate }}%</div></div>
    <div class="card"><div>총 거래 수</div><div class="big">{{ total_trades }}회</div></div>
    <div class="card"><div>오늘 신호</div><div class="big">{{ signal_count }}종목</div></div>
  </div>

  <div class="card">
    <h2>전략 조건 현황</h2>
    <table>
      <tr>
        <th>종목</th><th>현재가</th><th>MA20 우상향</th><th>현재가 > MA60</th><th>거래량 200%</th><th>매수 신호</th><th>백테스트</th>
      </tr>
      {% for r in rows %}
      <tr>
        <td>{{ r.name }} ({{ r.ticker }})</td>
        <td>{{ r.close }}</td>
        <td class="{{ 'ok' if r.ma20_up else 'bad' }}">{{ r.ma20_up }}</td>
        <td class="{{ 'ok' if r.price_above_ma60 else 'bad' }}">{{ r.price_above_ma60 }}</td>
        <td class="{{ 'ok' if r.volume_spike else 'wait' }}">{{ r.volume_ratio }}배</td>
        <td class="{{ 'ok' if r.signal else 'wait' }}">{{ '매수 후보' if r.signal else '대기' }}</td>
        <td>{{ r.trades }}회 / {{ r.pnl }}%</td>
      </tr>
      {% endfor %}
    </table>
  </div>
</body>
</html>
"""


@app.route("/")
def index():
    rows = []
    all_pnls = []
    signal_count = 0

    for ticker, name in TICKERS.items():
        try:
            raw = api.get_candles(ticker, count=180)
            df = normalize_candles(raw)
            status = latest_status(df)
            trades = backtest_general(df)

            pnls = [t["pnl_pct"] for t in trades]
            all_pnls.extend(pnls)
            if status.get("signal"):
                signal_count += 1

            rows.append({
                "ticker": ticker,
                "name": name,
                "close": round(status.get("close", 0), 2),
                "ma20_up": status.get("ma20_up", False),
                "price_above_ma60": status.get("price_above_ma60", False),
                "volume_spike": status.get("volume_spike", False),
                "volume_ratio": round(status.get("volume_ratio", 0), 2),
                "signal": status.get("signal", False),
                "trades": len(trades),
                "pnl": round(sum(pnls), 2),
            })

        except Exception as e:
            rows.append({
                "ticker": ticker,
                "name": name,
                "close": "오류",
                "ma20_up": False,
                "price_above_ma60": False,
                "volume_spike": False,
                "volume_ratio": 0,
                "signal": False,
                "trades": 0,
                "pnl": f"오류: {e}",
            })

    total_trades = len(all_pnls)
    win_rate = round(len([p for p in all_pnls if p > 0]) / total_trades * 100, 1) if total_trades else 0
    total_pnl = round(sum(all_pnls), 2)

    return render_template_string(
        HTML,
        rows=rows,
        total_trades=total_trades,
        win_rate=win_rate,
        total_pnl=total_pnl,
        signal_count=signal_count,
    )


@app.route("/api/status")
def api_status():
    return jsonify({"ok": True})
