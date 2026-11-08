from __future__ import annotations

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ui.bootstrap  # noqa: F401

from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import datacache
from ui.chart_nav import ChartNavigator, format_price, place_heading
from ui.data_utils import flatten_columns
from ui.theme import Colors, apply_chart_theme, set_window_title


def calculate_rsi(close, period=14):
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(window=period).mean()
    loss = (-delta.clip(upper=0)).rolling(window=period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def _rsi_word(value) -> tuple[str, str]:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "not enough history yet", Colors.MUTED
    if value >= 70:
        return "stretched high — the recent move has been mostly up", Colors.BEAR
    if value <= 30:
        return "stretched low — the recent move has been mostly down", Colors.BULL
    return "in the middle of its recent range", Colors.ACCENT_3


def plot_rsi(ticker):
    symbol = str(ticker).strip().upper()
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    data = flatten_columns(datacache.download(symbol, start=start_date, end=end_date))
    if data.empty or "Close" not in data.columns:
        print(f"No data found for ticker symbol: {symbol}")
        return None

    close = data["Close"].astype(float)
    rsi = calculate_rsi(close)
    close_values = close.to_numpy(dtype=float)
    rsi_values = rsi.to_numpy(dtype=float)
    x = np.arange(len(data))
    last_rsi = float(rsi_values[-1]) if np.isfinite(rsi_values[-1]) else None
    word, tone = _rsi_word(last_rsi)
    rsi_label = "—" if last_rsi is None else f"{last_rsi:.1f}"

    apply_chart_theme()
    fig, (ax_price, ax_rsi) = plt.subplots(
        2, 1, sharex=True, figsize=(11.5, 7.2),
        gridspec_kw={"height_ratios": [2.6, 1], "hspace": 0.06},
    )
    set_window_title(fig, f"{symbol} · RSI")
    ax_price.plot(x, close_values, color=Colors.ACCENT_4, linewidth=1.6)
    ax_price.set_ylabel("Price")
    ax_price.yaxis.set_major_formatter(plt.FuncFormatter(lambda value, _pos: format_price(value)))

    ax_rsi.plot(x, rsi_values, color=Colors.ACCENT_3, linewidth=1.5)
    ax_rsi.axhline(70, color=Colors.BEAR, linestyle="--", linewidth=0.9)
    ax_rsi.axhline(30, color=Colors.BULL, linestyle="--", linewidth=0.9)
    ax_rsi.axhspan(70, 100, color=Colors.BEAR, alpha=0.10)
    ax_rsi.axhspan(0, 30, color=Colors.BULL, alpha=0.10)
    ax_rsi.text(0.985, 0.86, "stretched high", transform=ax_rsi.transAxes, ha="right", va="top", color=Colors.BEAR, fontsize=9)
    ax_rsi.text(0.985, 0.14, "stretched low", transform=ax_rsi.transAxes, ha="right", va="bottom", color=Colors.BULL, fontsize=9)
    ax_rsi.set_ylabel("RSI")
    ax_rsi.set_yticks([0, 30, 50, 70, 100])

    def describe(index: int) -> str:
        day = pd.Timestamp(data.index[index]).strftime("%b %d, %Y")
        reading = rsi_values[index]
        text = "—" if not np.isfinite(reading) else f"{reading:.1f}"
        meaning, _color = _rsi_word(reading if np.isfinite(reading) else None)
        return f"{day}\nClose  {format_price(close_values[index])}\nRSI    {text}\n{meaning}"

    place_heading(
        fig,
        f"{symbol}    RSI {rsi_label}",
        f"RSI compares the size of up days and down days. Right now it is {word}.",
        hint=ChartNavigator.HINT,
        title_color=tone,
    )
    ChartNavigator(
        fig,
        [ax_price, ax_rsi],
        data.index,
        {
            ax_price: {"arrays": [close_values]},
            ax_rsi: {"lock": (0, 100)},
        },
        describe,
    ).attach()
    plt.show()
    return fig


if __name__ == "__main__":
    if len(sys.argv) < 2:
        ticker_input = input("Enter a valid stock ticker symbol: ")
    else:
        ticker_input = sys.argv[1]
    plot_rsi(ticker_input)
