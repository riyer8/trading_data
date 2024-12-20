import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd

def calculate_vwap(data):
    vwap = (data['Close'] * data['Volume']).cumsum() / data['Volume'].cumsum()
    return vwap

def plot_vwap(ticker, period='1y', interval='1d'):
    data = yf.download(ticker, period=period, interval=interval)
    
    data['VWAP'] = calculate_vwap(data)

    plt.figure(figsize=(6, 3.6))
    plt.plot(data.index, data['Close'], label='Close Price', color='blue', linewidth=1.5)
    plt.plot(data.index, data['VWAP'], label='VWAP', color='orange', linewidth=2)
    
    plt.title(f'{ticker} Price and VWAP', fontsize=16)
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Price', fontsize=12)
    
    plt.fill_between(data.index, data['Close'], data['VWAP'], where=(data['Close'] > data['VWAP']),
                     color='green', alpha=0.3, label='Price Above VWAP (Bullish)')
    plt.fill_between(data.index, data['Close'], data['VWAP'], where=(data['Close'] < data['VWAP']),
                     color='red', alpha=0.3, label='Price Below VWAP (Bearish)')

    plt.legend()
    plt.ylim(data['Close'].min() - 10, data['Close'].max() + 10)

    last_price = data['Close'].iloc[-1]
    last_vwap = data['VWAP'].iloc[-1]
    
    if last_price > last_vwap:
        sentiment = "Bullish"
        plt.annotate(f'Latest Price: {last_price:.2f}\n{sentiment}', 
                     xy=(data.index[-1], last_price), 
                     xytext=(data.index[-1], last_price + 10),
                     arrowprops=dict(facecolor='green', shrink=0.05), 
                     fontsize=10, color='green')
    elif last_price < last_vwap:
        sentiment = "Bearish"
        plt.annotate(f'Latest Price: {last_price:.2f}\n{sentiment}', 
                     xy=(data.index[-1], last_price), 
                     xytext=(data.index[-1], last_price - 10),
                     arrowprops=dict(facecolor='red', shrink=0.05), 
                     fontsize=10, color='red')
    else:
        plt.annotate(f'Latest Price: {last_price:.2f}\nNeutral', 
                     xy=(data.index[-1], last_price), 
                     xytext=(data.index[-1], last_price),
                     fontsize=10, color='black')

    plt.grid()
    plt.tight_layout()
    
    plt.show()
    latest_data = data.tail(5)[['Close', 'VWAP']]
    print("\nLatest 5 Closing Prices and VWAP Values:")
    print(latest_data)

if __name__ == "__main__":
    ticker_symbol = input("Enter the stock ticker symbol (e.g., AAPL): ")
    plot_vwap(ticker_symbol)