from flask import Flask, jsonify, render_template_string, abort
from .config import (
    TICKERS,
    BACKTEST_YEARS,
    UNIVERSE_MODE,
    USE_TREND_FILTER,
    SIDECAR_ENTRY_TIMING,
)
from .data_source import get_ohlcv
from .sidecar_events import get_events, get_sell_dates, get_buy_dates
from .strategy import latest_status, backtest_strategy, summarize_trades, monthly_summary

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
  <title>Korea AI Trader V0.8</title>
  <style>
    :root {
      --bg:#090b12; --panel:#141722; --panel2:#191d2b; --line:#2a3042;
      --txt:#f7f8ff; --muted:#9aa6c7; --green:#7cf29a; --red:#ff6b7a;
      --yellow:#ffc857; --blue:#6377ff; --purple:#9b5cff;
    }
    * { box-sizing:border-box; }
    body { background:radial-gradient(circle at top left,#171c31 0,#090b12 42%); color:var(--txt); font-family:Arial, sans-serif; margin:0; padding:28px; }
    .top { display:flex; align-items:center; justify-content:space-between; border-bottom:1px solid var(--line); padding-bottom:18px; }
    h1 { margin:0; letter-spacing:-1px; }
    .badge { background:linear-gradient(135deg,#5c3414,#2c1b0e); color:var(--yellow); padding:8px 14px; border-radius:999px; font-size:14px; border:1px solid #6d431d; }
    .button { background:linear-gradient(135deg,var(--blue),#4754c9); color:white; border:0; border-radius:12px; padding:12px 18px; font-weight:800; text-decoration:none; display:inline-block; }
    .grid { display:grid; grid-template-columns:repeat(5,1fr); gap:16px; margin:22px 0; }
    .card { background:linear-gradient(180deg,var(--panel2),var(--panel)); border:1px solid var(--line); border-radius:18px; padding:22px; margin-bottom:18px; box-shadow:0 10px 30px rgba(0,0,0,.25); }
    .label { color:var(--muted); font-size:14px; }
    .big { font-size:34px; font-weight:900; color:var(--green); margin-top:10px; letter-spacing:-1px; }
    .loss { color:var(--red); }
    table { width:100%; border-collapse:collapse; margin-top:12px; }
    th,td { padding:14px 12px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }
    th { color:var(--muted); font-size:14px; }
    .ok { color:var(--green); font-weight:800; }
    .wait { color:var(--yellow); font-weight:800; }
    .bad { color:var(--red); font-weight:800; }
    .small { color:var(--muted); font-size:13px; line-height:1.5; }
    .pill { display:inline-block; padding:6px 10px; border-radius:999px; font-weight:800; font-size:12px; }
    .pill-sell { background:rgba(255,107,122,.15); color:var(--red); border:1px solid rgba(255,107,122,.35); }
    .pill-buy { background:rgba(124,242,154,.14); color:var(--green); border:1px solid rgba(124,242,154,.35); }
    .section-title { display:flex; justify-content:space-between; align-items:flex-end; gap:12px; }
    code { color:var(--yellow); }
  </style>
</head>
<body>
  <div class="top">
    <h1>Korea AI Trader <span class="badge">V0.8 Official Sidecar</span></h1>
    <a class="button" href="/">새로고침</a>
  </div>

  <div class="grid">
    <div class="card"><div class="label">총 손익</div><div class="big {{ 'loss' if total.total_pnl < 0 else '' }}">{{ total.total_pnl }}%</div></div>
    <div class="card"><div class="label">승률</div><div class="big">{{ total.win_rate }}%</div></div>
    <div class="card"><div class="label">거래 수</div><div class="big">{{ total.total }}회</div></div>
    <div class="card"><div class="label">공식 이벤트</div><div class="big">{{ events|length }}개</div></div>
    <div class="card"><div class="label">MDD</div><div class="big {{ 'loss' if total.mdd < 0 else '' }}">{{ total.mdd }}%</div></div>
  </div>

  <div class="card">
    <div class="section-title">
      <div>
        <h2>전략 개요</h2>
        <div class="small">
          일봉 근사 감지 제거 · 확인된 사이드카 이벤트 DB 기반 · 매도 사이드카 역매수 전용<br>
          진입: {{ entry_timing }} · 추세필터: {{ use_trend_filter }} · 최근 {{ years }}년 · 유니버스: {{ universe_mode }}
        </div>
      </div>
      <div class="small">
        SELL {{ sell_count }}개 · BUY {{ buy_count }}개
      </div>
    </div>
  </div>

  <div class="card">
    <h2>사이드카 역매수 전략 현황</h2>
    <table>
      <tr>
        <th>종목</th><th>현재가</th><th>MA20</th><th>MA60</th><th>오늘 상태</th><th>백테스트</th><th>상세</th>
      </tr>
      {% for r in rows %}
      <tr>
        <td><b>{{ r.name }}</b><br><span class="small">{{ r.ticker }}</span></td>
        {% if r.ok %}
          <td>{{ "{:,.0f}".format(r.status.close) }}<br><span class="small">{{ r.status.date }}</span></td>
          <td>{{ "{:,.0f}".format(r.status.ma20) }}<br><span class="{{ 'ok' if r.status.ma20_up else 'bad' }}">{{ '우상향' if r.status.ma20_up else '아님' }}</span></td>
          <td>{{ "{:,.0f}".format(r.status.ma60) }}<br><span class="{{ 'ok' if r.status.price_above_ma60 else 'bad' }}">{{ 'MA60 위' if r.status.price_above_ma60 else 'MA60 아래' }}</span></td>
          <td>
            {% if r.status.sidecar_signal %}
              <span class="ok">역매수 후보</span>
            {% else %}
              <span class="wait">대기</span>
            {% endif %}
          </td>
          <td>
            <b>{{ r.summary.total }}회 / 승률 {{ r.summary.win_rate }}% / 손익 <span class="{{ 'ok' if r.summary.total_pnl > 0 else 'bad' }}">{{ r.summary.total_pnl }}%</span></b><br>
            <span class="small">평균 {{ r.summary.avg_pnl }}% · PF {{ r.summary.profit_factor }} · MDD {{ r.summary.mdd }}%</span>
          </td>
          <td><a class="button" href="/stock/{{ r.ticker }}">보기</a></td>
        {% else %}
          <td colspan="6" class="bad">{{ r.error }}</td>
        {% endif %}
      </tr>
      {% endfor %}
    </table>
  </div>

  <div class="card">
    <h2>내장 사이드카 이벤트 DB</h2>
    <table>
      <tr><th>날짜</th><th>시장</th><th>구분</th><th>시각</th><th>비고</th></tr>
      {% for e in events %}
      <tr>
        <td>{{ e.date }}</td>
        <td>{{ e.market }}</td>
        <td><span class="pill {{ 'pill-sell' if e.side == 'SELL' else 'pill-buy' }}">{{ e.side }}</span></td>
        <td>{{ e.time }}</td>
        <td class="small">{{ e.note }} · {{ e.source }}</td>
      </tr>
      {% endfor %}
    </table>
  </div>

  <div class="card">
    <h2>최근 사이드카 거래</h2>
    <table>
      <tr><th>종목</th><th>신호일</th><th>진입일</th><th>청산일</th><th>반익절</th><th>수익률</th><th>청산이유</th></tr>
      {% for t in recent_trades %}
      <tr>
        <td>{{ t.name }} {{ t.ticker }}</td>
        <td>{{ t.signal_date }}</td>
        <td>{{ t.entry_date }}</td>
        <td>{{ t.exit_date }}</td>
        <td>{{ 'O' if t.partial_done else 'X' }}</td>
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
  <title>{{ name }} 사이드카 상세</title>
  <style>
    :root { --bg:#090b12; --panel:#141722; --panel2:#191d2b; --line:#2a3042; --txt:#f7f8ff; --muted:#9aa6c7; --green:#7cf29a; --red:#ff6b7a; --yellow:#ffc857; --blue:#6377ff; }
    body { background:radial-gradient(circle at top left,#171c31 0,#090b12 42%); color:var(--txt); font-family:Arial, sans-serif; margin:0; padding:28px; }
    .badge { background:#4a2b0f; color:var(--yellow); padding:8px 14px; border-radius:20px; font-size:14px; }
    .grid { display:grid; grid-template-columns:repeat(5,1fr); gap:16px; margin:22px 0; }
    .card { background:linear-gradient(180deg,var(--panel2),var(--panel)); border:1px solid var(--line); border-radius:18px; padding:22px; margin-bottom:18px; }
    .big { font-size:30px; font-weight:900; color:var(--green); margin-top:10px; }
    table { width:100%; border-collapse:collapse; margin-top:12px; }
    th,td { padding:14px 12px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }
    th { color:var(--muted); }
    .ok { color:var(--green); font-weight:800; }
    .bad { color:var(--red); font-weight:800; }
    .button { background:linear-gradient(135deg,var(--blue),#4754c9); color:white; border:0; border-radius:12px; padding:10px 14px; font-weight:800; text-decoration:none; display:inline-block; }
  </style>
</head>
<body>
  <h1>{{ name }} {{ ticker }} <span class="badge">Official Sidecar Report</span></h1>
  <p><a class="button" href="/">← 대시보드</a></p>

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
    <h2>사이드카 거래 내역</h2>
    <table>
      <tr><th>신호일</th><th>진입일</th><th>청산일</th><th>진입가</th><th>반익절가</th><th>최종가</th><th>수익률</th><th>청산이유</th></tr>
      {% for t in trades %}
      <tr>
        <td>{{ t.signal_date }}</td>
        <td>{{ t.entry_date }}</td>
        <td>{{ t.exit_date }}</td>
        <td>{{ "{:,.0f}".format(t.entry_price) }}</td>
        <td>{{ "{:,.0f}".format(t.partial_price) if t.partial_price else '-' }}</td>
        <td>{{ "{:,.0f}".format(t.final_price) }}</td>
        <td class="{{ 'ok' if t.pnl_pct > 0 else 'bad' }}">{{ t.pnl_pct }}%</td>
        <td>{{ t.exit_reason }}</td>
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
    events = get_events()

    return render_template_string(
        HTML,
        rows=rows,
        recent_trades=all_trades[:30],
        total=total,
        years=BACKTEST_YEARS,
        universe_mode=UNIVERSE_MODE,
        sell_count=len(get_sell_dates()),
        buy_count=len(get_buy_dates()),
        use_trend_filter=USE_TREND_FILTER,
        entry_timing=SIDECAR_ENTRY_TIMING,
        events=events,
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
        trades=trades_sorted,
        summary=summary,
        months=monthly_summary(trades),
    )


@app.route("/api/backtest")
def api_backtest():
    rows, all_trades, total = build_dashboard_data()
    return jsonify({"total": total, "rows": rows, "recent_trades": all_trades[:50], "events": get_events()})


@app.route("/health")
def health():
    return jsonify({"ok": True, "version": "0.8-official-sidecar-ui"})
