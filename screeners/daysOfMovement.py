from __future__ import annotations

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ui.bootstrap  # noqa: F401

import tkinter as tk
from tksheet import Sheet
import datacache
import numpy as np
from screeners.correlation import filter_tickers
from ui.theme import Colors, Fonts, style_sheet
from ui.data_utils import flatten_columns
from ui.loading import build_loading_panel, run_in_background
from ui.open_ticker import pack_open_hint, open_ticker_views


def fetch_ticker_data(ticker):
    history = flatten_columns(datacache.ticker_history(ticker, period="1y"))
    info = datacache.ticker_info(ticker)
    if history.empty:
        raise ValueError(f"No history for {ticker}")
    return history, info


def calculate_percentage_change(data):
    close_prices = data['Close'].to_numpy()
    percentage_changes = np.diff(close_prices) / close_prices[:-1] * 100
    return percentage_changes


def days_percentage_changes(ticker):
    try:
        hist, _ = fetch_ticker_data(ticker)
        last_15_days = hist.tail(16)
        if len(last_15_days) < 2:
            return [0.0] * 15
        changes = calculate_percentage_change(last_15_days)
        if len(changes) < 15:
            padded = [0.0] * (15 - len(changes)) + list(changes)
            return padded[-15:]
        return list(changes[-15:])
    except Exception as e:
        print(f"Error calculating percentage changes for {ticker}: {e}")
        return [0.0] * 15


def apply_change_highlights(sheet):
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


def build_matrix(ticker):
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

    return headers, data_matrix


def display_percentage_changes(ticker):
    root = tk.Tk()
    root.title(f"Percentage Changes for {ticker} and Correlated Tickers")
    root.configure(bg=Colors.BACKGROUND)
    root.geometry("1020x260")

    shell = tk.Frame(root, bg=Colors.BACKGROUND)
    shell.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
    pack_open_hint(shell)

    status_frame, status_label, detail_label, progress = build_loading_panel(
        shell, f"Loading 15-day moves for {ticker}…"
    )

    def populate_sheet(result):
        status_frame.destroy()
        headers, data_matrix = result
        if not data_matrix:
            tk.Label(
                shell,
                text="No movement data loaded.\nCheck your connection or .datacache/.",
                bg=Colors.BACKGROUND,
                fg=Colors.ACCENT_5,
                font=(Fonts.sans_name, 12),
                justify=tk.LEFT,
            ).pack(expand=True)
            return

        sheet = Sheet(shell,
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
        sort_job = {"id": None}

        def on_click(event, sheet=sheet):
            if sort_job["id"] is not None:
                sheet.after_cancel(sort_job["id"])
            column = get_clicked_column_index(event, sheet)
            sort_job["id"] = sheet.after(250, lambda: sort_sheet_column(sheet, column))

        def on_double(event, sheet=sheet):
            if sort_job["id"] is not None:
                sheet.after_cancel(sort_job["id"])
                sort_job["id"] = None
            if sheet.identify_region(event) != "table":
                return
            row = sheet.identify_row(event)
            data = sheet.get_sheet_data()
            if row is None or row < 0 or row >= len(data) or not data[row]:
                return
            open_ticker_views(data[row][0])

        sheet.bind("<Button-1>", on_click)
        sheet.bind("<Double-Button-1>", on_double)
        sheet.pack(expand=True, fill=tk.BOTH)

    run_in_background(root, lambda: build_matrix(ticker), populate_sheet)
    root.mainloop()


if __name__ == "__main__":
    ticker_symbol = input("Enter the symbol: ").strip().upper()
    if not ticker_symbol:
        print("A ticker symbol is required.")
        sys.exit(1)
    try:
        display_percentage_changes(ticker_symbol)
    except Exception as e:
        print(f"Error displaying percentage changes: {e}")
