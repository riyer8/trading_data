from __future__ import annotations

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ui.bootstrap  # noqa: F401

import tkinter as tk
from tkinter import ttk
import datacache
from portfolio.portfolioInfo import MY_TICKERS
from ui.theme import Colors, style_table, apply_row_stripes
from ui.data_utils import flatten_columns, format_metric
from ui.loading import build_loading_panel, run_in_background, show_empty_state
from ui.open_ticker import pack_open_hint, bind_tree_double_click


def fetch_all_tickers():
    return sorted(set(MY_TICKERS))


def get_company_info(ticker):
    try:
        info = datacache.ticker_info(ticker)
        return info.get('longName', 'N/A'), info.get('sector', 'N/A')
    except Exception as e:
        print(f"Error fetching company info for {ticker}: {e}")
        return 'N/A', 'N/A'


def calculate_rsi(data, period=14):
    delta = data['Close'].diff(1)
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]


def safe_fetch(ticker):
    try:
        data = datacache.download(ticker, period="6mo", interval="1d")
        data = flatten_columns(data)
        if data.empty:
            return None
        return data
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None


def collect_technical_data(ticker):
    data = safe_fetch(ticker)
    if data is None:
        return None

    last_price = data['Close'].iloc[-1]
    rsi = calculate_rsi(data)
    pe_ratio = datacache.ticker_info(ticker).get('trailingPE')
    ma_50 = data['Close'].rolling(window=50).mean().iloc[-1]
    short_percent_float = datacache.ticker_info(ticker).get('shortPercentFloat')
    spx_beta = datacache.ticker_info(ticker).get('beta')
    return last_price, rsi, pe_ratio, ma_50, short_percent_float, spx_beta


def collect_all_rows(progress_cb=None):
    rows = []
    tickers = fetch_all_tickers()
    total = len(tickers)

    for index, ticker in enumerate(tickers, start=1):
        if progress_cb:
            progress_cb(index, total, ticker)

        company_name, sector = get_company_info(ticker)
        metrics = collect_technical_data(ticker)
        if metrics is None:
            rows.append((
                ticker, company_name, sector,
                "N/A", "N/A", "N/A", "N/A", "N/A", "N/A",
            ))
            continue

        last_price, rsi, pe_ratio, ma_50, short_percent_float, spx_beta = metrics
        short_display = format_metric(
            float(short_percent_float) * 100 if short_percent_float not in (None, 'N/A') else None,
            "{:.2f}%",
        )
        rows.append((
            ticker,
            company_name,
            sector,
            format_metric(last_price),
            format_metric(rsi),
            format_metric(pe_ratio),
            format_metric(ma_50),
            short_display,
            format_metric(spx_beta),
        ))
    return rows


def sort_treeview_column(treeview, column, reverse):
    column_indices = {
        "Ticker": 0, "Company Name": 1, "Sector": 2,
        "Last Price": 3, "RSI": 4, "P/E Ratio": 5,
        "50-Day MA": 6, "Short % Float": 7, "SPX Beta": 8
    }
    col_index = column_indices[column]
    items = [(treeview.item(child)['values'], child) for child in treeview.get_children()]

    if column in ["RSI", "P/E Ratio", "50-Day MA", "Last Price", "Short % Float", "SPX Beta"]:
        items.sort(
            key=lambda x: float(str(x[0][col_index]).strip('%'))
            if x[0][col_index] not in ["N/A", ""] else float('inf'),
            reverse=reverse,
        )
    else:
        items.sort(key=lambda x: x[0][col_index], reverse=reverse)

    treeview.delete(*treeview.get_children())
    for values, item in items:
        treeview.insert("", tk.END, iid=item, values=values)

    for col in column_indices:
        if col == column:
            arrow = "↓" if reverse else "↑"
            treeview.heading(col, text=f"{col} {arrow}", command=lambda c=col: sort_treeview_column(treeview, c, not reverse))
        else:
            treeview.heading(col, text=col, command=lambda c=col: sort_treeview_column(treeview, c, False))
    apply_row_stripes(treeview)


def create_technical_indicators_screen():
    root = tk.Tk()
    root.title("Technical Indicators")
    root.geometry("980x560")
    style_table(root)

    frame = tk.Frame(root, bg=Colors.BACKGROUND)
    frame.pack(padx=12, pady=12, fill=tk.BOTH, expand=True)
    pack_open_hint(frame)

    status_frame, status_label, detail_label, progress = build_loading_panel(
        frame, "Loading technical indicators…"
    )

    columns = ("Ticker", "Company Name", "Sector", "Last Price", "RSI", "P/E Ratio", "50-Day MA", "Short % Float", "SPX Beta")
    tree = ttk.Treeview(frame, columns=columns, show='headings')
    column_widths = {
        "Ticker": 50, "Company Name": 150, "Sector": 100,
        "Last Price": 100, "RSI": 80, "P/E Ratio": 80,
        "50-Day MA": 100, "Short % Float": 100, "SPX Beta": 100
    }

    for col in columns:
        tree.heading(col, text=col, command=lambda c=col: sort_treeview_column(tree, c, False))
        tree.column(col, width=column_widths[col])
    bind_tree_double_click(tree)

    def update_progress(done, total, ticker):
        progress.configure(maximum=max(total, 1), value=done)
        status_label.configure(text=f"Loading technical indicators… ({done}/{total})")
        detail_label.configure(text=f"Fetching {ticker}")

    def populate_table(rows):
        status_frame.pack_forget()
        if not rows:
            show_empty_state(
                status_label, detail_label, progress,
                "No technical data loaded",
                "Check your connection or .datacache/.",
            )
            status_frame.pack(fill=tk.X, pady=(0, 8))
            return

        tree.pack(expand=True, fill=tk.BOTH)
        for row in rows:
            tree.insert("", tk.END, values=row)
        apply_row_stripes(tree)
        root.title(f"Technical Indicators ({len(rows)})")

    run_in_background(
        root,
        lambda: collect_all_rows(progress_cb=lambda d, t, s: root.after(0, update_progress, d, t, s)),
        populate_table,
    )
    root.mainloop()


if __name__ == "__main__":
    create_technical_indicators_screen()
