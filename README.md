# Trading Data Tools

A suite of Python scripts for analyzing, visualizing, and screening stock market data using [yfinance](https://github.com/ranaroussi/yfinance), [matplotlib](https://matplotlib.org/), and [tkinter](https://docs.python.org/3/library/tkinter.html).

---

## 📊 Main Tools & Scripts

### `correlation.py`

Finds tickers most correlated to a target symbol using sector, industry, market cap, beta, volume, liquidity, and financial ratios. Interactive GUI for sorting and filtering.

### `dailyMovers.py`

Displays top-moving stocks from your portfolio, showing price, percentage change, volume, and volatility. Double-click a ticker for a candlestick chart.

### `daysOfMovement.py`

Shows the last 15 days’ percentage price changes for a ticker and its correlated peers in a sortable, color-coded table.

### `earningsTracker.py`

Lists upcoming earnings dates for tracked tickers, sortable by ticker, company, sector, or date.

### `ema.py`

Plots 20, 50, and 200-day Exponential Moving Averages (EMA) for a given ticker, with annotated latest values.

### `marketcap.py`

Visualizes historical market capitalization growth for selected tickers over a specified date range.

### `marketHeatMap.py`

Generates a heat map of percentage price changes for all tickers over the last 5 days, with color intensity reflecting movement.

### `openAllTickerApps.py`

Launches all major GUI applications (earnings tracker, daily movers, heat map, sector analysis, technical indicators) in parallel.

### `openSingleTickerApp.py`

Runs VWAP, RSI, and candlestick chart visualizations for one or more tickers in parallel.

### `portfolioInfo.py`

Defines ticker lists for various sectors and aggregates them for use across all scripts.

### `rsi_trend.py`

Plots closing prices and 14-day RSI for a ticker, highlighting overbought/oversold levels.

### `sectorAnalysis.py`

Analyzes sector performance over the last month, visualizing price and volume changes for each sector.

### `stockChart.py`

Displays interactive candlestick charts with moving averages and Bollinger Bands. Supports zooming and lookback period selection.

### `technicalIndicators.py`

Shows a sortable table of technical indicators (RSI, P/E, moving averages, short interest, beta) for all portfolio tickers.

### `vwap.py`

Plots VWAP and closing price for a ticker, highlighting bullish/bearish sentiment and showing recent values.

---

## 🗂️ Other Files

- `.gitignore`: Excludes cache, temp files, and some scripts from version control.
- `README.md`: This file.

---

## 🚀 Getting Started

1. Install dependencies:
   ```sh
   pip install yfinance matplotlib mplfinance tksheet scipy
   ```
2. Run any script directly:
   ```sh
   python dailyMovers.py
   ```
3. For GUIs, follow prompts or use command-line arguments as decribed in each script.

## Customization

- Add / remove tickets in `portfolioInfo.py`
- Adjust analysis parameters in each script as needed.

## Work in Progress

More features and improvements to come soon.
