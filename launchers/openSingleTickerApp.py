import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import multiprocessing
from charts.vwap import plot_vwap
from charts.rsi_trend import plot_rsi
from charts.stockChart import main as plot_stock_chart

def run_vwap(ticker):
    plot_vwap(ticker)

def run_rsi(ticker):
    plot_rsi(ticker)

def run_stock_chart(ticker, lookback_months):
    plot_stock_chart(ticker, lookback_months)

def run_parallel(tickers, lookback_months):
    # Start every chart in its own process so all windows open at once. starmap
    # would block on each chart's plt.show() and reveal them one at a time.
    processes = []
    for ticker in tickers:
        processes.append(multiprocessing.Process(target=run_vwap, args=(ticker,)))
        processes.append(multiprocessing.Process(target=run_rsi, args=(ticker,)))
        processes.append(multiprocessing.Process(target=run_stock_chart, args=(ticker, lookback_months)))

    for process in processes:
        process.start()
    for process in processes:
        process.join()

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