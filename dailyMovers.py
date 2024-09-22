import tkinter as tk
from tkinter import ttk
import yfinance as yf
from portfolioInfo import MY_TICKERS, ALL_TICKERS
from stockChart import main as plot_stock_chart

def all_tickers():
    print(f"Total Number of Tickers: {len(MY_TICKERS)}")
    return sorted(set(MY_TICKERS))

def company_info(ticker):
    ticker = yf.Ticker(ticker)
    company_name = ticker.info.get('longName', 'N/A')
    sector = ticker.info.get('sector', 'N/A')
    return company_name, sector

def calculate_percentage_change(data):
    last_close = data['Close'].iloc[-2]
    today_close = data['Close'].iloc[-1]
    percentage_change = ((today_close - last_close) / last_close) * 100
    return percentage_change

def calculate_standard_deviation(data):
    data['Percent Change'] = data['Close'].pct_change() * 100
    return data['Percent Change'].std()

def calculate_volume_change(data):
    last_volume = data['Volume'].iloc[-2]
    today_volume = data['Volume'].iloc[-1]
    volume_change = ((today_volume - last_volume) / last_volume) * 100
    return volume_change

def volume_to_string(volume):
    if volume >= 1e6:
        return f"{volume / 1e6:.2f}M"
    elif volume >= 1e3:
        return f"{volume / 1e3:.2f}K"
    else:
        return f"{volume:.2f}"

def string_to_volume(volume_str):
    if volume_str.endswith('M'):
        return float(volume_str[:-1]) * 1e6
    elif volume_str.endswith('K'):
        return float(volume_str[:-1]) * 1e3
    else:
        return float(volume_str)

def collect_data(ticker):
    data = yf.download(ticker, period="5d", interval="1d")

    last_price = data['Close'].iloc[-1]
    percentage_change = calculate_percentage_change(data)
    std_change = calculate_standard_deviation(data)
    last_volume = data['Volume'].iloc[-1]
    volume_change = calculate_volume_change(data)
    
    return last_price, percentage_change, std_change, last_volume, volume_change

def filter_tickers():
    tickers = all_tickers()
    data = []

    for ticker in tickers:
        last_price, percentage_change, std_dev, volume, volume_change = collect_data(ticker)
        if last_price >= 10:
            company_name, sector = company_info(ticker)
            data.append((ticker, company_name, sector, last_price, percentage_change, std_dev, volume, volume_change))

    data.sort(key=lambda x: x[4], reverse=True)
    return data

def sort_tickers(treeview, column, reverse):
    column_indices = {"Ticker": 0, "Company Name": 1, "Sector": 2, "Last Price": 3, "Percentage Change": 4, "Standard Deviation": 5, "Volume": 6, "Volume Change": 7}
    col_index = column_indices[column]

    items = [(treeview.item(child)['values'], child) for child in treeview.get_children()]

    if column in ["Last Price", "Percentage Change", "Standard Deviation", "Volume", "Volume Change"]:
        if column == "Volume":
            items.sort(key=lambda x: string_to_volume(x[0][col_index]), reverse=reverse)
        else:
            items.sort(key=lambda x: float(x[0][col_index]), reverse=reverse)
    else:
        items.sort(key=lambda x: x[0][col_index], reverse=reverse)

    treeview.delete(*treeview.get_children())
    for index, (values, item) in enumerate(items):
        percent_change = float(values[4])
        tag = "positive" if percent_change > 0 else "negative"
        treeview.insert("", tk.END, iid=item, values=values, tags=(tag,))

    for col in column_indices:
        treeview.heading(col, text=col)

    arrow = "↓" if reverse else "↑"
    treeview.heading(column, text=f"{column} {arrow}", command=lambda: sort_tickers(treeview, column, not reverse))

def on_ticker_double_click(event, tree):
    item = tree.selection()[0]
    ticker = tree.item(item, 'values')[0]
    plot_stock_chart(ticker, 6)

def display_tickers():
    root = tk.Tk()
    root.title("Top Moving Tickers")

    frame = tk.Frame(root)
    frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    top_moving_tickers = filter_tickers()
    columns = ("Ticker", "Company Name", "Sector", "Last Price", "Percentage Change", "Standard Deviation", "Volume", "Volume Change")
    tree = ttk.Treeview(frame, columns=columns, show='headings')

    column_widths = {
        "Ticker": 50, "Company Name": 150, "Sector": 100, "Last Price": 70,
        "Percentage Change": 65, "Standard Deviation": 70, "Volume": 70, "Volume Change": 80
    }
    
    for col in columns:
        tree.heading(col, text=col, command=lambda col=col: sort_tickers(tree, col, False))
        tree.column(col, width=column_widths[col])

    tree.tag_configure("positive", foreground="green")
    tree.tag_configure("negative", foreground="red")

    tree.bind("<Double-1>", lambda event: on_ticker_double_click(event, tree))

    for ticker, company_name, sector, last_price, percentage_change, std_dev, volume, volume_change in top_moving_tickers:
        tag = "positive" if percentage_change > 0 else "negative"
        tree.insert("", tk.END, values=(ticker, company_name, sector, f"{last_price:.2f}", f"{percentage_change:.2f}", f"{std_dev:.2f}", volume_to_string(volume), f"{volume_change:.2f}"), tags=(tag,))

    tree.pack(expand=True, fill=tk.BOTH)
    root.mainloop()

if __name__ == "__main__":
    display_tickers()