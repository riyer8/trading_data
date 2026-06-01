import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yfinance as yf
import mplfinance as mpf
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.widgets import RectangleSelector

from ui.theme import Colors, candlestick_style, moving_average_colors, style_legend, set_window_title

def fetch_stock_history(ticker):
    stock = yf.Ticker(ticker)
    return stock.history(period="max")

def filter_data_by_lookback(stock_history, lookback_months):
    end_date = datetime.today().date()
    start_date = end_date - pd.DateOffset(months=lookback_months)
    
    if stock_history.index.tz is not None:
        stock_history.index = stock_history.index.tz_localize(None)
    
    return stock_history[start_date:end_date]

def calculate_moving_averages(data, windows):
    colors = moving_average_colors(len(windows))
    return [
        mpf.make_addplot(
            data['Close'].rolling(window=ma, min_periods=1).mean(),
            panel=0, color=color, width=1.2,
        )
        for ma, color in zip(windows, colors)
    ]

def calculate_bollinger_bands(data, window=20, std_dev=2):
    rolling_mean = data['Close'].rolling(window=window, min_periods=1).mean()
    rolling_std = data['Close'].rolling(window=window, min_periods=1).std()
    
    bollinger_upper = rolling_mean + (rolling_std * std_dev)
    bollinger_lower = rolling_mean - (rolling_std * std_dev)
    
    return bollinger_upper.bfill(), bollinger_lower.bfill()

def plot_candlestick_chart(ticker, data, lookback_months, moving_averages, bollinger_upper, bollinger_lower):
    fig, ax = mpf.plot(
        data,
        type='candle',
        style=candlestick_style(),
        title=f'\n{ticker.upper()}  ·  Candlestick  ·  Last {lookback_months} Months',
        ylabel='Price (USD)',
        addplot=moving_averages,
        figratio=(12, 8),
        figscale=1,
        tight_layout=True,
        show_nontrading=True,
        returnfig=True,
        warn_too_much_data=len(data) + 1000
    )

    set_window_title(fig, f"{ticker.upper()} · Candlestick")
    ax[0].fill_between(data.index, bollinger_lower, bollinger_upper,
                       color=Colors.ACCENT, alpha=0.12, label='Bollinger Bands (20, 2σ)')
    ax[0].plot(data.index, bollinger_upper, color=Colors.ACCENT, alpha=0.4, linewidth=0.8)
    ax[0].plot(data.index, bollinger_lower, color=Colors.ACCENT, alpha=0.4, linewidth=0.8)
    return fig, ax

def setup_zooming(ax, fig):
    original_xlim = ax[0].get_xlim()

    def hide_selection():
        # Hide the selection box/handles so they don't linger in the new view.
        rectangle_selector.set_visible(False)
        rectangle_selector.update()
        fig.canvas.draw_idle()

    def on_select(eclick, erelease):
        start, end = eclick.xdata, erelease.xdata
        if start is None or end is None:
            return
        # A single click reports a near-zero pixel span. matplotlib still fires
        # onselect once a selection exists, so ignore it here; otherwise we'd
        # set equal x-limits and jump to a garbage zoomed-out view.
        if abs(erelease.x - eclick.x) < 5:
            return
        ax[0].set_xlim(sorted([start, end]))
        hide_selection()

    def on_double_click(event):
        if event.dblclick:
            ax[0].set_xlim(original_xlim)
            hide_selection()

    rectangle_selector = RectangleSelector(
        ax[0],
        on_select,
        useblit=True,
        button=[1],
        minspanx=5, minspany=5,
        spancoords='pixels',
        interactive=False,
        props=dict(edgecolor=Colors.SELECTION, linestyle='-', linewidth=1.5,
                   facecolor=Colors.SELECTION, alpha=0.2, fill=True),
    )

    fig.canvas.mpl_connect('button_press_event', on_double_click)
    return rectangle_selector

def main(ticker, lookback_months):
    stock_history = fetch_stock_history(ticker)
    filtered_data = filter_data_by_lookback(stock_history, int(lookback_months))
    moving_averages = calculate_moving_averages(filtered_data, [20, 50])
    bollinger_upper, bollinger_lower = calculate_bollinger_bands(filtered_data)

    fig, ax = plot_candlestick_chart(ticker, filtered_data, lookback_months, moving_averages, bollinger_upper, bollinger_lower)
    selector = setup_zooming(ax, fig)

    plt.tight_layout()
    fig.subplots_adjust(left=0.08, right=0.92, top=0.9, bottom=0.1)
    ax[0].yaxis.set_ticks_position('left')
    ax[0].yaxis.set_label_position('left')
    plt.show()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        ticker_symbol = input("Enter the stock ticker symbol (e.g., AAPL): ").strip()
        lookback_time = input("Enter the lookback period in months: ").strip()
    else:
        ticker_symbol = sys.argv[1]
        lookback_time = sys.argv[2]
    
    if not lookback_time.isdigit():
        print("Lookback period must be a valid number.")
    else:
        main(ticker_symbol, lookback_time)