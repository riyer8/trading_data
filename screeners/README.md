# Screeners

Scans across the watchlist in `portfolio/portfolioInfo.py`. Most of these open a table. Double-click a row to open that ticker's chart and snapshot.

## Run

From the repo root:

```bash
python -m screeners.dailyMovers
python -m screeners.earningsTracker
```

| File | What it does | Run it |
| --- | --- | --- |
| `dailyMovers.py` | Ranks the watchlist by daily % change, with price, volume, and volatility. | `python -m screeners.dailyMovers` |
| `marketHeatMap.py` | Heat map of daily % change. | `python -m screeners.marketHeatMap` |
| `sectorAnalysis.py` | Price, volume, and a sum of prices by sector over the last month. | `python -m screeners.sectorAnalysis` |
| `technicalIndicators.py` | RSI, P/E, 50-day average, short interest, and beta. | `python -m screeners.technicalIndicators` |
| `earningsTracker.py` | Upcoming earnings, soonest first. Click a column header to re-sort. | `python -m screeners.earningsTracker` |
| `correlation.py` | Tickers closest to one symbol. It asks for the symbol and a minimum correlation. | `python -m screeners.correlation` |
| `daysOfMovement.py` | Last 15 days of % moves for a ticker and a few correlated names. | `python -m screeners.daysOfMovement` |

Correlation weights live at the top of `correlation.py` (`CORRELATION_WEIGHTS`).
