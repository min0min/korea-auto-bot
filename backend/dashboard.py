from flask import Flask, jsonify, render_template_string
from .config import TICKERS, BACKTEST_YEARS, UNIVERSE_MODE, MIN_AI_SCORE, MAX_PICKS_PER_EVENT, FIRST_TAKE_PROFIT, FIRST_TAKE_RATIO, FINAL_TAKE_PROFIT, STOP_LOSS, MAX_HOLD_DAYS, STRATEGY_NAME
from .data_source import get_ohlcv
from .indicators import add_indicators
from .strategy import backtest_v10, summarize_trades
from .sidecar_events import get_events

app = Flask(__name__)

def load_stock_data():
    data = {}
    for ticker, name in TICKERS.items():
        df = add_indicators(get_ohlcv(ticker))
        data[ticker] = {"name": name, "df": df}
    return data

def build_data():
    stock_data = load_stock_data(); trades, event_reports = backtest_v10(stock_data)
    trades = sorted(trades, key=lambda x: x["entry_date"], reverse=True); summary = summarize_trades(trades)
    latest_rows = []
    for ticker, item in stock_data.items():
        row = item["df"].iloc[-1]
        latest_rows.append({"ticker":ticker,"name":item["name"],"date":str(row["date"]),"close":float(row["close"]),"ma20":float(row["ma20"]),"ma60":float(row["ma60"]),"rsi":round(float(row["rsi"]),1) if row["rsi"]==row["rsi"] else 0,"volume_ratio":round(float(row["volume_ratio"]),2) if row["volume_ratio"]==row["volume_ratio"] else 0,"trend":bool(row["ma20_slope"]>0 and row["close"]>row["ma60"])})
    return stock_data, trades, event_reports, summary, latest_rows

HTML = r'''
<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>Korea AI Trader V1.0</title>
<style>:root{--bg:#070a12;--panel:#141824;--panel2:#1b2030;--line:#2b3348;--txt:#f7f8ff;--muted:#9aa6c7;--green:#79f59b;--red:#ff6b7a;--yellow:#ffc857;--blue:#6577ff;--cyan:#67e8f9}*{box-sizing:border-box}body{background:radial-gradient(circle at 10% 0%,#1e2a52 0,#070a12 42%);color:var(--txt);font-family:Arial,sans-serif;margin:0;padding:28px}.top{display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid var(--line);padding-bottom:18px}h1{margin:0;letter-spacing:-1px}.badge{background:linear-gradient(135deg,#223c7a,#12192e);color:#c9d3ff;padding:8px 14px;border-radius:999px;font-size:14px;border:1px solid #3d56a8}.grid{display:grid;grid-template-columns:repeat(5,1fr);gap:16px;margin:22px 0}.card{background:linear-gradient(180deg,var(--panel2),var(--panel));border:1px solid var(--line);border-radius:20px;padding:22px;margin-bottom:18px;box-shadow:0 12px 30px rgba(0,0,0,.25)}.label{color:var(--muted);font-size:14px}.big{font-size:34px;font-weight:900;color:var(--green);margin-top:10px}.loss{color:var(--red)}table{width:100%;border-collapse:collapse;margin-top:12px}th,td{padding:14px 12px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}th{color:var(--muted);font-size:14px}.ok{color:var(--green);font-weight:800}.bad{color:var(--red);font-weight:800}.wait{color:var(--yellow);font-weight:800}.small{color:var(--muted);font-size:13px;line-height:1.5}.btn{background:linear-gradient(135deg,var(--blue),#4956cf);color:white;border:0;border-radius:12px;padding:11px 16px;font-weight:800;text-decoration:none;display:inline-block}.score{font-size:24px;font-weight:900;color:var(--cyan)}.pill{padding:6px 10px;border-radius:999px;background:rgba(103,232,249,.12);color:var(--cyan);border:1px solid rgba(103,232,249,.3);font-weight:800;font-size:12px}.flow{display:flex;flex-wrap:wrap;gap:10px;margin-top:12px}.step{padding:10px 12px;border:1px solid var(--line);border-radius:12px;background:#101522;color:#dfe6ff;font-weight:700}.arrow{color:var(--muted);align-self:center}</style></head>
<body><div class="top"><h1>Korea AI Trader <span class="badge">V1.0 Hybrid Sidecar Analyzer</span></h1><a class="btn" href="/">새로고침</a></div>
<div class="grid"><div class="card"><div class="label">총 손익</div><div class="big {{ 'loss' if summary.total_pnl < 0 else '' }}">{{ summary.total_pnl }}%</div></div><div class="card"><div class="label">승률</div><div class="big">{{ summary.win_rate }}%</div></div><div class="card"><div class="label">거래 수</div><div class="big">{{ summary.total }}회</div></div><div class="card"><div class="label">Profit Factor</div><div class="big">{{ summary.profit_factor }}</div></div><div class="card"><div class="label">MDD</div><div class="big {{ 'loss' if summary.mdd < 0 else '' }}">{{ summary.mdd }}%</div></div></div>
<div class="card"><h2>{{ strategy_name }}</h2><div class="small">유니버스 {{ universe_mode }} · 최근 {{ years }}년 · 이벤트당 상위 {{ max_picks }}개 · 최소 AI {{ min_score }}점</div><div class="flow"><div class="step">공식 매도 사이드카</div><div class="arrow">→</div><div class="step">대형주 전체 스캔</div><div class="arrow">→</div><div class="step">AI 점수 100점</div><div class="arrow">→</div><div class="step">상위 3종목</div><div class="arrow">→</div><div class="step">다음날 시가 진입</div><div class="arrow">→</div><div class="step">+2% 50% 익절</div><div class="arrow">→</div><div class="step">잔여 +5% / MA20 / 3일 / -2%</div></div></div>
<div class="card"><h2>이벤트별 AI 후보 랭킹</h2><table><tr><th>이벤트</th><th>선택 종목</th><th>상위 후보 TOP5</th></tr>{% for er in event_reports %}<tr><td><b>{{ er.event.date }}</b><br><span class="small">{{ er.event.side }} · {{ er.event.note }}</span></td><td>{% if er.selected %}{% for s in er.selected %}<div><span class="score">{{ s.score }}</span> {{ s.name }} {{ s.ticker }}</div>{% endfor %}{% else %}<span class="wait">진입 없음</span>{% endif %}</td><td>{% for c in er.top_candidates[:5] %}<div><span class="pill">{{ c.score }}</span> {{ c.name }} <span class="small">RSI {{ c.score_detail.rsi }} · 거래량 {{ c.score_detail.volume_ratio }}배 · 낙폭 {{ c.score_detail.drop_3d_pct }}%</span></div>{% endfor %}</td></tr>{% endfor %}</table></div>
<div class="card"><h2>거래 분석기</h2><table><tr><th>종목</th><th>AI점수</th><th>신호일</th><th>진입/청산</th><th>1차익절</th><th>수익률</th><th>청산이유</th><th>진입 근거</th></tr>{% for t in trades %}<tr><td><b>{{ t.name }}</b><br><span class="small">{{ t.ticker }}</span></td><td><span class="score">{{ t.ai_score }}</span></td><td>{{ t.signal_date }}</td><td>{{ t.entry_date }} → {{ t.exit_date }}<br><span class="small">{{ "{:,.0f}".format(t.entry_price) }} → {{ "{:,.0f}".format(t.final_price) }}</span></td><td>{{ 'O' if t.first_tp_done else 'X' }}</td><td class="{{ 'ok' if t.pnl_pct > 0 else 'bad' }}">{{ t.pnl_pct }}%</td><td>{{ t.exit_reason }}</td><td class="small">{{ ", ".join(t.score_detail.reasons) }}</td></tr>{% endfor %}</table></div>
<div class="card"><h2>현재 대형주 상태</h2><table><tr><th>종목</th><th>현재가</th><th>MA20</th><th>MA60</th><th>RSI</th><th>거래량</th><th>추세</th></tr>{% for r in latest_rows %}<tr><td><b>{{ r.name }}</b><br><span class="small">{{ r.ticker }}</span></td><td>{{ "{:,.0f}".format(r.close) }}<br><span class="small">{{ r.date }}</span></td><td>{{ "{:,.0f}".format(r.ma20) }}</td><td>{{ "{:,.0f}".format(r.ma60) }}</td><td>{{ r.rsi }}</td><td>{{ r.volume_ratio }}배</td><td class="{{ 'ok' if r.trend else 'bad' }}">{{ 'PASS' if r.trend else 'FAIL' }}</td></tr>{% endfor %}</table></div></body></html>
'''

@app.route("/")
def index():
    _, trades, event_reports, summary, latest_rows = build_data()
    return render_template_string(HTML, trades=trades[:80], event_reports=event_reports, summary=summary, latest_rows=latest_rows, min_score=MIN_AI_SCORE, max_picks=MAX_PICKS_PER_EVENT, strategy_name=STRATEGY_NAME, universe_mode=UNIVERSE_MODE, years=BACKTEST_YEARS)

@app.route("/api/backtest")
def api_backtest():
    _, trades, event_reports, summary, latest_rows = build_data()
    return jsonify({"summary": summary, "trades": trades, "event_reports": event_reports, "latest_rows": latest_rows, "events": get_events()})

@app.route("/health")
def health(): return jsonify({"ok": True, "version": "1.0-hybrid-sidecar-analyzer"})
