import os
import sys
import subprocess

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)


def _launch(module, *args):
    """Launch a chart module as an independent process (non-blocking)."""
    subprocess.Popen(
        [sys.executable, "-m", module, *args],
        cwd=PROJECT_ROOT,
    )


def run_parallel(tickers, lookback_months):
    # Fire off every chart without waiting — each runs in its own Python process
    # so all windows appear together instead of blocking on plt.show() one at a time.
    lookback = str(lookback_months)
    for ticker in tickers:
        ticker = ticker.strip().upper()
        if not ticker:
            continue
        _launch("charts.vwap", ticker)
        _launch("charts.rsi_trend", ticker)
        _launch("charts.stockChart", ticker, lookback)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        tickers_input = input("Enter stock ticker symbols separated by commas (e.g., AAPL, MSFT): ")
        tickers = [ticker.strip() for ticker in tickers_input.split(',')]
        lookback_time = input("Enter the lookback period in months: ").strip()
    else:
        tickers = sys.argv[1].split(',')
        lookback_time = sys.argv[2]

    if not lookback_time.isdigit():
        print("Lookback period must be a valid number.")
    else:
        run_parallel(tickers, lookback_time)
