# Trading Data

Local tools for a watchlist: what moved, how a ticker looks, and the longer-term numbers. Data comes from Yahoo Finance and sits in `.datacache/` for 30 minutes so the apps don't keep hitting the network.

Double-click a row in any table to open that ticker's candlestick chart and a snapshot of the company.

## Venv + setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

From the repo root:

```bash
python -m launchers.openAllTickerApps
python -m chatbot
python -m charts.stockChart AAPL 6
```

The watchlist is `portfolio/portfolioInfo.py` (it's customizable to which ones that you want to track!)

## Overall Dir

- [screeners/](screeners/README.md) — scans across the watchlist
- [charts/](charts/README.md) — one ticker at a time
- [fundamentals/](fundamentals/README.md) — earnings, margins, market cap
- [launchers/](launchers/README.md) — open several tools together
- [chatbot/](chatbot/README.md) — ask it to open a tool

`ui/` is the shared dark theme. `datacache/` is the shared cache. Set `TRADING_DATA_CACHE_TTL` (seconds, default `1800`) if you want a different lifetime.
