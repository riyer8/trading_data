import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd

from ui.theme import Colors, Fonts, apply_chart_theme, style_legend, value_tag, set_window_title


def calculate_vwap(data):
    vwap = (data['Close'] * data['Volume']).cumsum() / data['Volume'].cumsum()
    return vwap


def plot_vwap(ticker, period='1y', interval='1d'):
    data = yf.download(ticker, period=period, interval=interval)

    # Recent yfinance returns MultiIndex columns (field, ticker); flatten to a single level.
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    if data.empty:
        print(f"No data found for ticker symbol: {ticker}")
        return

    data['VWAP'] = calculate_vwap(data)

    apply_chart_theme()
    fig, ax = plt.subplots(figsize=(11, 6))
    set_window_title(fig, f"{ticker.upper()} · VWAP")

    ax.plot(data.index, data['Close'], label='Close', color=Colors.TEXT, linewidth=1.6)
    ax.plot(data.index, data['VWAP'], label='VWAP', color=Colors.ACCENT_2, linewidth=2.0)

    ax.fill_between(data.index, data['Close'], data['VWAP'], where=(data['Close'] > data['VWAP']),
                    color=Colors.BULL, alpha=0.25, interpolate=True, label='Above VWAP (Bullish)')
    ax.fill_between(data.index, data['Close'], data['VWAP'], where=(data['Close'] < data['VWAP']),
                    color=Colors.BEAR, alpha=0.25, interpolate=True, label='Below VWAP (Bearish)')

    ax.set_title(f'{ticker.upper()}  Price vs VWAP')
    ax.set_xlabel('Date')
    ax.set_ylabel('Price (USD)')
    ax.margins(x=0.01)

    last_price = data['Close'].iloc[-1]
    last_vwap = data['VWAP'].iloc[-1]
    sentiment_color = Colors.BULL if last_price >= last_vwap else Colors.BEAR
    value_tag(ax, data.index[-1], last_price, f'{last_price:,.2f}', sentiment_color)
    value_tag(ax, data.index[-1], last_vwap, f'{last_vwap:,.2f}', Colors.ACCENT_2)

    sentiment = "BULLISH" if last_price > last_vwap else "BEARISH" if last_price < last_vwap else "NEUTRAL"
    ax.text(0.01, 0.97, f'{sentiment}', transform=ax.transAxes, ha='left', va='top',
            fontsize=Fonts.SUBTITLE, fontweight='bold', color=sentiment_color,
            bbox=dict(boxstyle='round,pad=0.4', facecolor=Colors.HEADER, edgecolor=Colors.GRID))

    style_legend(ax, loc='lower left')
    fig.tight_layout()
    plt.show()

    latest_data = data.tail(5)[['Close', 'VWAP']]
    print("\nLatest 5 Closing Prices and VWAP Values:")
    print(latest_data)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        ticker_input = input("Enter a valid stock ticker symbol: ").strip()
    else:
        ticker_input = sys.argv[1]

    plot_vwap(ticker_input)
