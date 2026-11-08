from __future__ import annotations

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ui.bootstrap  # noqa: F401

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import datacache
from portfolio.portfolioInfo import MY_TICKERS
from ui.theme import Colors, Fonts, apply_chart_theme, set_window_title
from ui.data_utils import flatten_columns, safe_pct_change


def all_tickers():
    return sorted(set(MY_TICKERS))


def top_moving_tickers(progress_cb=None):
    tickers = all_tickers()
    metrics = []
    total = len(tickers)

    for index, ticker in enumerate(tickers, start=1):
        if progress_cb:
            progress_cb(index, total, ticker)

        data = datacache.download(ticker, period="5d", interval="1d")
        data = flatten_columns(data)

        if data.empty or len(data['Close'].dropna()) < 2:
            continue

        percentage_change = safe_pct_change(data['Close'].iloc[-1], data['Close'].iloc[-2])
        if percentage_change is None:
            continue
        metrics.append((ticker, float(percentage_change)))

    return sorted(metrics, key=lambda x: x[1], reverse=True)


def _heatmap_norm(values):
    vmin = min(values)
    vmax = max(values)
    if vmin == vmax:
        pad = max(abs(vmin), 1.0) * 0.1
        vmin -= pad
        vmax += pad
    if not (vmin < 0 < vmax):
        if vmax <= 0:
            vmax = 0.01
        if vmin >= 0:
            vmin = -0.01
    return mcolors.TwoSlopeNorm(vmin=vmin, vcenter=0, vmax=vmax)


def heat_map(tickers_data):
    apply_chart_theme()

    if not tickers_data:
        fig, ax = plt.subplots(figsize=(8, 4))
        set_window_title(fig, "Market Heat Map")
        ax.axis("off")
        ax.text(
            0.5, 0.5,
            "No ticker data available for heat map.\nCheck your connection or .datacache/.",
            ha="center", va="center", color=Colors.TEXT, fontsize=12,
        )
        plt.show()
        return

    tickers = [item[0] for item in tickers_data]
    percentages = [item[1] for item in tickers_data]
    num_tickers = len(tickers)
    size = int(np.ceil(np.sqrt(num_tickers)))
    data = np.full((size, size), np.nan)

    for i, percentage in enumerate(percentages):
        row, col = divmod(i, size)
        data[row, col] = percentage

    cmap = mcolors.LinearSegmentedColormap.from_list(
        "BearBull", [Colors.BEAR, Colors.PANEL, Colors.BULL], N=256
    )
    norm = _heatmap_norm(percentages)

    fig, ax = plt.subplots(figsize=(7.5, 7.5))
    set_window_title(fig, "Market Heat Map")
    ax.grid(False)
    cax = ax.matshow(np.ma.masked_invalid(data), cmap=cmap, norm=norm)
    cax.format_cursor_data = lambda _data: ''

    cbar = plt.colorbar(cax, fraction=0.046, pad=0.04)
    cbar.set_label('Daily % Change', color=Colors.MUTED)
    cbar.ax.tick_params(colors=Colors.MUTED)
    cbar.outline.set_edgecolor(Colors.GRID)

    for (i, j), val in np.ndenumerate(data):
        if not np.isnan(val):
            ax.text(j, i, f"{tickers[i * size + j]}\n{val:+.1f}%",
                    ha='center', va='center', fontsize=Fonts.TICK, fontweight='bold',
                    fontfamily='monospace', color=Colors.TEXT)

    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_title("Today's move across the watchlist", pad=18)
    fig.text(
        0.5, 0.02,
        "Green is up, red is down. A stronger color is a bigger move.",
        ha="center", color=Colors.MUTED, fontsize=Fonts.TICK,
    )

    fig.tight_layout(rect=(0, 0.04, 1, 1))
    plt.show()


if __name__ == "__main__":
    apply_chart_theme()
    loading_fig, loading_ax = plt.subplots(figsize=(7, 2.5))
    set_window_title(loading_fig, "Market Heat Map")
    loading_ax.axis("off")
    loading_ax.text(0.5, 0.5, "Loading heat map data…", ha="center", va="center", color=Colors.TEXT)
    loading_fig.canvas.draw()
    plt.show(block=False)
    plt.pause(0.05)

    print("Loading heat map data…")
    tickers_data = top_moving_tickers()
    plt.close(loading_fig)
    heat_map(tickers_data)
