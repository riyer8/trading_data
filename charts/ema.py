import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd

START_DATE = "2024-01-01"
END_DATE = "2024-12-31"

def calculate_ema(data, period):
    return data['Close'].ewm(span=period, adjust=False).mean()

def annotate_last_value(ax, data, label, color):
    last_date = data.index[-1]
    last_value = data[-1]
    ax.text(last_date, last_value, f'{last_value:.2f}', color=color, 
            fontsize=10, fontweight='bold', verticalalignment='bottom')

def plot_ema(ticker):
    data = yf.download(ticker, start=START_DATE, end=END_DATE)

    if data.empty:
        print(f"No data found for ticker symbol: {ticker}")
        return

    data['20-day EMA'] = calculate_ema(data, 20)
    data['50-day EMA'] = calculate_ema(data, 50)
    data['200-day EMA'] = calculate_ema(data, 200)

    fig, ax = plt.subplots(figsize=(6, 4))
    
    ax.plot(data['Close'], label='Closing Price', color='black', linewidth=1.5)
    ax.plot(data['20-day EMA'], label='20-day EMA', color='blue', linestyle='--', linewidth=1.2)
    ax.plot(data['50-day EMA'], label='50-day EMA', color='orange', linestyle='--', linewidth=1.2)
    ax.plot(data['200-day EMA'], label='200-day EMA', color='red', linestyle='--', linewidth=1.2)

    annotate_last_value(ax, data['Close'], 'Closing Price', 'black')
    annotate_last_value(ax, data['20-day EMA'], '20-day EMA', 'blue')
    annotate_last_value(ax, data['50-day EMA'], '50-day EMA', 'orange')
    annotate_last_value(ax, data['200-day EMA'], '200-day EMA', 'red')

    ax.set_title(f"{ticker} EMAs", fontsize=16)
    plt.xticks(rotation=30)
    ax.set_xlabel("Date", fontsize=12)
    ax.set_ylabel("Closing Price", fontsize=12)
    ax.legend(loc='upper left')
    ax.grid(True)
    plt.tight_layout()

    plt.show()

if __name__ == "__main__":
    ticker_input = input("Enter a valid stock ticker symbol: ")
    plot_ema(ticker_input)