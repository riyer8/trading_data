import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib.pyplot as plt
import pandas as pd

import datacache
from ui.theme import Colors, Fonts, apply_chart_theme, style_legend, value_tag, set_window_title


def calculate_rsi(data, period=14):
    """Calculate the Relative Strength Index (RSI)."""
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def plot_rsi(ticker):
    """Plot the closing prices and RSI for a given ticker."""
    data = datacache.download(ticker, start="2024-01-01", end="2024-12-31")

    # Recent yfinance returns MultiIndex columns (field, ticker); flatten to a single level.
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    if data.empty:
        print(f"No data found for ticker symbol: {ticker}")
        return

    data['RSI'] = calculate_rsi(data)

    apply_chart_theme()
    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(11, 7.5), sharex=True,
        gridspec_kw={'height_ratios': [3, 1], 'hspace': 0.08},
    )
    set_window_title(fig, f"{ticker.upper()} · Price & RSI")

    # Price panel
    ax1.plot(data.index, data['Close'], label='Close', color=Colors.ACCENT_4, linewidth=1.6)
    value_tag(ax1, data.index[-1], data['Close'].iloc[-1], f"{data['Close'].iloc[-1]:,.2f}", Colors.ACCENT_4)
    ax1.set_title(f"{ticker.upper()}  Closing Price")
    ax1.set_ylabel("Price (USD)")
    style_legend(ax1, loc='upper left')

    # RSI panel with overbought/oversold zones
    ax2.plot(data.index, data['RSI'], label='RSI (14)', color=Colors.ACCENT_3, linewidth=1.6)
    ax2.axhline(70, color=Colors.BEAR, linestyle='--', linewidth=1)
    ax2.axhline(30, color=Colors.BULL, linestyle='--', linewidth=1)
    ax2.axhspan(70, 100, color=Colors.BEAR, alpha=0.08)
    ax2.axhspan(0, 30, color=Colors.BULL, alpha=0.08)
    ax2.set_title("Relative Strength Index", fontsize=Fonts.SUBTITLE)
    ax2.set_ylabel("RSI")
    ax2.set_ylim(0, 100)
    ax2.set_yticks([0, 30, 50, 70, 100])
    ax2.set_xlabel("Date")
    style_legend(ax2, loc='upper left')

    last_rsi = data['RSI'].iloc[-1]
    rsi_color = Colors.BEAR if last_rsi >= 70 else Colors.BULL if last_rsi <= 30 else Colors.ACCENT_3
    value_tag(ax2, data.index[-1], last_rsi, f"{last_rsi:,.1f}", rsi_color)

    fig.autofmt_xdate(rotation=30)
    fig.tight_layout()
    plt.show()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        ticker_input = input("Enter a valid stock ticker symbol: ")
    else:
        ticker_input = sys.argv[1]

    plot_rsi(ticker_input)
