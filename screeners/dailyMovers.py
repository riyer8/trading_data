import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from tkinter import ttk
import pandas as pd
import time
import datacache
from portfolio.portfolioInfo import MY_TICKERS, ALL_TICKERS
from charts.stockChart import main as plot_stock_chart
from ui.theme import Colors, style_table, apply_row_stripes
import matplotlib.pyplot as plt
import numpy as np
import requests
import json

def all_tickers():
    print(f"Total Number of Tickers: {len(MY_TICKERS)}")
    return sorted(set(MY_TICKERS))

def company_info(ticker):
    try:
        info = datacache.ticker_info(ticker)
        company_name = info.get('longName', 'N/A')
        sector = info.get('sector', 'N/A')
        return company_name, sector
    except (json.decoder.JSONDecodeError, requests.exceptions.RequestException) as e:
        print(f"Error fetching data for {ticker}: {e}")
        time.sleep(3)
        return 'N/A', 'N/A'

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
    retries = 3
    for attempt in range(retries):
        try:
            data = datacache.download(ticker, period="5d", interval="1d")
            # Recent yfinance returns MultiIndex columns (field, ticker); flatten
            # so data['Close'].iloc[-1] is a scalar instead of a Series.
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)
            if not data.empty:
                last_price = data['Close'].iloc[-1]
                percentage_change = calculate_percentage_change(data)
                std_change = calculate_standard_deviation(data)
                last_volume = data['Volume'].iloc[-1]
                volume_change = calculate_volume_change(data)
                return last_price, percentage_change, std_change, last_volume, volume_change, data
            else:
                print(f"No data returned for {ticker}.")
                return None, None, None, None, None, None
        except Exception as e:
            print(f"Attempt {attempt+1} failed for {ticker}: {e}")
            time.sleep(5 * (2 ** attempt))
    return None, None, None, None, None, None

def filter_tickers():
    tickers = all_tickers()
    data = []

    for ticker in tickers:
        last_price, percentage_change, std_dev, volume, volume_change, stock_data = collect_data(ticker)
        # Keep any ticker that returned a usable price >= $10. The previous
        # check (type(last_price) == int) was always False since prices are
        # floats, so the table came back empty.
        if last_price is not None and float(last_price) >= 10:
            company_name, sector = company_info(ticker)
            data.append((ticker, company_name, sector, last_price, percentage_change, std_dev, volume, volume_change, stock_data))

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
    apply_row_stripes(treeview)

_chart_opening = False

def on_ticker_double_click(event, tree):
    # plt.show() spins matplotlib's own Tk event loop, which can dispatch a
    # second buffered double-click and re-enter this handler -> two charts.
    # Guard against re-entry while a chart is already opening.
    global _chart_opening
    if _chart_opening:
        return

    row_id = tree.identify_row(event.y)
    if not row_id:
        return

    ticker = tree.item(row_id, 'values')[0]
    _chart_opening = True
    try:
        plot_stock_chart(ticker, 6)
    finally:
        _chart_opening = False

def display_tickers():
    root = tk.Tk()
    root.title("Top Moving Tickers")
    style_table(root)

    frame = tk.Frame(root, bg=Colors.BACKGROUND)
    frame.pack(padx=12, pady=12, fill=tk.BOTH, expand=True)

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

    tree.bind("<Double-1>", lambda event: on_ticker_double_click(event, tree))

    for ticker, company_name, sector, last_price, percentage_change, std_dev, volume, volume_change, _ in top_moving_tickers:
        tag = "positive" if percentage_change > 0 else "negative"
        tree.insert("", tk.END, values=(ticker, company_name, sector, f"{last_price:.2f}", f"{percentage_change:.2f}", f"{std_dev:.2f}", volume_to_string(volume), f"{volume_change:.2f}"), tags=(tag,))

    apply_row_stripes(tree)
    tree.pack(expand=True, fill=tk.BOTH)

    root.mainloop()

if __name__ == "__main__":
    display_tickers()