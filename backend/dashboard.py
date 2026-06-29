from flask import Flask, jsonify, render_template_string, request
from .config import TICKERS, BACKTEST_YEARS, UNIVERSE_MODE, MA20_SLOPE_DAYS, RSI_PERIOD
from .data_source import get_ohlcv
from .indicators import add_indicators
from .backtest_engine import Params, run_backtest
from .sidecar_events import get_events

app = Flask(__name__)


def f_arg(name, default, cast=float):
    try:
        return cast(request.args.get(name, default))
    except Exception:
        return default


def b_arg(name, default=False):
    val = request.args.get(name)
    if val is None:
        return default
    return str(val).lower() in ["1", "true", "on", "yes"]


def current_params():
    return Params(
        min_ai_score=f_arg("min_ai_score", 60, float),
        max_picks=f_arg("max_picks", 3, int),
        entry_timing=request.args.get("entry_timing", "next_open"),
        first_tp=f_arg("first_tp", 0.02, float),
        first_ratio=f_arg("first_ratio", 0.50, float),
        final_tp=f_arg("final_tp", 0.04, float),
        stop_loss=f_arg("stop_loss", -0.02, float),
        max_hold_days=f_arg("max_hold_days", 3, int),
        exit_on_ma20=b_arg("exit_on_ma20", True),
        exit_on_buy_sidecar=b_arg("exit_on_buy_sidecar", True),
        use_trend_filter=b_arg("use_trend_filter", False),
    )


def load_stock_data():
    data = {}
    for ticker, name in TICKERS.items():
        df = get_ohlcv(ticker)
        df = add_indicators(df, MA20_SLOPE_DAYS, RSI_PERIOD)
        data[ticker] = {"name": name, "df": df}
    return data


def build_data(params):
    stock_data = load_stock_data()
    trades, event_reports, summary, curve, months = run_backtest(stock_data, params)

    latest_rows = []
    for ticker, item in stock_data.items():
        row = item["df"].iloc[-1]
        latest_rows.append({
            "ticker": ticker,
            "name": item["name"],
            "date": str(row["date"]),
            "close": float(row["close"]),
            "ma20": float(row["ma20"]),
            "ma60": float(row["ma60"]),
            "rsi": round(float(row["rsi"]), 1) if row["rsi"] == row["rsi"] else 0,
            "volume_ratio": round(float(row["volume_ratio"]), 2) if row["volume_ratio"] == row["volume_ratio"] else 0,
            "trend": bool(row["ma20_slope"] > 0 and row["close"] > row["ma60"]),
        })

    return trades, event_reports, summary, curve, months, latest_rows


HTML = """
<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>Korea AI Trader V1.1</title>
<style>
:root{--bg:#070a12;--panel:#141824;--panel2:#1b2030;--line:#2b3348;--txt:#f7f8ff;--muted:#9aa6c7;--green:#79f59b;--red:#ff6b7a;--yellow:#ffc857;--blue:#6577ff;--cyan:#67e8f9}
*{box-sizing:border-box}body{background:radial-gradient(circle at 10% 0%,#1e2a52 0,#070a12 42%);color:var(--txt);font-family:Arial,sans-serif;margin:0;padding:28px}
.top{display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid var(--line);padding-bottom:18px}h1{margin:0;letter-spacing:-1px}
.badge{background:linear-gradient(135deg,#223c7a,#12192e);color:#c9d3ff;padding:8px 14px;border-radius:999px;font-size:14px;border:1px solid #3d56a8}
.grid{display:grid;grid-template-columns:repeat(5,1fr);gap:16px;margin:22px 0}.card{background:linear-gradient(180deg,var(--panel2),var(--panel));border:1px solid var(--line);border-radius:20px;padding:22px;margin-bottom:18px;box-shadow:0 12px 30px rgba(0,0,0,.25)}
.label{color:var(--muted);font-size:14px}.big{font-size:34px;font-weight:900;color:var(--green);margin-top:10px}.loss{color:var(--red)}
table{width:100%;border-collapse:collapse;margin-top:12px}th,td{padding:14px 12px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}th{color:var(--muted);font-size:14px}
.ok{color:var(--green);font-weight:800}.bad{color:var(--red);font-weight:800}.wait{color:var(--yellow);font-weight:800}.small{color:var(--muted);font-size:13px;line-height:1.5}
.btn{background:linear-gradient(135deg,var(--blue),#4956cf);color:white;border:0;border-radius:12px;padding:11px 16px;font-weight:800;text-decoration:none;display:inline-block;cursor:pointer}
input,select{background:#0d1220;border:1px solid var(--line);border-radius:10px;color:white;padding:10px;width:100%}.formgrid{display:grid;grid-template-columns:repeat(6,1fr);gap:12px}.score{font-size:22px;font-weight:900;color:var(--cyan)}
svg{width:100%;height:220px;background:#0d1220;border-radius:14px;border:1px solid var(--line)}
</style>
</head>
<body>
<div class="top">
  <h1>Korea AI Trader <span class="badge">V1.1 Backtest Lab</span></h1>
  <a class="btn" href="/">초기화</a>
</div>

<div class="grid">
  <div class="card"><div class="label">총 손익</div><div class="big {{ 'loss' if summary.total_pnl < 0 else '' }}">{{ summary.total_pnl }}%</div></div>
  <div class="card"><div class="label">승률</div><div class="big">{{ summary.win_rate }}%</div></div>
  <div class="card"><div class="label">거래 수</div><div class="big">{{ summary.total }}회</div></div>
  <div class="card"><div class="label">PF</div><div class="big">{{ summary.profit_factor }}</div></div>
  <div class="card"><div class="label">MDD</div><div class="big {{ 'loss' if summary.mdd < 0 else '' }}">{{ summary.mdd }}%</div></div>
</div>

<div class="card">
  <h2>백테스트 설정</h2>
  <form method="get">
    <div class="formgrid">
      <label>최소 AI 점수<input name="min_ai_score" value="{{ p.min_ai_score }}"></label>
      <label>이벤트당 종목수<input name="max_picks" value="{{ p.max_picks }}"></label>
      <label>진입방식<select name="entry_timing"><option value="next_open" {{ 'selected' if p.entry_timing=='next_open' else '' }}>다음날 시가</option><option value="close" {{ 'selected' if p.entry_timing=='close' else '' }}>당일 종가</option></select></label>
      <label>1차 익절<input name="first_tp" value="{{ p.first_tp }}"></label>
      <label>1차 비중<input name="first_ratio" value="{{ p.first_ratio }}"></label>
      <label>최종 익절<input name="final_tp" value="{{ p.final_tp }}"></label>
      <label>손절<input name="stop_loss" value="{{ p.stop_loss }}"></label>
      <label>최대보유<input name="max_hold_days" value="{{ p.max_hold_days }}"></label>
      <label>MA20 이탈청산<select name="exit_on_ma20"><option value="true" {{ 'selected' if p.exit_on_ma20 else '' }}>ON</option><option value="false" {{ 'selected' if not p.exit_on_ma20 else '' }}>OFF</option></select></label>
      <label>매수사이드카 탈출<select name="exit_on_buy_sidecar"><option value="true" {{ 'selected' if p.exit_on_buy_sidecar else '' }}>ON</option><option value="false" {{ 'selected' if not p.exit_on_buy_sidecar else '' }}>OFF</option></select></label>
      <label>추세필터<select name="use_trend_filter"><option value="false" {{ 'selected' if not p.use_trend_filter else '' }}>OFF</option><option value="true" {{ 'selected' if p.use_trend_filter else '' }}>ON</option></select></label>
      <label>&nbsp;<button class="btn" type="submit">백테스트 실행</button></label>
    </div>
  </form>
</div>

<div class="card">
  <h2>누적 손익 곡선</h2>
  {% if curve %}
  <svg viewBox="0 0 1000 220" preserveAspectRatio="none">
    <polyline fill="none" stroke="#67e8f9" stroke-width="3"
      points="{% for pt in chart_points %}{{ pt }} {% endfor %}" />
  </svg>
  {% else %}
  <div class="wait">거래가 없어 손익곡선이 없습니다.</div>
  {% endif %}
</div>

<div class="card">
  <h2>이벤트별 AI 후보 랭킹</h2>
  <table>
    <tr><th>이벤트</th><th>선택 종목</th><th>상위 후보 TOP5</th></tr>
    {% for er in event_reports %}
    <tr>
      <td><b>{{ er.event.date }}</b><br><span class="small">{{ er.event.side }} · {{ er.event.note }}</span></td>
      <td>
        {% if er.selected %}
          {% for s in er.selected %}<div><span class="score">{{ s.score }}</span> {{ s.name }} {{ s.ticker }}</div>{% endfor %}
        {% else %}<span class="wait">진입 없음</span>{% endif %}
      </td>
      <td>
        {% for c in er.top_candidates[:5] %}
          <div><span class="score">{{ c.score }}</span> {{ c.name }} <span class="small">RSI {{ c.score_detail.rsi }} · 거래량 {{ c.score_detail.volume_ratio }}배 · 낙폭 {{ c.score_detail.drop_3d_pct }}%</span></div>
        {% endfor %}
      </td>
    </tr>
    {% endfor %}
  </table>
</div>

<div class="card">
  <h2>거래 분석기</h2>
  <table>
    <tr><th>종목</th><th>AI</th><th>신호일</th><th>진입/청산</th><th>1차익절</th><th>수익률</th><th>청산이유</th><th>근거</th></tr>
    {% for t in trades %}
    <tr>
      <td><b>{{ t.name }}</b><br><span class="small">{{ t.ticker }}</span></td>
      <td><span class="score">{{ t.ai_score }}</span></td>
      <td>{{ t.signal_date }}</td>
      <td>{{ t.entry_date }} → {{ t.exit_date }}<br><span class="small">{{ "{:,.0f}".format(t.entry_price) }} → {{ "{:,.0f}".format(t.final_price) }}</span></td>
      <td>{{ 'O' if t.first_tp_done else 'X' }}</td>
      <td class="{{ 'ok' if t.pnl_pct > 0 else 'bad' }}">{{ t.pnl_pct }}%</td>
      <td>{{ t.exit_reason }}</td>
      <td class="small">{{ ", ".join(t.score_detail.reasons) }}</td>
    </tr>
    {% endfor %}
  </table>
</div>

<div class="card">
  <h2>월별 성과</h2>
  <table>
    <tr><th>월</th><th>거래수</th><th>승률</th><th>손익</th><th>평균</th><th>MDD</th></tr>
    {% for m in months %}
    <tr><td>{{ m.month }}</td><td>{{ m.total }}</td><td>{{ m.win_rate }}%</td><td class="{{ 'ok' if m.total_pnl > 0 else 'bad' }}">{{ m.total_pnl }}%</td><td>{{ m.avg_pnl }}%</td><td>{{ m.mdd }}%</td></tr>
    {% endfor %}
  </table>
</div>
</body>
</html>
"""


def chart_points(curve):
    if not curve:
        return []
    vals = [c["equity"] for c in curve]
    mn, mx = min(vals), max(vals)
    if mn == mx:
        mn -= 1
        mx += 1
    pts = []
    n = len(vals)
    for i, v in enumerate(vals):
        x = 20 + (960 * i / max(n - 1, 1))
        y = 200 - ((v - mn) / (mx - mn) * 170)
        pts.append(f"{x:.1f},{y:.1f}")
    return pts


@app.route("/")
def index():
    p = current_params()
    trades, event_reports, summary, curve, months, latest_rows = build_data(p)
    return render_template_string(
        HTML,
        trades=trades[:120],
        event_reports=event_reports,
        summary=summary,
        curve=curve,
        months=months,
        latest_rows=latest_rows,
        p=p,
        chart_points=chart_points(curve),
    )


@app.route("/api/backtest")
def api_backtest():
    p = current_params()
    trades, event_reports, summary, curve, months, latest_rows = build_data(p)
    return jsonify({
        "params": p.__dict__,
        "summary": summary,
        "trades": trades,
        "equity_curve": curve,
        "monthly": months,
        "event_reports": event_reports,
    })


@app.route("/health")
def health():
    return jsonify({"ok": True, "version": "1.1-backtest-lab"})
