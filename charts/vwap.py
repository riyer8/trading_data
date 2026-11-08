from __future__ import annotations

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ui.bootstrap  # noqa: F401

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import datacache
from ui.chart_nav import ChartNavigator, format_price, place_heading
from ui.data_utils import flatten_columns
from ui.theme import Colors, apply_chart_theme, set_window_title, style_legend

VWAP_DAYS = 20


def rolling_vwap(data, window=VWAP_DAYS):
    typical = (data["High"] + data["Low"] + data["Close"]) / 3
    volume = data["Volume"].astype(float).replace(0, np.nan)
    traded = typical * volume
    return traded.rolling(window, min_periods=window).sum() / volume.rolling(window, min_periods=window).sum()


def plot_vwap(ticker, period="1y", interval="1d"):
    symbol = str(ticker).strip().upper()
    data = flatten_columns(datacache.download(symbol, period=period, interval=interval))
    needed = {"Close", "High", "Low", "Volume"}
    if data.empty or not needed.issubset(data.columns):
        print(f"No data found for ticker symbol: {symbol}")
        return None

    vwap = rolling_vwap(data)
    close_values = data["Close"].to_numpy(dtype=float)
    vwap_values = vwap.to_numpy(dtype=float)
    x = np.arange(len(data))
    last = float(close_values[-1])
    last_vwap = float(vwap_values[-1]) if np.isfinite(vwap_values[-1]) else None
    if last_vwap is None:
        relation = "not ready yet"
        tone = Colors.MUTED
    elif last >= last_vwap:
        relation = "above"
        tone = Colors.BULL
    else:
        relation = "below"
        tone = Colors.BEAR

    apply_chart_theme()
    fig, ax = plt.subplots(figsize=(11.5, 6.4))
    set_window_title(fig, f"{symbol} · VWAP")
    ax.plot(x, close_values, label="Close", color=Colors.TEXT, linewidth=1.6, zorder=3)
    ax.plot(x, vwap_values, label=f"{VWAP_DAYS}-day VWAP", color=Colors.ACCENT_2, linewidth=2.0, zorder=3)
    above = np.isfinite(vwap_values) & (close_values >= vwap_values)
    below = np.isfinite(vwap_values) & (close_values < vwap_values)
    ax.fill_between(x, close_values, vwap_values, where=above, color=Colors.BULL, alpha=0.22, interpolate=True, label="Close above VWAP")
    ax.fill_between(x, close_values, vwap_values, where=below, color=Colors.BEAR, alpha=0.22, interpolate=True, label="Close below VWAP")
    ax.set_ylabel("Price")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda value, _pos: format_price(value)))
    style_legend(ax, loc="lower left")

    def describe(index: int) -> str:
        day = pd.Timestamp(data.index[index]).strftime("%b %d, %Y")
        price = close_values[index]
        anchor = vwap_values[index]
        if not np.isfinite(anchor):
            side = "VWAP needs 20 days"
        elif price >= anchor:
            side = "Close is above VWAP"
        else:
            side = "Close is below VWAP"
        anchor_text = "—" if not np.isfinite(anchor) else format_price(anchor)
        return f"{day}\nClose  {format_price(price)}\nVWAP   {anchor_text}\n{side}"

    if last_vwap is None:
        note = "VWAP is the average price people actually traded, weighted by volume. It appears after 20 days."
    else:
        note = (
            f"Close is {relation} the {VWAP_DAYS}-day volume-weighted average. "
            "Green means buyers paid up relative to that average."
        )
    place_heading(
        fig,
        f"{symbol}    {format_price(last)}",
        note,
        hint=ChartNavigator.HINT,
        title_color=tone,
    )
    ChartNavigator(
        fig, [ax], data.index,
        {ax: {"arrays": [close_values, vwap_values]}},
        describe,
    ).attach()
    plt.show()
    return fig


if __name__ == "__main__":
    if len(sys.argv) < 2:
        ticker_input = input("Enter a valid stock ticker symbol: ").strip()
    else:
        ticker_input = sys.argv[1]
    plot_vwap(ticker_input)
