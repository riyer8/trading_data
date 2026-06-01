import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import sys

def calculate_rsi(data, period=14):
    """Calculate the Relative Strength Index (RSI)."""
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def annotate_last_value(ax, data, label, color):
    """Annotate the last value on the plot."""
    last_date = data.index[-1]
    last_value = data[-1]
    ax.text(last_date, last_value, f'{last_value:.2f}', color=color, 
            fontsize=10, fontweight='bold', verticalalignment='bottom')

def plot_rsi(ticker):
    """Plot the closing prices and RSI for a given ticker."""
    data = yf.download(ticker, start="2024-01-01", end="2024-12-31")

    if data.empty:
        print(f"No data found for ticker symbol: {ticker}")
        return

    data['RSI'] = calculate_rsi(data)

    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    # Plot the closing price
    ax1.plot(data['Close'], label='Closing Price', color='black', linewidth=1.5)
    annotate_last_value(ax1, data['Close'], 'Closing Price', 'black')

    ax1.set_title(f"{ticker} Closing Prices", fontsize=16)
    ax1.set_ylabel("Price", fontsize=12)
    ax1.legend(loc='upper left')
    ax1.grid(True)

    # Plot the RSI
    ax2.plot(data['RSI'], label='RSI (14)', color='purple', linewidth=1.5)
    ax2.axhline(70, color='red', linestyle='--', linewidth=1)
    ax2.axhline(30, color='green', linestyle='--', linewidth=1)
    
    ax2.set_title("Relative Strength Index (RSI)", fontsize=16)
    ax2.set_ylabel("RSI", fontsize=12)
    ax2.set_ylim(0, 100)
    ax2.legend(loc='upper left')
    ax2.grid(True)

    plt.xticks(rotation=30)
    plt.xlabel("Date", fontsize=12)
    plt.tight_layout()

    plt.show()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        ticker_input = input("Enter a valid stock ticker symbol: ")
    else:
        ticker_input = sys.argv[1]
    
    plot_rsi(ticker_input)