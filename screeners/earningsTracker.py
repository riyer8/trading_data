from __future__ import annotations

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ui.bootstrap  # noqa: F401

import datacache
import tkinter as tk
from tkinter import ttk
from portfolio.portfolioInfo import MY_TICKERS
from ui.theme import Colors, style_table, apply_row_stripes
from ui.data_utils import next_earnings_date
from ui.loading import build_loading_panel, run_in_background, show_empty_state
from ui.open_ticker import pack_open_hint, bind_tree_double_click


def all_tickers():
    return sorted(set(MY_TICKERS))


def company_info(ticker):
    try:
        info = datacache.ticker_info(ticker)
        return info.get('longName', 'N/A'), info.get('sector', 'N/A')
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return 'N/A', 'N/A'


def find_next_earnings(ticker):
    try:
        calendar = datacache.ticker_calendar(ticker)
        earnings = next_earnings_date(calendar)
        return earnings.isoformat() if earnings else 'N/A'
    except Exception as e:
        print(f"Error fetching earnings for {ticker}: {e}")
        return 'N/A'


def filter_tickers(progress_cb=None):
    tickers = all_tickers()
    data = []
    total = len(tickers)

    for index, ticker in enumerate(tickers, start=1):
        if progress_cb:
            progress_cb(index, total, ticker)
        company_name, sector = company_info(ticker)
        next_earnings = find_next_earnings(ticker)
        if next_earnings != 'N/A':
            data.append([ticker, company_name, sector, next_earnings])

    return sorted(data, key=lambda x: x[3])


def sort_tickers(treeview, column, reverse):
    column_indices = {"Ticker": 0, "Company Name": 1, "Sector": 2, "Upcoming Earnings": 3}
    col_index = column_indices[column]

    items = [(treeview.item(child)['values'], child) for child in treeview.get_children()]

    if column == "Upcoming Earnings":
        items.sort(key=lambda x: (x[0][col_index] == 'N/A', x[0][col_index]), reverse=reverse)
    else:
        items.sort(key=lambda x: x[0][col_index], reverse=reverse)

    treeview.delete(*treeview.get_children())
    for values, item in items:
        treeview.insert("", tk.END, iid=item, values=values)

    for col in column_indices:
        treeview.heading(col, text=col)

    arrow = "↓" if reverse else "↑"
    treeview.heading(column, text=f"{column} {arrow}", command=lambda: sort_tickers(treeview, column, not reverse))
    apply_row_stripes(treeview)


def display_tickers():
    root = tk.Tk()
    root.title("Upcoming Earnings Tickers")
    root.geometry("860x520")
    style_table(root)

    frame = tk.Frame(root, bg=Colors.BACKGROUND)
    frame.pack(padx=12, pady=12, fill=tk.BOTH, expand=True)
    pack_open_hint(frame)

    status_frame, status_label, detail_label, progress = build_loading_panel(
        frame, "Loading upcoming earnings…"
    )

    columns = ("Ticker", "Company Name", "Sector", "Upcoming Earnings")
    tree = ttk.Treeview(frame, columns=columns, show='headings')
    column_widths = {
        "Ticker": 100, "Company Name": 200, "Sector": 150, "Upcoming Earnings": 150
    }

    for col in columns:
        tree.heading(col, text=col, command=lambda col=col: sort_tickers(tree, col, False))
        tree.column(col, width=column_widths[col])
    bind_tree_double_click(tree)

    def update_progress(done, total, ticker):
        progress.configure(maximum=max(total, 1), value=done)
        status_label.configure(text=f"Loading upcoming earnings… ({done}/{total})")
        detail_label.configure(text=f"Checking {ticker}")

    def populate_table(rows):
        status_frame.pack_forget()
        if not rows:
            show_empty_state(
                status_label, detail_label, progress,
                "No upcoming earnings found",
                "No earnings dates were returned. Check your connection or .datacache/.",
            )
            status_frame.pack(fill=tk.X, pady=(0, 8))
            return

        tree.pack(expand=True, fill=tk.BOTH)
        for item in rows:
            tree.insert("", tk.END, values=item)
        apply_row_stripes(tree)
        root.title(f"Upcoming Earnings Tickers ({len(rows)})")

    run_in_background(
        root,
        lambda: filter_tickers(progress_cb=lambda d, t, s: root.after(0, update_progress, d, t, s)),
        populate_table,
    )
    root.mainloop()


if __name__ == "__main__":
    display_tickers()
