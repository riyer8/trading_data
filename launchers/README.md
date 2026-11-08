# Launchers

Open several tools at once. Each one starts in its own window.

## Run

From the repo root:

```bash
python -m launchers.openAllTickerApps
python -m launchers.openSingleTickerApp AAPL 6
```

`openSingleTickerApp` takes tickers, then a lookback in months. Several tickers: `AAPL,MSFT`.

| File | What it does | Run it |
| --- | --- | --- |
| `openAllTickerApps.py` | Earnings, daily movers, heat map, sector charts, and technicals. | `python -m launchers.openAllTickerApps` |
| `openSingleTickerApp.py` | VWAP, RSI, and the candlestick chart for one or more tickers. | `python -m launchers.openSingleTickerApp AAPL 6` |

If you leave the arguments off, it asks in the terminal.
