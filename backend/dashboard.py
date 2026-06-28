from flask import Flask, jsonify, render_template_string
from .collector import collect_all
from .strategy import summarize_trades
from .toss_api import TossAPI

app = Flask(__name__)

HTML = """
<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>국장시봇 V0.3</title>
  <style>
    body { background:#0f1014; color:#fff; font-family:Arial, sans-serif; margin:0; padding:28px; }
    .top { display:flex; align-items:center; justify-content:space-between; border-bottom:1px solid #272934; padding-bottom:18px; }
    .badge { background:#163f1f; color:#79ef8c; padding:8px 14px; border-radius:20px; font-size:14px; }
    .grid { display:grid; grid-template-columns:repeat(4,1fr); gap:16px; margin:22px 0; }
    .card { background:#171821; border:1px solid #252735; border-radius:14px; padding:20px; margin-bottom:16px; }
    .big { font-size:30px; font-weight:800; color:#79ef8c; margin-top:10px; }
    table { width:100%; border-collapse:collapse; margin-top:12px; }
    th,td { padding:12px; border-bottom:1px solid #2a2d3a; text-align:left; vertical-align:top; }
    th { color:#8992ad; }
    .ok { color:#79ef8c; font-weight:700; }
    .wait { color:#ffbd4a; font-weight:700; }
    .bad { color:#ff6b6b; font-weight:700; }
    a, button { background:#4058d8; color:white; border:0; border-radius:10px; padding:12px 18px; font-weight:700; text-decoration:none; }
    code { color:#9aa7ff; font-size:12px; }
  </style>
</head>
<body>
  <div class="top">
    <h1>국장시봇 <span class="badge">V0.3 Collector</span></h1>
    <div><a href="/debug">Debug</a> <button onclick="location.reload()">새로고침</button></div>
  </div>

  <div class="grid">
    <div class="card"><div>총 백테스트 손익</div><div class="big">{{ summary.total_pnl }}%</div></div>
    <div class="card"><div>승률</div><div class="big">{{ summary.win_rate }}%</div></div>
    <div class="card"><div>총 거래 수</div><div class="big">{{ summary.total }}회</div></div>
    <div class="card"><div>오늘 신호</div><div class="big">{{ signal_count }}종목</div></div>
  </div>

  <div class="card">
    <h2>실시간 전략 조건 현황</h2>
    <table>
      <tr>
        <th>종목</th><th>현재가</th><th>MA20</th><th>MA60</th><th>거래량</th><th>조건</th><th>백테스트</th><th>API</th>
      </tr>
      {% for r in rows %}
      <tr>
        <td><b>{{ r.name }}</b><br>{{ r.ticker }}</td>
        {% if r.ok %}
          <td>{{ "{:,.0f}".format(r.status.close) }}</td>
          <td>{{ "{:,.0f}".format(r.status.ma20) }}<br><span class="{{ 'ok' if r.status.ma20_up else 'bad' }}">{{ '우상향' if r.status.ma20_up else '아님' }}</span></td>
          <td>{{ "{:,.0f}".format(r.status.ma60) }}<br><span class="{{ 'ok' if r.status.price_above_ma60 else 'bad' }}">{{ '위' if r.status.price_above_ma60 else '아래' }}</span></td>
          <td><span class="{{ 'ok' if r.status.volume_spike else 'wait' }}">{{ "%.2f"|format(r.status.volume_ratio) }}배</span></td>
          <td class="{{ 'ok' if r.status.signal else 'wait' }}">{{ '매수 후보' if r.status.signal else '대기' }}</td>
          <td>{{ r.trades|length }}회</td>
          <td><code>{{ r.candle_url }}</code></td>
        {% else %}
          <td colspan="7" class="bad">{{ r.error }}</td>
        {% endif %}
      </tr>
      {% endfor %}
    </table>
  </div>
</body>
</html>
"""


@app.route("/")
def index():
    rows, trades = collect_all(count=300)
    summary = summarize_trades(trades)
    signal_count = sum(1 for r in rows if r.get("ok") and r.get("status", {}).get("signal"))

    return render_template_string(
        HTML,
        rows=rows,
        trades=trades,
        summary=summary,
        signal_count=signal_count,
    )


@app.route("/api/collector")
def api_collector():
    rows, trades = collect_all(count=300)
    return jsonify({
        "rows": rows,
        "summary": summarize_trades(trades),
    })


@app.route("/debug")
def debug():
    import os
    import sys
    import platform
    import requests
    from datetime import datetime

    public_ip = "확인 실패"
    ip_error = None

    try:
        public_ip = requests.get("https://api.ipify.org", timeout=5).text.strip()
    except Exception as e:
        ip_error = str(e)

    env_status = {
        "TOSS_CLIENT_ID": "있음" if os.getenv("TOSS_CLIENT_ID") else "없음",
        "TOSS_CLIENT_SECRET": "있음" if os.getenv("TOSS_CLIENT_SECRET") else "없음",
        "TOSS_BASE_URL": os.getenv("TOSS_BASE_URL", "없음"),
        "TOSS_ACCOUNT_SEQ": "있음" if os.getenv("TOSS_ACCOUNT_SEQ") else "없음",
        "DRY_RUN": os.getenv("DRY_RUN", "true"),
    }

    token_status = "테스트 전"
    token_detail = ""

    try:
        test_api = TossAPI()
        test_api.ensure_token()
        token_status = "성공"
        token_detail = "토큰 발급 성공"
    except Exception as e:
        token_status = "실패"
        token_detail = str(e)

    html = """
    <!doctype html>
    <html lang="ko">
    <head>
      <meta charset="utf-8">
      <title>국장시봇 Debug</title>
      <style>
        body { background:#0f1014; color:#fff; font-family:Arial, sans-serif; margin:0; padding:28px; }
        .card { background:#171821; border:1px solid #252735; border-radius:14px; padding:20px; margin-bottom:16px; }
        .ok { color:#79ef8c; font-weight:800; }
        .bad { color:#ff6b6b; font-weight:800; }
        table { width:100%; border-collapse:collapse; }
        td, th { padding:12px; border-bottom:1px solid #2a2d3a; text-align:left; }
        a { color:white; background:#4058d8; border-radius:10px; padding:10px 14px; text-decoration:none; font-weight:700; }
        code { color:#79ef8c; font-size:32px; }
      </style>
    </head>
    <body>
      <h1>국장시봇 Debug Center</h1>
      <p><a href="/">대시보드로 돌아가기</a></p>
      <div class="card"><h2>Railway Public IP</h2><code>{{ public_ip }}</code><p class="{{ 'bad' if ip_error else 'ok' }}">{{ ip_error or '이 IP를 토스 허용 IP에 추가하면 됩니다.' }}</p></div>
      <div class="card"><h2>OAuth Token Test</h2><p class="{{ 'ok' if token_status == '성공' else 'bad' }}">상태: {{ token_status }}</p><pre>{{ token_detail }}</pre></div>
      <div class="card"><h2>Environment Variables</h2><table>{% for k, v in env_status.items() %}<tr><th>{{ k }}</th><td>{{ v }}</td></tr>{% endfor %}</table></div>
      <div class="card"><h2>Server Info</h2><table><tr><th>Server Time</th><td>{{ now }}</td></tr><tr><th>Python</th><td>{{ python }}</td></tr><tr><th>Platform</th><td>{{ platform }}</td></tr></table></div>
    </body>
    </html>
    """

    return render_template_string(
        html,
        public_ip=public_ip,
        ip_error=ip_error,
        env_status=env_status,
        token_status=token_status,
        token_detail=token_detail,
        now=datetime.now().isoformat(),
        python=sys.version,
        platform=platform.platform(),
    )
