from flask import Flask, jsonify, render_template_string, abort
from .config import TICKERS, BACKTEST_YEARS, UNIVERSE_MODE
from .data_source import get_ohlcv
from .strategy import (
    latest_status,
    backtest_strategy,
    summarize_trades,
    equity_curve,
    monthly_summary,
)

app = Flask(__name__)


def load_one(ticker):
    name = TICKERS.get(ticker, ticker)
    df = get_ohlcv(ticker)
    status = latest_status(df)
    trades = [{**t, "ticker": ticker, "name": name} for t in backtest_strategy(df)]
    summary = summarize_trades(trades)
    return name, df, status, trades, summary


def build_dashboard_data():
    rows = []
    all_trades = []

    for ticker, name in TICKERS.items():
        item = {"ticker": ticker, "name": name, "ok": False}
        try:
            _, df, status, trades, summary = load_one(ticker)
            all_trades.extend(trades)

            item.update({
                "ok": True,
                "status": status,
                "trades": trades,
                "summary": summary,
            })
        except Exception as e:
            item["error"] = str(e)

        rows.append(item)

    all_trades = sorted(all_trades, key=lambda x: x["entry_date"], reverse=True)
    total = summarize_trades(all_trades)
    return rows, all_trades, total


HTML = """
<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>Korea AI Trader V0.5</title>
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
    button, a { background:#4058d8; color:white; border:0; border-radius:10px; padding:10px 14px; font-weight:700; text-decoration:none; display:inline-block; }
    .small { color:#8992ad; font-size:13px; }
    .link { background:transparent; color:#9aa7ff; padding:0; }
  </style>
</head>
<body>
  <div class="top">
    <h1>Korea AI Trader <span class="badge">V0.5 Research</span></h1>
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
    <div class="small">모드: {{ universe_mode }} · 토스 API 호출 없음 · pykrx 기반 최근 {{ years }}년 일봉 백테스트</div>
    <table>
      <tr>
        <th>종목</th><th>현재가</th><th>MA20</th><th>MA60</th><th>거래량</th><th>오늘 신호</th><th>백테스트</th><th>상세</th>
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
          <td><a href="/stock/{{ r.ticker }}">보기</a></td>
        {% else %}
          <td colspan="7" class="bad">{{ r.error }}</td>
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

DETAIL_HTML = """
<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>{{ name }} 상세</title>
  <style>
    body { background:#0f1014; color:#fff; font-family:Arial, sans-serif; margin:0; padding:28px; }
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
    a { background:#4058d8; color:white; border:0; border-radius:10px; padding:10px 14px; font-weight:700; text-decoration:none; display:inline-block; }
    .small { color:#8992ad; font-size:13px; }
  </style>
</head>
<body>
  <h1>{{ name }} {{ ticker }} <span class="badge">상세 리포트</span></h1>
  <p><a href="/">← 대시보드</a></p>

  <div class="grid">
    <div class="card"><div>손익</div><div class="big">{{ summary.total_pnl }}%</div></div>
    <div class="card"><div>승률</div><div class="big">{{ summary.win_rate }}%</div></div>
    <div class="card"><div>거래수</div><div class="big">{{ summary.total }}회</div></div>
    <div class="card"><div>PF</div><div class="big">{{ summary.profit_factor }}</div></div>
    <div class="card"><div>MDD</div><div class="big">{{ summary.mdd }}%</div></div>
  </div>

  <div class="card">
    <h2>월별 성과</h2>
    <table>
      <tr><th>월</th><th>거래수</th><th>승률</th><th>손익</th><th>평균</th><th>MDD</th></tr>
      {% for m in months %}
      <tr>
        <td>{{ m.month }}</td>
        <td>{{ m.total }}</td>
        <td>{{ m.win_rate }}%</td>
        <td class="{{ 'ok' if m.total_pnl > 0 else 'bad' }}">{{ m.total_pnl }}%</td>
        <td>{{ m.avg_pnl }}%</td>
        <td>{{ m.mdd }}%</td>
      </tr>
      {% endfor %}
    </table>
  </div>

  <div class="card">
    <h2>전체 거래 내역</h2>
    <table>
      <tr>
        <th>진입유형</th><th>신호일</th><th>진입일</th><th>청산일</th><th>진입가</th><th>청산가</th><th>수익률</th><th>이유</th>
      </tr>
      {% for t in trades %}
      <tr>
        <td>{{ t.entry_type }}</td>
        <td>{{ t.signal_date }}</td>
        <td>{{ t.entry_date }}</td>
        <td>{{ t.exit_date }}</td>
        <td>{{ "{:,.0f}".format(t.entry_price) }}</td>
        <td>{{ "{:,.0f}".format(t.exit_price) }}</td>
        <td class="{{ 'ok' if t.pnl_pct > 0 else 'bad' }}">{{ t.pnl_pct }}%</td>
        <td>
          {{ t.exit_reason }}<br>
          <span class="small">
            MA20={{ t.reasons.ma20_up }},
            MA60={{ t.reasons.price_above_ma60 }},
            거래량={{ t.reasons.volume_ratio }}배
          </span>
        </td>
      </tr>
      {% endfor %}
    </table>
  </div>
</body>
</html>
"""


@app.route("/")
def index():
    rows, all_trades, total = build_dashboard_data()
    return render_template_string(
        HTML,
        rows=rows,
        recent_trades=all_trades[:20],
        total=total,
        years=BACKTEST_YEARS,
        universe_mode=UNIVERSE_MODE,
    )


@app.route("/stock/<ticker>")
def stock_detail(ticker):
    if ticker not in TICKERS:
        abort(404)

    name, df, status, trades, summary = load_one(ticker)
    trades_sorted = sorted(trades, key=lambda x: x["entry_date"], reverse=True)

    return render_template_string(
        DETAIL_HTML,
        ticker=ticker,
        name=name,
        status=status,
        trades=trades_sorted,
        summary=summary,
        curve=equity_curve(trades),
        months=monthly_summary(trades),
    )


@app.route("/api/backtest")
def api_backtest():
    rows, all_trades, total = build_dashboard_data()
    return jsonify({
        "total": total,
        "rows": rows,
        "recent_trades": all_trades[:50],
    })


@app.route("/api/stock/<ticker>")
def api_stock(ticker):
    if ticker not in TICKERS:
        abort(404)

    name, df, status, trades, summary = load_one(ticker)
    return jsonify({
        "ticker": ticker,
        "name": name,
        "status": status,
        "summary": summary,
        "equity_curve": equity_curve(trades),
        "monthly": monthly_summary(trades),
        "trades": trades,
    })


@app.route("/health")
def health():
    return jsonify({"ok": True, "version": "0.5-research"})
