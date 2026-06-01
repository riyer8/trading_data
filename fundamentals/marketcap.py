import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import datacache
import matplotlib.pyplot as plt
from portfolio.portfolioInfo import MY_TICKERS
from ui.theme import Colors, apply_chart_theme, moving_average_colors, style_legend, set_window_title

def get_historical_market_cap(ticker, start_date, end_date):
    history = datacache.ticker_history(ticker, start=start_date, end=end_date)
    market_cap = history['Close'] * datacache.ticker_info(ticker)['sharesOutstanding']
    return market_cap

def compare_market_caps(tickers, start_date, end_date):
    market_caps = {}
    
    for ticker in tickers:
        historical_market_cap = get_historical_market_cap(ticker, start_date, end_date)
        if historical_market_cap is not None:
            market_caps[ticker] = historical_market_cap

    apply_chart_theme()
    fig, ax = plt.subplots(figsize=(11, 6))
    set_window_title(fig, "Market Capitalization")

    series_colors = moving_average_colors(len(market_caps))
    for (ticker, market_cap), color in zip(market_caps.items(), series_colors):
        highlight = ticker == 'PYPL'
        ax.plot(market_cap.index, market_cap.values, label=ticker, color=color,
                linewidth=3 if highlight else 1.3, alpha=1.0 if highlight else 0.85)

    ax.set_xlabel('Date')
    ax.set_ylabel('Market Capitalization')
    ax.set_title('Market Capitalization Growth Over Quarters')
    ax.yaxis.set_major_formatter(lambda x, _pos: f"${x / 1e9:.0f}B")
    ax.margins(x=0.01)
    style_legend(ax, loc='upper left')

    fig.autofmt_xdate(rotation=30)
    fig.tight_layout()
    plt.show()

if __name__ == "__main__": 
    start_date = "2023-05-01"
    end_date = "2024-01-01"
    compare_market_caps(MY_TICKERS, start_date, end_date)