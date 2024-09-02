import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import yfinance as yf
from portfolioInfo import ALL_TICKERS, MY_TICKERS

def all_tickers():
    print(f"Total tickers: {len(MY_TICKERS)}")
    return sorted(set(MY_TICKERS))

def calculate_percentage_change(data):
    last_close = data['Close'].iloc[-2]
    today_close = data['Close'].iloc[-1]
    percentage_change = ((today_close - last_close) / last_close) * 100
    return percentage_change

def top_moving_tickers():
    tickers = all_tickers()
    metrics = []
    for ticker in tickers:
        data = yf.download(ticker, period="5d", interval="1d")
        percentage_change = calculate_percentage_change(data)
        metrics.append((ticker, percentage_change))
    metrics.sort(key=lambda x: x[1], reverse=True)
    return metrics

def heat_map(tickers_data):
    tickers = [item[0] for item in tickers_data]
    percentages = [item[1] for item in tickers_data]

    num_tickers = len(tickers)
    size = int(np.ceil(np.sqrt(num_tickers)))
    data = np.full((size, size), np.nan)

    for i, percentage in enumerate(percentages):
        row, col = divmod(i, size)
        data[row, col] = percentage

    norm = mcolors.Normalize(vmin=min(percentages), vmax=max(percentages))
    cmap = plt.get_cmap('coolwarm_r')

    fig, ax = plt.subplots(figsize=(10, 10))
    cax = ax.matshow(data, cmap=cmap, norm=norm)

    cbar = plt.colorbar(cax)
    cbar.set_label('Percentage Change')

    for (i, j), val in np.ndenumerate(data):
        if not np.isnan(val):
            ax.text(j, i, tickers[i * size + j], ha='center', va='center', fontsize=6, color='white' if abs(val) > 3 else 'black')

    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title('Percentage Change Heat Map')

    plt.show()

if __name__ == "__main__":
    top_moving_tickers = top_moving_tickers()
    heat_map(top_moving_tickers)