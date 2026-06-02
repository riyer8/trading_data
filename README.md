# Trading Data Tools

A small toolkit of Python scripts for exploring the stock market: screening a watchlist for
movers, charting price action and technical indicators, and digging into fundamentals. Most
tools either pop up an interactive [Tkinter](https://docs.python.org/3/library/tkinter.html)
table or a [matplotlib](https://matplotlib.org/) chart, all powered by
[yfinance](https://github.com/ranaroussi/yfinance) market data.

Think of it as a personal Bloomberg-lite you run from the terminal.

Charts and tables share a **dark trading-desk theme** (`ui/theme.py`) and a **30-minute
on-disk data cache** (`datacache/`) so repeated lookups across apps don't re-hit Yahoo Finance.

---

## Quick start

```sh
# 1. (optional) create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\\Scripts\\activate

# 2. install dependencies
pip install -r requirements.txt

# 3. run any tool as a module from the project root
python -m screeners.dailyMovers
python -m charts.vwap AAPL
python -m launchers.openAllTickerApps
python -m launchers.openSingleTickerApp AAPL 6

# 4. run the chatbot assistant (optional)
pip install -r chatbot/requirements.txt
python -m chatbot
```

> **Run from the repo root.** Tools are organized into packages (`screeners`, `charts`, …),
> so the `python -m <package>.<module>` form lets Python resolve the shared imports. Each
> script also adds the project root to `sys.path`, so running a file directly
> (`python screeners/dailyMovers.py`) works too.

---

## Project layout

```
trading_data/
├── portfolio/          # the ticker universe everything else reads from
│   └── portfolioInfo.py
├── datacache/          # shared 30-min on-disk cache for yfinance lookups
│   └── __init__.py
├── ui/                 # shared dark “trading desk” styling for charts & tables
│   └── theme.py
├── screeners/          # scan the whole watchlist → interactive tables / charts
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
├── fundamentals/       # earnings, margins, market cap over time
│   ├── marketcap.py
│   ├── eps.py
│   └── operatingdollars.py
├── launchers/          # convenience scripts that open several tools at once
│   ├── openAllTickerApps.py
│   └── openSingleTickerApp.py
├── chatbot/            # interactive assistant UI and local tool launcher
│   ├── __main__.py
│   ├── app.py
│   ├── entities.py
│   ├── intent.py
│   ├── launcher.py
│   ├── llm.py
│   ├── offline.py
│   ├── rag.py
│   ├── requirements.txt
│   ├── tool_specs.py
│   └── widgets.py
├── experiments/        # scratch / non-trading prototypes (local only)
│   └── pricedata.py
├── .datacache/         # auto-generated market-data cache (git-ignored)
├── requirements.txt
└── README.md
```

The dependency flow is simple: `portfolio/portfolioInfo.py` defines the lists of tickers
(`MY_TICKERS` for your curated watchlist, `ALL_TICKERS` for a broader universe), and the
screeners, charts, and fundamentals all import from it. Data fetching goes through
`datacache` instead of calling `yfinance` directly. The launchers orchestrate the other tools.

---

## The tools

### `portfolio/` — your watchlist

| File | What it does |
| --- | --- |
| `portfolioInfo.py` | Defines tickers grouped by sector (technology, semiconductors, energy, …) and assembles them into `MY_TICKERS` / `ALL_TICKERS`. **This is the file you edit to change what every other tool looks at.** |

### `screeners/` — scan the whole list

| File | What it does | Run it |
| --- | --- | --- |
| `dailyMovers.py` | Ranks your watchlist by daily % change with price, volume, and volatility. Double-click a row to open a candlestick chart. | `python -m screeners.dailyMovers` |
| `marketHeatMap.py` | Dark heat map of daily % change across every ticker in `MY_TICKERS`. | `python -m screeners.marketHeatMap` |
| `sectorAnalysis.py` | Three bar charts (price, volume, sum of prices) by sector over the last month — each opens in its own window, all at once. | `python -m screeners.sectorAnalysis` |
| `technicalIndicators.py` | Sortable table of RSI, P/E, 50-day MA, short interest, and beta for each ticker. | `python -m screeners.technicalIndicators` |
| `earningsTracker.py` | Upcoming earnings dates, sorted soonest-first by default; click column headers to re-sort. | `python -m screeners.earningsTracker` |
| `correlation.py` | Finds tickers most similar to a target symbol using a weighted blend of sector, market cap, beta, volume, liquidity, return correlation, and financial ratios. | `python -m screeners.correlation` _(prompts for `AAPL` + min correlation)_ |
| `daysOfMovement.py` | Color-coded [tksheet](https://github.com/ragnerok/tksheet) grid of the last 15 days of % moves for a ticker and its top correlated peers. Click a column to sort. | `python -m screeners.daysOfMovement` _(prompts for `AAPL`)_ |

### `charts/` — focus on one ticker

| File | What it does | Run it |
| --- | --- | --- |
| `stockChart.py` | Interactive candlestick chart with moving averages and Bollinger Bands. Drag to zoom in (green selection tint), double-click to reset. | `python -m charts.stockChart AAPL 6` |
| `ema.py` | 20 / 50 / 200-day exponential moving averages with latest values annotated. | `python -m charts.ema AAPL` |
| `rsi_trend.py` | Closing price plus 14-day RSI with overbought/oversold zones. | `python -m charts.rsi_trend AAPL` |
| `vwap.py` | VWAP vs. close with the gap shaded bullish/bearish. | `python -m charts.vwap AAPL` |

### `fundamentals/` — the longer-term picture

| File | What it does | Run it |
| --- | --- | --- |
| `marketcap.py` | Historical market-cap growth for every ticker in `MY_TICKERS`, with a scrollable color-coded key beside the chart. | `python -m fundamentals.marketcap` |
| `eps.py` | Quarterly EPS comparison; defaults to big-tech tickers. | `python -m fundamentals.eps` or `python -m fundamentals.eps AAPL,MSFT` |
| `operatingdollars.py` | Operating margin trend over the last 12 quarters for a single ticker. | `python -m fundamentals.operatingdollars AAPL` |

### `launchers/` — open several at once

| File | What it does | Run it |
| --- | --- | --- |
| `openAllTickerApps.py` | Spawns the earnings tracker, daily movers, heat map, sector analysis, and technical indicators in parallel. | `python -m launchers.openAllTickerApps` |
| `openSingleTickerApp.py` | Opens VWAP, RSI, and candlestick views for one or more tickers in parallel (all windows at once). | `python -m launchers.openSingleTickerApp AAPL 6` |

### `chatbot/` — interactive assistant

| File | What it does | Run it |
| --- | --- | --- |
| `__main__.py` | Launches a Tkinter chatbot UI that can query the trading tools and local README knowledge. | `python -m chatbot` |

---

## Shared infrastructure

### Data cache (`datacache/`)

All market-data fetches go through cached wrappers instead of calling `yfinance` directly:

```python
from datacache import download, ticker_history, ticker_info, ticker_calendar, ticker_quarterly_financials

data = download("AAPL", period="6mo", interval="1d")
info = ticker_info("AAPL")
```

Results are pickled into `.datacache/` (git-ignored) and reused for **30 minutes**, shared
across every app and process. Override with environment variables:

| Variable | Default | Purpose |
| --- | --- | --- |
| `TRADING_DATA_CACHE_TTL` | `1800` (30 min) | Seconds before a cached entry is refreshed |
| `TRADING_DATA_CACHE_DIR` | `.datacache/` | Where cache files are stored |

Clear everything: `python -c "import datacache; print(datacache.clear_cache(), 'entries removed')"`

### UI theme (`ui/theme.py`)

Central palette, fonts, and helpers used by every chart and table:

- **Charts:** call `apply_chart_theme()` once before creating a figure; use `style_legend()`,
  `value_tag()`, and `candlestick_style()` for mplfinance.
- **Tkinter tables:** call `style_table(root)` and `apply_row_stripes(tree)`.
- **tksheet grids:** call `style_sheet(sheet)`.

---

## Customizing

- **Change the universe:** edit the sector lists in `portfolio/portfolioInfo.py`. Everything
  downstream picks up the change automatically.
- **Tweak analysis windows:** date ranges, lookback periods, and indicator parameters live as
  constants near the top of each script.
- **Correlation weighting:** adjust `CORRELATION_WEIGHTS` in `screeners/correlation.py` to
  emphasize the factors you care about.
- **Cache lifetime:** set `TRADING_DATA_CACHE_TTL=3600` (for example) before running a tool.

---

## Dependencies

Install the core trading tools with:

```sh
pip install -r requirements.txt
```

If you want the chatbot UI, also install:

```sh
pip install -r chatbot/requirements.txt
```

---

## Notes

- Data comes from Yahoo Finance via `yfinance`, which is rate-limited and occasionally returns
gaps. Several scripts retry with backoff; the shared cache reduces duplicate requests.
- The interactive tables and charts require a desktop environment (Tkinter + a matplotlib GUI
  backend); they won't render on a headless server.
- `fundamentals/marketcap.py` embeds matplotlib in a Tk window (for the scrollable legend).
  On macOS, don't mix `pyplot` windows with Tk in the same process — the other charts use
  plain `plt.show()` and are fine.
- `experiments/pricedata.py` is personal scratch work and is intentionally git-ignored.

---

## Roadmap

- Configuration via a single settings file (date ranges, defaults, cache TTL).
- More screeners and richer fundamentals pulled live from yfinance.
