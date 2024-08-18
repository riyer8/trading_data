import yfinance as yf
import tkinter as tk
from tkinter import ttk
import pandas as pd
import sys
import os

from portfolioInfo import ALL_TICKERS

def get_sp500_tickers():
    filtered_tickers = set(ALL_TICKERS)

    print(f"Total Tickers: {len(ALL_TICKERS)}")
    print(f"Total Filtered Tickers: {len(filtered_tickers)}")

    return sorted(filtered_tickers)

def calculate_percentage_change(data):
    if len(data) < 2:
        return None
    
    yesterday_close = data['Close'].iloc[-2]
    today_close = data['Close'].iloc[-1]
    percentage_change = ((today_close - yesterday_close) / yesterday_close) * 100

    if today_close < yesterday_close:
        percentage_change = -abs(percentage_change)

    data['Pct Change'] = data['Close'].pct_change() * 100
    
    return percentage_change

def calculate_standard_deviation(data):
    if 'Pct Change' in data:
        return data['Pct Change'].std()
    return None

def calculate_volume_change(data):
    if len(data) < 2:
        return None
    
    yesterday_volume = data['Volume'].iloc[-2]
    today_volume = data['Volume'].iloc[-1]
    volume_change = ((today_volume - yesterday_volume) / yesterday_volume) * 100

    return volume_change

def calculate_metrics(ticker):
    try:
        original_stdout = sys.stdout
        with open(os.devnull, 'w') as fnull:
            sys.stdout = fnull
            data = yf.download(ticker, period="5d", interval="1d")
            sys.stdout = original_stdout

        if len(data) < 2:
            return None, None, None, None, None

        percentage_change = calculate_percentage_change(data)
        std_dev = calculate_standard_deviation(data)
        volume_change = calculate_volume_change(data)

        last_price = data['Close'].iloc[-1]
        volume = data['Volume'].iloc[-1]
        
        return last_price, percentage_change, std_dev, volume, volume_change

    except Exception as e:
        print(f"Error processing {ticker}: {e}")
        return None, None, None, None, None

def get_company_info(ticker):
    try:
        ticker_obj = yf.Ticker(ticker)
        company_name = ticker_obj.info.get('longName', 'N/A')
        sector = ticker_obj.info.get('sector', 'N/A')
        return company_name, sector

    except Exception as e:
        print(f"Error retrieving info for {ticker}: {e}")
        return 'N/A', 'N/A'

def get_top_moving_tickers(progress_callback=None):
    tickers = get_sp500_tickers()
    metrics = []

    total = len(tickers)
    for idx, ticker in enumerate(tickers):
        last_price, percentage_change, std_dev, volume, volume_change = calculate_metrics(ticker)
        if last_price is not None and percentage_change is not None and std_dev is not None:
            
            # Filtered out any tickers with prices less than $10
            if last_price >= 10:
                company_name, sector = get_company_info(ticker)
                metrics.append((ticker, company_name, sector, last_price, percentage_change, std_dev, volume, volume_change))

        if progress_callback:
            progress_callback(idx + 1, total)

    metrics.sort(key=lambda x: x[4], reverse=True)
    return metrics

def format_volume(volume):
    if volume >= 1e6:
        return f"{volume / 1e6:.2f}M"

    elif volume >= 1e3:
        return f"{volume / 1e3:.2f}K"

    else:
        return f"{volume:.2f}"

def convert_volume_to_numeric(volume_str):
    if volume_str.endswith('M'):
        return float(volume_str[:-1]) * 1e6

    elif volume_str.endswith('K'):
        return float(volume_str[:-1]) * 1e3

    else:
        return float(volume_str)

def sort_treeview_column(treeview, column, reverse):
    column_indices = {"Ticker": 0, "Company Name": 1, "Sector": 2, "Last Price": 3, "Percentage Change": 4, "Standard Deviation": 5, "Volume": 6, "Volume Change": 7}
    col_index = column_indices[column]

    items = [(treeview.item(child)['values'], child) for child in treeview.get_children()]

    if column in ["Last Price", "Percentage Change", "Standard Deviation", "Volume", "Volume Change"]:
        if column == "Volume":
            items.sort(key=lambda x: convert_volume_to_numeric(x[0][col_index]), reverse=reverse)
        else:
            items.sort(key=lambda x: float(x[0][col_index]), reverse=reverse)
    else:
        items.sort(key=lambda x: x[0][col_index], reverse=reverse)

    treeview.delete(*treeview.get_children())

    for index, (values, item) in enumerate(items):
        percent_change = float(values[4])

        if percent_change > 0:
            tag = "positive"
        else:
            tag = "negative"
        
        treeview.insert("", tk.END, iid=item, values=values, tags=(tag,))

    for col in column_indices:
        treeview.heading(col, text=col)

    if reverse:
        arrow = "↓"
    else:
        arrow = "↑"
    
    treeview.heading(column, text=f"{column} {arrow}", command=lambda: sort_treeview_column(treeview, column, not reverse))

def show_top_tickers():
    def update_progress(current, total):
        progress_var.set((current / total) * 100)
        root.update_idletasks()

    # Progress bar pop-up information
    root = tk.Tk()
    root.title("Top Moving Tickers")
    frame = tk.Frame(root)
    frame.pack(padx=10, pady=10)

    progress_var = tk.DoubleVar()
    progress_bar = ttk.Progressbar(frame, variable=progress_var, maximum=100, length=400)
    progress_bar.pack(pady=10)

    # Creating main frame and information
    top_moving_tickers = get_top_moving_tickers(progress_callback=update_progress)
    frame.destroy()
    columns = ("Ticker", "Company Name", "Sector", "Last Price", "Percentage Change", "Standard Deviation", "Volume", "Volume Change")
    tree = ttk.Treeview(root, columns=columns, show='headings')

    # Custom widths, adjust as needed
    column_widths = {
        "Ticker": 50, "Company Name": 100, "Sector": 60, "Last Price": 70,
        "Percentage Change": 120, "Standard Deviation": 120, "Volume": 90, "Volume Change": 120
    }
    for col in columns:
        tree.heading(col, text=col, command=lambda col=col: sort_treeview_column(tree, col, False))
        tree.column(col, width=column_widths[col])

    tree.tag_configure("positive", foreground="green")
    tree.tag_configure("negative", foreground="red")

    for ticker, company_name, sector, last_price, percentage_change, std_dev, volume, volume_change in top_moving_tickers:
        if percentage_change > 0:
            tag = "positive"
        else:
            tag = "negative"

        tree.insert("", tk.END, values=(ticker, company_name, sector, f"{last_price:.2f}", f"{percentage_change:.2f}", f"{std_dev:.2f}", format_volume(volume), f"{volume_change:.2f}"), tags=(tag,))

    tree.pack(expand=True, fill=tk.BOTH)
    root.update_idletasks()
    root.mainloop()

if __name__ == "__main__":
    show_top_tickers()
