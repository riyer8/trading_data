from __future__ import annotations

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ui.bootstrap  # noqa: F401

from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import numpy as np

import datacache
from ui.chart_nav import ChartNavigator, format_price, place_heading
from ui.data_utils import flatten_columns
from ui.theme import Colors, apply_chart_theme, moving_average_colors, set_window_title, style_legend


def calculate_ema(close, period):
    return close.ewm(span=period, adjust=False).mean()


def plot_ema(ticker):
    symbol = str(ticker).strip().upper()
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    data = flatten_columns(datacache.download(symbol, start=start_date, end=end_date))
    if data.empty or "Close" not in data.columns:
        print(f"No data found for ticker symbol: {symbol}")
        return None

    close = data["Close"].astype(float)
    periods = [20, 50, 200]
    averages = {period: calculate_ema(close, period) for period in periods}
    close_values = close.to_numpy(dtype=float)
    x = np.arange(len(data))

    apply_chart_theme()
    fig, ax = plt.subplots(figsize=(11.5, 6.4))
    set_window_title(fig, f"{symbol} · Averages")
    ax.plot(x, close_values, label="Close", color=Colors.TEXT, linewidth=1.7, zorder=3)
    colors = moving_average_colors(len(periods))
    labels = {
        20: "20-day average (short trend)",
        50: "50-day average",
        200: "200-day average (long trend)",
    }
    plotted = [close_values]
    for period, color in zip(periods, colors):
        values = averages[period].to_numpy(dtype=float)
        plotted.append(values)
        ax.plot(x, values, label=labels[period], color=color, linewidth=1.35, zorder=2)

    last = float(close_values[-1])
    long_average = float(averages[200].iloc[-1])
    tone = Colors.BULL if last >= long_average else Colors.BEAR
    relation = "above" if last >= long_average else "below"
    ax.set_ylabel("Price")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda value, _pos: format_price(value)))
    style_legend(ax, loc="lower left")

    def describe(index: int) -> str:
        day = data.index[index]
        lines = [pd_stamp(day), f"Close  {format_price(close_values[index])}"]
        for period in periods:
            lines.append(f"{period:>3}-day {format_price(averages[period].iloc[index])}")
        return "\n".join(lines)

    place_heading(
        fig,
        f"{symbol}    {format_price(last)}",
        f"Price is {relation} the 200-day average, so the long trend is {'up' if last >= long_average else 'down'}. Shorter lines react faster.",
        hint=ChartNavigator.HINT,
        title_color=tone,
    )
    ChartNavigator(
        fig, [ax], data.index,
        {ax: {"arrays": plotted}},
        describe,
    ).attach()
    plt.show()
    return fig


def pd_stamp(value) -> str:
    import pandas as pd
    return pd.Timestamp(value).strftime("%b %d, %Y")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        ticker_input = input("Enter a valid stock ticker symbol: ")
    else:
        ticker_input = sys.argv[1]
    plot_ema(ticker_input)
