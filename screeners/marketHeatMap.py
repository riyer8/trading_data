import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import datacache
from portfolio.portfolioInfo import MY_TICKERS
from ui.theme import Colors, Fonts, apply_chart_theme, set_window_title

def all_tickers():
    return sorted(set(MY_TICKERS))

def calculate_percentage_change(data):
    last_close = data['Close'].iloc[-2]
    today_close = data['Close'].iloc[-1]
    return ((today_close - last_close) / last_close) * 100

def top_moving_tickers():
    tickers = all_tickers()
    metrics = []

    for ticker in tickers:
        data = datacache.download(ticker, period="5d", interval="1d")

        # Recent yfinance returns MultiIndex columns (field, ticker); flatten so
        # data['Close'].iloc[-1] is a scalar rather than a Series (otherwise
        # percentage_change is a Series and sorting the tuples below fails).
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        # Need at least two closes to compute a day-over-day change.
        if data.empty or len(data['Close'].dropna()) < 2:
            print(f"Skipping {ticker}: not enough data.")
            continue

        percentage_change = float(calculate_percentage_change(data))
        metrics.append((ticker, percentage_change))

    return sorted(metrics, key=lambda x: x[1], reverse=True)

def _heatmap_norm(values):
    """Build a TwoSlopeNorm that won't collapse when all values are equal."""
    vmin = min(values)
    vmax = max(values)
    if vmin == vmax:
        pad = max(abs(vmin), 1.0) * 0.1
        vmin -= pad
        vmax += pad
    # TwoSlopeNorm requires vcenter to sit strictly between vmin and vmax.
    if not (vmin < 0 < vmax):
        if vmax <= 0:
            vmax = 0.01
        if vmin >= 0:
            vmin = -0.01
    return mcolors.TwoSlopeNorm(vmin=vmin, vcenter=0, vmax=vmax)

def heat_map(tickers_data):
    if not tickers_data:
        print("No ticker data available for heat map.")
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

    apply_chart_theme()
    fig, ax = plt.subplots(figsize=(7.5, 7.5))
    set_window_title(fig, "Market Heat Map")
    ax.grid(False)
    cax = ax.matshow(np.ma.masked_invalid(data), cmap=cmap, norm=norm)
    # Status-bar hover on matshow can crash in matplotlib 3.x when the
    # colormap range is degenerate (log10(inf)). Values are already labeled
    # on each cell, so disable the cursor formatter.
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
    ax.set_title('Portfolio Heat Map  ·  Daily % Change', pad=16)

    fig.tight_layout()
    plt.show()

if __name__ == "__main__":
    heat_map(top_moving_tickers())