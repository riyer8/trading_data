import yfinance as yf
import matplotlib.pyplot as plt
from portfolioInfo import MY_TICKERS

def get_historical_market_cap(ticker, start_date, end_date):
    stock = yf.Ticker(ticker)
    history = stock.history(start=start_date, end=end_date)
    market_cap = history['Close'] * stock.info['sharesOutstanding']
    return market_cap

def compare_market_caps(tickers, start_date, end_date):
    market_caps = {}
    
    for ticker in tickers:
        historical_market_cap = get_historical_market_cap(ticker, start_date, end_date)
        if historical_market_cap is not None:
            market_caps[ticker] = historical_market_cap

    plt.figure(figsize=(6, 3))

    for ticker, market_cap in market_caps.items():
        if (ticker == 'PYPL'):
            plt.plot(market_cap.index, market_cap.values, label=ticker, linewidth = 3)
        else:
            plt.plot(market_cap.index, market_cap.values, label=ticker, linewidth = 1)

    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Market Capitalization (in billions)', fontsize=12)
    plt.title('Market Capitalization Growth Over Quarters', fontsize=16)
    plt.legend()
    
    # Format y-axis to show billions
    plt.yticks(ticks=plt.yticks()[0], labels=[f"${x/1e9:.2f}B" for x in plt.yticks()[0]], fontsize=10)
    
    plt.grid()
    plt.tight_layout()
    plt.show()

if __name__ == "__main__": 
    start_date = "2023-05-01"
    end_date = "2024-01-01"
    compare_market_caps(MY_TICKERS, start_date, end_date)