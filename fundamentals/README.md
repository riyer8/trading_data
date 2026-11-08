# Fundamentals

The longer view: market cap, earnings, and margins. These open charts, not tables.

## Run

From the repo root:

```bash
python -m fundamentals.marketcap
python -m fundamentals.eps AAPL,MSFT
python -m fundamentals.operatingdollars AAPL
```

| File | What it does | Run it |
| --- | --- | --- |
| `marketcap.py` | Market-cap history for the watchlist, with a color key beside the chart. | `python -m fundamentals.marketcap` |
| `eps.py` | Quarterly EPS. Defaults to a short list of large tech names. | `python -m fundamentals.eps` |
| `operatingdollars.py` | Operating margin over the last 12 quarters for one ticker. | `python -m fundamentals.operatingdollars AAPL` |
