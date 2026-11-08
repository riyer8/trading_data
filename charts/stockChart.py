from __future__ import annotations

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ui.bootstrap  # noqa: F401

from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import datacache
from ui.chart_nav import ChartNavigator, format_price, format_volume, place_heading
from ui.data_utils import flatten_columns
from ui.theme import Colors, apply_chart_theme, set_window_title, style_legend


def fetch_stock_history(ticker):
    data = datacache.ticker_history(ticker, period="max")
    return flatten_columns(data)


def filter_data_by_lookback(stock_history, lookback_months):
    end_date = datetime.today().date()
    start_date = end_date - pd.DateOffset(months=int(lookback_months))
    history = stock_history.copy()
    if history.index.tz is not None:
        history.index = history.index.tz_localize(None)
    return history[start_date:end_date]


def _series(frame, name):
    if name not in frame.columns:
        return None
    return frame[name].astype(float)


def build_figure(ticker, lookback_months):
    symbol = str(ticker).strip().upper()
    history = filter_data_by_lookback(fetch_stock_history(symbol), lookback_months)
    close = _series(history, "Close")
    if close is None or close.dropna().empty:
        print(f"No data for {symbol} in the last {lookback_months} months.")
        return None

    history = history.loc[close.notna()].copy()
    open_ = _series(history, "Open")
    high = _series(history, "High")
    low = _series(history, "Low")
    close = _series(history, "Close")
    if open_ is None:
        open_ = close.copy()
    if high is None:
        high = np.maximum(open_, close)
        high = pd.Series(high, index=history.index)
    if low is None:
        low = np.minimum(open_, close)
        low = pd.Series(low, index=history.index)
    volume = _series(history, "Volume")

    close_values = close.to_numpy(dtype=float)
    open_values = open_.to_numpy(dtype=float)
    high_values = high.to_numpy(dtype=float)
    low_values = low.to_numpy(dtype=float)
    average_20 = close.rolling(20, min_periods=20).mean().to_numpy(dtype=float)
    average_50 = close.rolling(50, min_periods=50).mean().to_numpy(dtype=float)
    mid = close.rolling(20, min_periods=20).mean()
    spread = close.rolling(20, min_periods=20).std()
    band_high = (mid + 2 * spread).to_numpy(dtype=float)
    band_low = (mid - 2 * spread).to_numpy(dtype=float)

    last = float(close_values[-1])
    previous = float(close_values[-2]) if len(close_values) > 1 else None
    change = ((last - previous) / previous) * 100 if previous else None
    tone = Colors.TEXT if change is None else Colors.BULL if change >= 0 else Colors.BEAR
    change_text = "" if change is None else f"   {change:+.2f}%"

    apply_chart_theme()
    fig, (ax_price, ax_volume) = plt.subplots(
        2, 1, sharex=True, figsize=(12.2, 7.4),
        gridspec_kw={"height_ratios": [3.4, 1], "hspace": 0.04},
    )
    set_window_title(fig, f"{symbol} · Chart")
    x = np.arange(len(history))
    up = close_values >= open_values
    candle_colors = np.where(up, Colors.BULL, Colors.BEAR)

    ax_price.fill_between(x, band_low, band_high, color=Colors.ACCENT, alpha=0.14, label="Usual range (20-day)", zorder=1)
    ax_price.plot(x, average_20, color=Colors.ACCENT_5, linewidth=1.3, label="20-day average", zorder=4)
    ax_price.plot(x, average_50, color=Colors.ACCENT_3, linewidth=1.3, label="50-day average", zorder=4)
    ax_price.vlines(x, low_values, high_values, colors=candle_colors, linewidth=0.8, zorder=3)
    body = np.abs(close_values - open_values)
    span = float(np.nanmax(high_values) - np.nanmin(low_values)) or 1.0
    body = np.maximum(body, span * 0.0015)
    ax_price.bar(
        x, body, bottom=np.minimum(open_values, close_values),
        width=0.62, color=candle_colors, linewidth=0, zorder=3,
    )
    ax_price.axhline(last, color=tone, linewidth=0.8, linestyle="--", alpha=0.75, zorder=2)
    ax_price.set_ylabel("Price")
    ax_price.yaxis.set_major_formatter(plt.FuncFormatter(lambda value, _pos: format_price(value)))
    style_legend(ax_price, loc="lower left")

    if volume is not None:
        volume_values = volume.fillna(0).to_numpy(dtype=float)
        ax_volume.bar(x, volume_values, width=0.62, color=candle_colors, alpha=0.85, linewidth=0)
    else:
        volume_values = np.zeros(len(x))
    ax_volume.set_ylabel("Volume")
    ax_volume.yaxis.set_major_formatter(plt.FuncFormatter(lambda value, _pos: format_volume(value)))
    ax_volume.grid(axis="x", visible=False)

    def describe(index: int) -> str:
        stamp = history.index[index]
        day = pd.Timestamp(stamp).strftime("%b %d, %Y")
        bar_close = close_values[index]
        prior = close_values[index - 1] if index else None
        move = ""
        if prior:
            move = f"   {((bar_close - prior) / prior) * 100:+.2f}%"
        return (
            f"{day}\n"
            f"Open {format_price(open_values[index])}    High {format_price(high_values[index])}\n"
            f"Low  {format_price(low_values[index])}    Close {format_price(bar_close)}{move}\n"
            f"Volume {format_volume(volume_values[index])}"
        )

    place_heading(
        fig,
        f"{symbol}    {format_price(last)}{change_text}",
        "Each bar is one trading day. Green closed higher than it opened. The band is the usual 20-day range.",
        hint=ChartNavigator.HINT,
        title_color=tone,
    )
    ChartNavigator(
        fig,
        [ax_price, ax_volume],
        history.index,
        {
            ax_price: {"arrays": [high_values, low_values, band_high, band_low, average_20, average_50]},
            ax_volume: {"arrays": [volume_values], "floor": 0},
        },
        describe,
    ).attach()
    return fig


def main(ticker, lookback_months):
    fig = build_figure(ticker, lookback_months)
    if fig is not None:
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
