import yfinance as yf
import mplfinance as mpf
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.widgets import RectangleSelector
import sys

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
    return [
        mpf.make_addplot(data['Close'].rolling(window=ma, min_periods=1).mean(), panel=0, color='grey')
        for ma in windows
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
        style='charles',
        title=f'{ticker.upper()} Candlestick Chart (Last {lookback_months} Months)',
        ylabel='Price (USD)',
        addplot=moving_averages,
        figratio=(12, 8),
        figscale=1,
        tight_layout=True,
        show_nontrading=True,
        returnfig=True,
        warn_too_much_data=len(data) + 1000
    )
    
    ax[0].fill_between(data.index, bollinger_lower, bollinger_upper, color='grey', alpha=0.3)
    return fig, ax

def setup_zooming(ax, fig):
    original_xlim = ax[0].get_xlim()
    rectangle_selector = None

    def on_select(eclick, erelease):
        start, end = eclick.xdata, erelease.xdata
        ax[0].set_xlim([start, end])
        plt.draw()
        remove_rectangle_selector()
        create_rectangle_selector()

    def on_double_click(event):
        if event.dblclick:
            ax[0].set_xlim(original_xlim)
            plt.draw()
            remove_rectangle_selector()
            create_rectangle_selector()

    def remove_rectangle_selector():
        nonlocal rectangle_selector
        if rectangle_selector is not None:
            rectangle_selector.disconnect_events()
            rectangle_selector = None
            for patch in ax[0].patches:
                if isinstance(patch, plt.Rectangle):
                    patch.remove()
            fig.canvas.draw()

    def create_rectangle_selector():
        nonlocal rectangle_selector
        rectangle_selector = RectangleSelector(
            ax[0], 
            on_select,
            useblit=True,
            button=[1],
            minspanx=5, minspany=5,
            spancoords='pixels',
            interactive=True
        )
        rectangle_selector.rectprops = {
            'edgecolor': 'white', 
            'linestyle': '-', 
            'linewidth': 2, 
            'facecolor': 'none'
        }
        rectangle_selector.rectprops['visible'] = True

    create_rectangle_selector()
    fig.canvas.mpl_connect('button_press_event', on_double_click)

def main(ticker, lookback_months):
    stock_history = fetch_stock_history(ticker)
    filtered_data = filter_data_by_lookback(stock_history, int(lookback_months))
    moving_averages = calculate_moving_averages(filtered_data, [20, 50])
    bollinger_upper, bollinger_lower = calculate_bollinger_bands(filtered_data)

    fig, ax = plot_candlestick_chart(ticker, filtered_data, lookback_months, moving_averages, bollinger_upper, bollinger_lower)
    setup_zooming(ax, fig)

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