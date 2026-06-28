from .config import TICKERS
from .toss_api import TossAPI
from .strategy import normalize_candles, latest_status, backtest_general


def collect_all(count=300):
    api = TossAPI()
    rows = []
    all_trades = []

    for ticker, name in TICKERS.items():
        item = {
            "ticker": ticker,
            "name": name,
            "ok": False,
            "error": None,
            "quote_url": "",
            "candle_url": "",
            "status": {},
            "trades": [],
        }

        try:
            quote_res = api.get_quote(ticker)
            candle_res = api.get_candles(ticker, count=count)

            item["quote_url"] = quote_res["url"]
            item["candle_url"] = candle_res["url"]

            df = normalize_candles(candle_res["data"])
            status = latest_status(df)
            trades = backtest_general(df)

            item["ok"] = True
            item["status"] = status
            item["trades"] = trades
            all_trades.extend([{**t, "ticker": ticker, "name": name} for t in trades])

        except Exception as e:
            item["error"] = str(e)

        rows.append(item)

    return rows, all_trades
