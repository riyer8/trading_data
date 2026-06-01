# Trading Data Tools

A small toolkit of Python scripts for exploring the stock market: screening a watchlist for
movers, charting price action and technical indicators, and digging into fundamentals. Most
tools either pop up an interactive [Tkinter](https://docs.python.org/3/library/tkinter.html)
table or a [matplotlib](https://matplotlib.org/) chart, all powered by
[yfinance](https://github.com/ranaroussi/yfinance) market data.

Think of it as a personal Bloomberg-lite you run from the terminal.

---

## Quick start

```sh
# 1. (optional) create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. install dependencies
pip install -r requirements.txt

# 3. run any tool as a module from the project root
python -m screeners.dailyMovers
python -m charts.vwap AAPL
python -m launchers.openAllTickerApps
```

> **Run from the repo root.** Tools are organized into packages (`screeners`, `charts`, ...),
> so the `python -m <package>.<module>` form lets Python resolve the shared imports. Each
> script also adds the project root to `sys.path`, so running a file directly
> (`python screeners/dailyMovers.py`) works too.

---

## Project layout

```
trading_data/
├── portfolio/          # the ticker universe everything else reads from
│   └── portfolioInfo.py
├── screeners/          # scan the whole watchlist → interactive tables
│   ├── dailyMovers.py
│   ├── marketHeatMap.py
│   ├── sectorAnalysis.py
│   ├── technicalIndicators.py
│   ├── earningsTracker.py
│   ├── correlation.py
│   └── daysOfMovement.py
├── charts/             # single-ticker price & indicator visualizations
│   ├── stockChart.py
│   ├── ema.py
│   ├── rsi_trend.py
│   └── vwap.py
├── fundamentals/       # earnings, revenue, margins, market cap over time
│   ├── marketcap.py
│   ├── eps.py
│   ├── operatingdollars.py
│   ├── quarteroverquarter_revenue.py
│   └── yearoveryear_revenue.py
├── launchers/          # convenience scripts that open several tools at once
│   ├── openAllTickerApps.py
│   └── openSingleTickerApp.py
├── experiments/        # scratch / non-trading prototypes
│   └── pricedata.py
├── requirements.txt
└── README.md
```

The dependency flow is simple: `portfolio/portfolioInfo.py` defines the lists of tickers, and
the screeners, charts, and fundamentals all import from it. The launchers just orchestrate the
other tools.

---

## The tools

### `portfolio/` — your watchlist

| File | What it does |
| --- | --- |
| `portfolioInfo.py` | Defines tickers grouped by sector (technology, semiconductors, energy, ...) and assembles them into `MY_TICKERS` / `ALL_TICKERS`. **This is the file you edit to change what every other tool looks at.** |

### `screeners/` — scan the whole list

| File | What it does | Run it |
| --- | --- | --- |
| `dailyMovers.py` | Ranks your tickers by daily % change with price, volume, and volatility. Double-click a row for a candlestick chart. | `python -m screeners.dailyMovers` |
| `marketHeatMap.py` | Red/blue heat map of 5-day % change across every ticker. | `python -m screeners.marketHeatMap` |
| `sectorAnalysis.py` | Bar charts of price and volume performance by sector over the last month. | `python -m screeners.sectorAnalysis` |
| `technicalIndicators.py` | Sortable table of RSI, P/E, 50-day MA, short interest, and beta for each ticker. | `python -m screeners.technicalIndicators` |
| `earningsTracker.py` | Upcoming earnings dates, sortable by ticker, company, sector, or date. | `python -m screeners.earningsTracker` |
| `correlation.py` | Finds tickers most similar to a target symbol using a weighted blend of sector, market cap, beta, volume, liquidity, return correlation, and financial ratios. | `python -m screeners.correlation` _(prompts for `AAPL` + min correlation)_ |
| `daysOfMovement.py` | Color-coded table of the last 15 days of % moves for a ticker and its peers. | `python -m screeners.daysOfMovement` _(prompts for `AAPL`)_ |

### `charts/` — focus on one ticker

| File | What it does | Run it |
| --- | --- | --- |
| `stockChart.py` | Interactive candlestick chart with moving averages and Bollinger Bands; drag to zoom, double-click to reset. | `python -m charts.stockChart AAPL 6` |
| `ema.py` | 20 / 50 / 200-day exponential moving averages with the latest values annotated. | `python -m charts.ema AAPL` |
| `rsi_trend.py` | Closing price plus 14-day RSI with overbought/oversold lines. | `python -m charts.rsi_trend AAPL` |
| `vwap.py` | VWAP vs. close with the gap shaded bullish/bearish. | `python -m charts.vwap AAPL` |

### `fundamentals/` — the longer-term picture

| File | What it does | Run it |
| --- | --- | --- |
| `marketcap.py` | Historical market-cap growth for selected tickers. | `python -m fundamentals.marketcap` |
| `eps.py` | Quarterly EPS comparison across a group of tickers. | `python -m fundamentals.eps` |
| `operatingdollars.py` | Operating margin trend over the last ~12 quarters. | `python -m fundamentals.operatingdollars` |
| `quarteroverquarter_revenue.py` | Quarter-over-quarter revenue change (sample data). | `python -m fundamentals.quarteroverquarter_revenue` |
| `yearoveryear_revenue.py` | Year-over-year revenue growth with a forward estimate (sample data). | `python -m fundamentals.yearoveryear_revenue` |

### `launchers/` — open several at once

| File | What it does | Run it |
| --- | --- | --- |
| `openAllTickerApps.py` | Spawns the earnings tracker, daily movers, heat map, sector analysis, and technical indicators in parallel. | `python -m launchers.openAllTickerApps` |
| `openSingleTickerApp.py` | Opens VWAP, RSI, and candlestick views for one or more tickers at once. | `python -m launchers.openSingleTickerApp AAPL 6` |

---

## Customizing

- **Change the universe:** edit the sector lists in `portfolio/portfolioInfo.py`. Everything
  downstream picks up the change automatically.
- **Tweak analysis windows:** date ranges, lookback periods, and indicator parameters live as
  constants near the top of each script.
- **Correlation weighting:** adjust `CORRELATION_WEIGHTS` in `screeners/correlation.py` to
  emphasize the factors you care about.

## Notes

- Data comes from Yahoo Finance via `yfinance`, which is rate-limited and occasionally returns
  gaps. Several scripts already retry with backoff.
- The interactive tables and charts require a desktop environment (Tkinter + a matplotlib GUI
  backend); they won't render on a headless server.
- Files in `experiments/` and a few `fundamentals/` prototypes are personal scratch work and are
  intentionally git-ignored.

## Roadmap

More screeners, cleaner data caching, and configuration via a single settings file are on the
way.
