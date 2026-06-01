import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
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
        percentage_change = calculate_percentage_change(data)
        metrics.append((ticker, percentage_change))

    return sorted(metrics, key=lambda x: x[1], reverse=True)

def heat_map(tickers_data):
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

    norm = mcolors.TwoSlopeNorm(vmin=min(percentages), vcenter=0, vmax=max(percentages))

    apply_chart_theme()
    fig, ax = plt.subplots(figsize=(7.5, 7.5))
    set_window_title(fig, "Market Heat Map")
    ax.grid(False)
    cax = ax.matshow(data, cmap=cmap, norm=norm)

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