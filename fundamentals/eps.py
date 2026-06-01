import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib.pyplot as plt

import datacache
from ui.theme import apply_chart_theme, moving_average_colors, style_legend, set_window_title

DEFAULT_TICKERS = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA']


def get_quarterly_eps(ticker):
    try:
        financials = datacache.ticker_quarterly_financials(ticker)
        if financials is None or financials.empty:
            print(f"No quarterly financials data available for {ticker}")
            return None

        net_income = financials.loc['Net Income']
        shares_outstanding = datacache.ticker_info(ticker).get('sharesOutstanding')
        if not shares_outstanding:
            print(f"Shares outstanding data not available for {ticker}")
            return None

        return (net_income / shares_outstanding).sort_index()
    except Exception as e:
        print(f"Error fetching quarterly financials data for {ticker}: {e}")
        return None


def compare_eps(tickers):
    eps_data = {}
    for ticker in tickers:
        quarterly_eps = get_quarterly_eps(ticker)
        if quarterly_eps is not None:
            eps_data[ticker] = quarterly_eps

    if not eps_data:
        print("No EPS data available for the requested tickers.")
        return

    apply_chart_theme()
    fig, ax = plt.subplots(figsize=(11, 6))
    set_window_title(fig, "Quarterly EPS")

    colors = moving_average_colors(len(eps_data))
    highlight_ticker = tickers[0] if tickers else None
    for (ticker, eps), color in zip(eps_data.items(), colors):
        highlight = ticker == highlight_ticker
        ax.plot(eps.index, eps.values, label=ticker, color=color,
                linewidth=3 if highlight else 1.4, marker='o', markersize=3,
                alpha=1.0 if highlight else 0.9)

    ax.set_xlabel('Quarter')
    ax.set_ylabel('Earnings Per Share (EPS)')
    ax.set_title('Quarterly Earnings Per Share Growth')
    ax.margins(x=0.02)
    style_legend(ax, loc='best')

    fig.autofmt_xdate(rotation=30)
    fig.tight_layout()
    plt.show()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        tickers = [t.strip().upper() for t in sys.argv[1].split(',') if t.strip()]
    else:
        user_input = input(f"Enter tickers separated by commas (default: {', '.join(DEFAULT_TICKERS)}): ").strip()
        tickers = [t.strip().upper() for t in user_input.split(',') if t.strip()] or DEFAULT_TICKERS
    compare_eps(tickers)
