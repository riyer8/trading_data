import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib.pyplot as plt
import pandas as pd

import datacache
from ui.theme import Colors, apply_chart_theme, moving_average_colors, style_legend, value_tag, set_window_title

START_DATE = "2024-01-01"
END_DATE = "2024-12-31"


def calculate_ema(data, period):
    return data['Close'].ewm(span=period, adjust=False).mean()


def plot_ema(ticker):
    data = datacache.download(ticker, start=START_DATE, end=END_DATE)

    # Recent yfinance returns MultiIndex columns (field, ticker); flatten to a single level.
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    if data.empty:
        print(f"No data found for ticker symbol: {ticker}")
        return

    periods = [20, 50, 200]
    for period in periods:
        data[f'{period}-day EMA'] = calculate_ema(data, period)

    apply_chart_theme()
    fig, ax = plt.subplots(figsize=(11, 6))
    set_window_title(fig, f"{ticker.upper()} · EMAs")

    ax.plot(data.index, data['Close'], label='Close', color=Colors.TEXT, linewidth=1.8)
    value_tag(ax, data.index[-1], data['Close'].iloc[-1], f"{data['Close'].iloc[-1]:,.2f}", Colors.TEXT)

    ema_colors = moving_average_colors(len(periods))
    for period, color in zip(periods, ema_colors):
        column = f'{period}-day EMA'
        ax.plot(data.index, data[column], label=column, color=color, linestyle='--', linewidth=1.3)
        value_tag(ax, data.index[-1], data[column].iloc[-1], f"{data[column].iloc[-1]:,.2f}", color)

    ax.set_title(f"{ticker.upper()}  Exponential Moving Averages")
    ax.set_xlabel("Date")
    ax.set_ylabel("Price (USD)")
    ax.margins(x=0.01)
    style_legend(ax, loc='upper left')

    fig.autofmt_xdate(rotation=30)
    fig.tight_layout()
    plt.show()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        ticker_input = input("Enter a valid stock ticker symbol: ")
    else:
        ticker_input = sys.argv[1]

    plot_ema(ticker_input)
