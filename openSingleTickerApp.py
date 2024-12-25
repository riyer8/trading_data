import sys
import multiprocessing
from vwap import plot_vwap
from rsi_trend import plot_rsi
from stockChart import main as plot_stock_chart

def run_vwap(ticker):
    plot_vwap(ticker)

def run_rsi(ticker):
    plot_rsi(ticker)

def run_stock_chart(ticker, lookback_months):
    plot_stock_chart(ticker, lookback_months)

def run_parallel(tickers, lookback_months):
    with multiprocessing.Pool(processes=len(tickers)) as pool:
        pool.starmap(run_vwap, [(ticker,) for ticker in tickers])
        pool.starmap(run_rsi, [(ticker,) for ticker in tickers])
        pool.starmap(run_stock_chart, [(ticker, lookback_months) for ticker in tickers])  # Pass lookback_months

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