from flask import Flask, jsonify, render_template_string
from .config import TICKERS, BACKTEST_YEARS
from .data_source import get_ohlcv
from .strategy import latest_status, backtest_strategy, summarize_trades

app = Flask(__name__)

HTML = """
<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>Korea AI Trader V0.4</title>
  <style>
    body { background:#0f1014; color:#fff; font-family:Arial, sans-serif; margin:0; padding:28px; }
    .top { display:flex; align-items:center; justify-content:space-between; border-bottom:1px solid #272934; padding-bottom:18px; }
    .badge { background:#163f1f; color:#79ef8c; padding:8px 14px; border-radius:20px; font-size:14px; }
    .grid { display:grid; grid-template-columns:repeat(5,1fr); gap:16px; margin:22px 0; }
    .card { background:#171821; border:1px solid #252735; border-radius:14px; padding:20px; margin-bottom:16px; }
    .big { font-size:28px; font-weight:800; color:#79ef8c; margin-top:10px; }
    table { width:100%; border-collapse:collapse; margin-top:12px; }
    th,td { padding:12px; border-bottom:1px solid #2a2d3a; text-align:left; vertical-align:top; }
    th { color:#8992ad; }
    .ok { color:#79ef8c; font-weight:700; }
    .wait { color:#ffbd4a; font-weight:700; }
    .bad { color:#ff6b6b; font-weight:700; }
    button, a { background:#4058d8; color:white; border:0; border-radius:10px; padding:12px 18px; font-weight:700; text-decoration:none; }
    .small { color:#8992ad; font-size:13px; }
  </style>
</head>
<body>
  <div class="top">
    <h1>Korea AI Trader <span class="badge">V0.4 Backtest Core</span></h1>
    <button onclick="location.reload()">새로고침</button>
  </div>

  <div class="grid">
    <div class="card"><div>총 백테스트 손익</div><div class="big">{{ total.total_pnl }}%</div></div>
    <div class="card"><div>승률</div><div class="big">{{ total.win_rate }}%</div></div>
    <div class="card"><div>총 거래 수</div><div class="big">{{ total.total }}회</div></div>
    <div class="card"><div>Profit Factor</div><div class="big">{{ total.profit_factor }}</div></div>
    <div class="card"><div>MDD</div><div class="big">{{ total.mdd }}%</div></div>
  </div>

  <div class="card">
    <h2>전략 조건 현황</h2>
    <div class="small">토스 API 호출 없음 · pykrx 기반 최근 {{ years }}년 일봉 백테스트</div>
    <table>
      <tr>
        <th>종목</th><th>현재가</th><th>MA20</th><th>MA60</th><th>거래량</th><th>오늘 신호</th><th>백테스트</th>
      </tr>
      {% for r in rows %}
      <tr>
        <td><b>{{ r.name }}</b><br>{{ r.ticker }}</td>
        {% if r.ok %}
          <td>{{ "{:,.0f}".format(r.status.close) }}<br><span class="small">{{ r.status.date }}</span></td>
          <td>{{ "{:,.0f}".format(r.status.ma20) }}<br><span class="{{ 'ok' if r.status.ma20_up else 'bad' }}">{{ '우상향' if r.status.ma20_up else '아님' }}</span></td>
          <td>{{ "{:,.0f}".format(r.status.ma60) }}<br><span class="{{ 'ok' if r.status.price_above_ma60 else 'bad' }}">{{ 'MA60 위' if r.status.price_above_ma60 else 'MA60 아래' }}</span></td>
          <td><span class="{{ 'ok' if r.status.volume_spike else 'wait' }}">{{ "%.2f"|format(r.status.volume_ratio) }}배</span></td>
          <td>
            {% if r.status.sidecar_buy %}
              <span class="ok">사이드카 역매수</span>
            {% elif r.status.general_buy %}
              <span class="ok">일반 매수</span>
            {% else %}
              <span class="wait">대기</span>
            {% endif %}
          </td>
          <td>
            {{ r.summary.total }}회 / 승률 {{ r.summary.win_rate }}% / 손익 {{ r.summary.total_pnl }}%<br>
            <span class="small">평균 {{ r.summary.avg_pnl }}% · PF {{ r.summary.profit_factor }} · MDD {{ r.summary.mdd }}%</span>
          </td>
        {% else %}
          <td colspan="6" class="bad">{{ r.error }}</td>
        {% endif %}
      </tr>
      {% endfor %}
    </table>
  </div>

  <div class="card">
    <h2>최근 백테스트 거래</h2>
    <table>
      <tr><th>종목</th><th>진입유형</th><th>신호일</th><th>진입일</th><th>청산일</th><th>수익률</th><th>청산이유</th></tr>
      {% for t in recent_trades %}
      <tr>
        <td>{{ t.name }} {{ t.ticker }}</td>
        <td>{{ t.entry_type }}</td>
        <td>{{ t.signal_date }}</td>
        <td>{{ t.entry_date }}</td>
        <td>{{ t.exit_date }}</td>
        <td class="{{ 'ok' if t.pnl_pct > 0 else 'bad' }}">{{ t.pnl_pct }}%</td>
        <td>{{ t.exit_reason }}</td>
      </tr>
      {% endfor %}
    </table>
  </div>
</body>
</html>
"""


def build_dashboard_data():
    rows = []
    all_trades = []

    for ticker, name in TICKERS.items():
        item = {"ticker": ticker, "name": name, "ok": False}
        try:
            df = get_ohlcv(ticker)
            status = latest_status(df)
            trades = backtest_strategy(df)

            named_trades = [{**t, "ticker": ticker, "name": name} for t in trades]
            all_trades.extend(named_trades)

            item.update({
                "ok": True,
                "status": status,
                "trades": named_trades,
                "summary": summarize_trades(named_trades),
            })
        except Exception as e:
            item["error"] = str(e)

        rows.append(item)

    all_trades = sorted(all_trades, key=lambda x: x["entry_date"], reverse=True)
    total = summarize_trades(all_trades)

    return rows, all_trades, total


@app.route("/")
def index():
    rows, all_trades, total = build_dashboard_data()
    return render_template_string(
        HTML,
        rows=rows,
        recent_trades=all_trades[:20],
        total=total,
        years=BACKTEST_YEARS,
    )


@app.route("/api/backtest")
def api_backtest():
    rows, all_trades, total = build_dashboard_data()
    return jsonify({
        "total": total,
        "rows": rows,
        "recent_trades": all_trades[:50],
    })


@app.route("/health")
def health():
    return jsonify({"ok": True, "version": "0.4-backtest-core"})
