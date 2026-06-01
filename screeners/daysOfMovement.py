import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from tksheet import Sheet
import datacache
import time
import numpy as np
from screeners.correlation import filter_tickers
from ui.theme import Colors, style_sheet

def fetch_ticker_data_with_retry(ticker, retries=5, delay=2):
    for attempt in range(retries):
        try:
            history = datacache.ticker_history(ticker, period="1y")
            info = datacache.ticker_info(ticker)
            return history, info
        except Exception as e:
            print(f"Attempt {attempt + 1} failed for {ticker}: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
                delay *= 2
            else:
                print(f"Failed to fetch data for {ticker} after {retries} attempts.")
                return None, None

def ticker_data(ticker):
    """Wrapper to fetch ticker data."""
    history, info = fetch_ticker_data_with_retry(ticker)
    if history is None or info is None:
        raise ValueError(f"Could not fetch data for ticker {ticker}")
    return history, info

def calculate_percentage_change(data):
    close_prices = data['Close'].to_numpy()
    percentage_changes = np.diff(close_prices) / close_prices[:-1] * 100
    return percentage_changes

def days_percentage_changes(ticker):
    try:
        hist, _ = ticker_data(ticker)
        last_15_days = hist.tail(16)
        return calculate_percentage_change(last_15_days)[-15:]
    except Exception as e:
        print(f"Error calculating percentage changes for {ticker}: {e}")
        return [0] * 15

def apply_change_highlights(sheet):
    """Color each % cell green/red based on its sign (re-applied after sorting)."""
    sheet.dehighlight_all()
    for i, row in enumerate(sheet.get_sheet_data()):
        for j, cell in enumerate(row[1:], start=1):
            try:
                cell_value = float(str(cell).strip('%'))
            except ValueError:
                continue
            bg = Colors.BULL_FILL if cell_value >= 0 else Colors.BEAR_FILL
            fg = Colors.BULL if cell_value >= 0 else Colors.BEAR
            sheet.highlight_cells(row=i, column=j, bg=bg, fg=fg)

def sort_sheet_column(sheet, col_index):
    if col_index is None:
        return

    # get_sheet_data()/set_sheet_data() operate on the whole grid. (get_data()/
    # set_data() are span-based in tksheet 7.x and error without a span.)
    data = sheet.get_sheet_data()
    if not data:
        return

    if col_index == 0:
        data.sort(key=lambda row: str(row[0]))
    else:
        def sort_key(row):
            try:
                return float(str(row[col_index]).strip('%'))
            except (ValueError, IndexError):
                return float('-inf')
        # Biggest movers first for the clicked day.
        data.sort(key=sort_key, reverse=True)

    sheet.set_sheet_data(data, reset_col_positions=False, reset_row_positions=False)
    apply_change_highlights(sheet)

def get_clicked_column_index(event, sheet):
    x = event.x
    total_width = 0
    for col_index, col_width in enumerate(sheet.get_column_widths()):
        total_width += col_width
        if x <= total_width:
            return col_index
    return None

def display_percentage_changes(ticker):
    root = tk.Tk()
    root.title(f"Percentage Changes for {ticker} and Correlated Tickers")
    root.configure(bg=Colors.BACKGROUND)

    correlated_tickers = []
    try:
        correlated_tickers = [t for t in filter_tickers(ticker, 0) if t[0] != ticker][:5]
    except Exception as e:
        print(f"Error fetching correlated tickers for {ticker}: {e}")

    tickers_to_display = [ticker] + [t[0] for t in correlated_tickers]

    headers = ["Ticker"] + [f"Day {i}" for i in range(1, 16)]
    data_matrix = []

    for current_ticker in tickers_to_display:
        percentage_changes = days_percentage_changes(current_ticker)
        formatted_changes = [f"{change:.2f}%" for change in percentage_changes]
        data_matrix.append([current_ticker] + formatted_changes)

    sheet = Sheet(root,
                  data=data_matrix,
                  headers=headers,
                  width=1000,
                  height=175)
    style_sheet(sheet)

    sheet.enable_bindings(("single_select", "column_select", "row_select",
                           "row_height_resize", "double_click_column_resize",
                           "right_click_popup_menu", "copy"))

    apply_change_highlights(sheet)

    initial_width = 60
    for col_index in range(sheet.total_columns()):
        sheet.column_width(col_index, initial_width)

    sheet.bind('<Button-1>', lambda event: sort_sheet_column(sheet, get_clicked_column_index(event, sheet)))

    sheet.pack(expand=True, fill=tk.BOTH)
    root.mainloop()

if __name__ == "__main__":
    ticker_symbol = input("Enter the symbol: ").strip().upper()
    try:
        display_percentage_changes(ticker_symbol)
    except Exception as e:
        print(f"Error displaying percentage changes: {e}")