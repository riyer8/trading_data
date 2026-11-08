# Charts

One ticker at a time. The candlestick chart is the one that opens when you double-click a table row, along with the snapshot.

## Run

From the repo root:

```bash
python -m charts.stockChart AAPL 6
python -m charts.stockDetail AAPL
python -m charts.vwap AAPL
```

`stockChart` takes a ticker and a lookback in months. On the price charts, scroll to zoom, drag to pan, and double-click to reset. The box in the corner describes the bar under the cursor.

| File | What it does | Run it |
| --- | --- | --- |
| `stockChart.py` | Candlestick chart with moving averages and Bollinger Bands. | `python -m charts.stockChart AAPL 6` |
| `stockDetail.py` | One window with price, technicals, fundamentals, earnings, and a short company summary. | `python -m charts.stockDetail AAPL` |
| `ema.py` | 20 / 50 / 200-day exponential moving averages. | `python -m charts.ema AAPL` |
| `rsi_trend.py` | Close plus 14-day RSI. | `python -m charts.rsi_trend AAPL` |
| `vwap.py` | Close against the 20-day volume-weighted average price. | `python -m charts.vwap AAPL` |
