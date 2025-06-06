import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import yfinance as yf
from portfolioInfo import MY_TICKERS

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
        data = yf.download(ticker, period="5d", interval="1d")
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

    colors = [(1, 0, 0), (1, 1, 1), (0, 0, 1)]
    cmap = mcolors.LinearSegmentedColormap.from_list("RedBlue", colors, N=256)
    
    norm = mcolors.TwoSlopeNorm(vmin=min(percentages), vcenter=0, vmax=max(percentages))

    fig, ax = plt.subplots(figsize=(6, 6))
    cax = ax.matshow(data, cmap=cmap, norm=norm)

    cbar = plt.colorbar(cax)
    cbar.set_label('Percentage Change')

    for (i, j), val in np.ndenumerate(data):
        if not np.isnan(val):
            ax.text(j, i, tickers[i * size + j], ha='center', va='center', fontsize=8, 
                    color='white' if abs(val) > 3 else 'black')

    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title('Percentage Change Heat Map')
    
    plt.show()

if __name__ == "__main__":
    heat_map(top_moving_tickers())