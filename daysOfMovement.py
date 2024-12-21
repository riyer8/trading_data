import tkinter as tk
from tksheet import Sheet
import yfinance as yf
import time
import numpy as np

def fetch_ticker_data_with_retry(ticker, retries=5, delay=2):
    for attempt in range(retries):
        try:
            ticker_obj = yf.Ticker(ticker)
            history = ticker_obj.history(period="1y")
            info = ticker_obj.info
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

def sort_sheet_column(sheet, col_index):
    data = sheet.get_data()
    if col_index == 0:
        data.sort(key=lambda x: x[0])
    else:
        for i in range(len(data)):
            row_to_sort = data[i][1:]
            sorted_values = sorted(row_to_sort, key=lambda x: float(x.strip('%')))
            data[i][1:] = sorted_values
    sheet.set_data(data)

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

    sheet.enable_bindings(("single_select", "column_select", "row_select",
                           "row_height_resize", "double_click_column_resize",
                           "right_click_popup_menu", "copy"))

    for i, row in enumerate(data_matrix):
        for j, cell in enumerate(row[1:], start=1):
            try:
                cell_value = float(cell.strip('%'))
                color = "#c8e6c9" if cell_value >= 0 else "#ffcdd2"
                sheet.highlight_cells(row=i, column=j, bg=color, fg="black")
            except ValueError:
                continue

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