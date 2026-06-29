from functools import lru_cache
from .config import EXTRA_SELL_SIDECAR_DATES, EXTRA_BUY_SIDECAR_DATES

DEFAULT_EVENTS = [
    {"date":"20250623","market":"KOSPI","side":"SELL","time":"09:46","source":"reported","note":"KOSPI sell-side sidecar"},
    {"date":"20251105","market":"KOSPI","side":"SELL","time":"09:46","source":"reported","note":"KOSPI sell-sidecar"},
    {"date":"20260608","market":"KOSPI","side":"SELL","time":"09:34","source":"reported","note":"KOSPI sell-sidecar"},
    {"date":"20260610","market":"KOSPI","side":"SELL","time":"13:17","source":"reported","note":"KOSPI sell-sidecar"},
    {"date":"20260612","market":"KOSPI","side":"BUY","time":"-","source":"reported","note":"KOSPI buy-sidecar"},
    {"date":"20260615","market":"KOSPI","side":"BUY","time":"09:06","source":"reported","note":"KOSPI buy-sidecar"},
    {"date":"20260626","market":"KOSPI","side":"SELL","time":"11:12","source":"reported","note":"KOSPI sell-sidecar"},
]
@lru_cache(maxsize=1)
def get_events():
    events = list(DEFAULT_EVENTS)
    for d in EXTRA_SELL_SIDECAR_DATES: events.append({"date":d,"market":"KOSPI","side":"SELL","time":"-","source":"extra_env","note":"extra sell-sidecar"})
    for d in EXTRA_BUY_SIDECAR_DATES: events.append({"date":d,"market":"KOSPI","side":"BUY","time":"-","source":"extra_env","note":"extra buy-sidecar"})
    seen, unique = set(), []
    for e in sorted(events, key=lambda x: (x["date"], x["side"], x["market"])):
        key = (e["date"], e["side"], e["market"])
        if key in seen: continue
        seen.add(key); unique.append(e)
    return sorted(unique, key=lambda x: x["date"], reverse=True)
def get_sell_events(): return sorted([e for e in get_events() if e["side"] == "SELL"], key=lambda x: x["date"])
def get_buy_dates(): return {e["date"] for e in get_events() if e["side"] == "BUY"}
