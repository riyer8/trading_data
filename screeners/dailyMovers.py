from __future__ import annotations

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ui.bootstrap  # noqa: F401

import tkinter as tk
from tkinter import ttk
import datacache
from portfolio.portfolioInfo import MY_TICKERS
from ui.theme import Colors, Fonts, style_table, apply_row_stripes
from ui.data_utils import flatten_columns, safe_pct_change, to_scalar
from ui.loading import attach_tree_scrollbar
from ui.open_ticker import DOUBLE_CLICK_HINT, bind_tree_double_click

DOWNLOAD_KEY_KWARGS = {"period": "5d", "interval": "1d"}


def _terminal_progress(done: int, total: int, ticker: str) -> None:
    print(f"  [{done:3d}/{total}] {ticker}", flush=True)


def company_info(ticker: str) -> tuple[str, str]:
    key = "info|" + datacache._normalize(ticker)
    cached = datacache.read_cached(key, allow_stale=True)
    if cached:
        return cached.get("longName", "N/A"), cached.get("sector", "N/A")
    try:
        info = datacache.ticker_info(ticker)
        return info.get("longName", "N/A"), info.get("sector", "N/A")
    except Exception as exc:
        print(f"  info skip {ticker}: {exc}")
        return "N/A", "N/A"


def calculate_standard_deviation(data):
    data = data.copy()
    data["Percent Change"] = data["Close"].pct_change() * 100
    return to_scalar(data["Percent Change"].std())


def calculate_volume_change(data):
    last_volume = to_scalar(data["Volume"].iloc[-2])
    today_volume = to_scalar(data["Volume"].iloc[-1])
    if not last_volume:
        return 0.0
    return ((today_volume - last_volume) / last_volume) * 100


def volume_to_string(volume):
    volume = to_scalar(volume) or 0
    if volume >= 1e6:
        return f"{volume / 1e6:.2f}M"
    if volume >= 1e3:
        return f"{volume / 1e3:.2f}K"
    return f"{volume:.2f}"


def string_to_volume(volume_str):
    if volume_str.endswith("M"):
        return float(volume_str[:-1]) * 1e6
    if volume_str.endswith("K"):
        return float(volume_str[:-1]) * 1e3
    return float(volume_str)


def collect_data(ticker: str):
    try:
        data = flatten_columns(datacache.download(ticker, **DOWNLOAD_KEY_KWARGS))
        if data.empty or len(data["Close"].dropna()) < 2:
            return None

        last_price = to_scalar(data["Close"].iloc[-1])
        prev_close = to_scalar(data["Close"].iloc[-2])
        percentage_change = safe_pct_change(last_price, prev_close)
        if last_price is None or percentage_change is None:
            return None

        return {
            "ticker": ticker,
            "last_price": float(last_price),
            "percentage_change": float(percentage_change),
            "std_dev": float(calculate_standard_deviation(data) or 0.0),
            "volume": float(to_scalar(data["Volume"].iloc[-1]) or 0),
            "volume_change": float(calculate_volume_change(data)),
        }
    except Exception as exc:
        print(f"  skip {ticker}: {exc}")
        return None


def load_rows(progress_cb=None) -> list[dict]:
    tickers = sorted(set(MY_TICKERS))
    total = len(tickers)
    rows: list[dict] = []

    print(f"Loading {total} tickers (fresh cache ≤ {datacache.CACHE_TTL_SECONDS // 60} min, else network/stale)…")

    for index, ticker in enumerate(tickers, start=1):
        if progress_cb:
            progress_cb(index, total, ticker)

        row = collect_data(ticker)
        if row is None or row["last_price"] < 10:
            continue

        company_name, sector = company_info(ticker)
        row["company_name"] = company_name
        row["sector"] = sector
        rows.append(row)

    rows.sort(key=lambda item: item["percentage_change"], reverse=True)
    return rows


def sort_tickers(treeview, column, reverse):
    column_indices = {
        "Ticker": 0, "Company Name": 1, "Sector": 2, "Last Price": 3,
        "Percentage Change": 4, "Standard Deviation": 5, "Volume": 6, "Volume Change": 7,
    }
    col_index = column_indices[column]
    items = [(treeview.item(child)["values"], child) for child in treeview.get_children()]

    if column in ["Last Price", "Percentage Change", "Standard Deviation", "Volume", "Volume Change"]:
        if column == "Volume":
            items.sort(key=lambda x: string_to_volume(x[0][col_index]), reverse=reverse)
        else:
            items.sort(key=lambda x: float(x[0][col_index]), reverse=reverse)
    else:
        items.sort(key=lambda x: x[0][col_index], reverse=reverse)

    treeview.delete(*treeview.get_children())
    for values, item in items:
        percent_change = float(values[4])
        tag = "positive" if percent_change > 0 else "negative"
        treeview.insert("", tk.END, iid=item, values=values, tags=(tag,))

    for col in column_indices:
        treeview.heading(col, text=col)
    arrow = "↓" if reverse else "↑"
    treeview.heading(column, text=f"{column} {arrow}", command=lambda: sort_tickers(treeview, column, not reverse))
    apply_row_stripes(treeview)


def _build_table(parent, rows):
    columns = (
        "Ticker", "Company Name", "Sector", "Last Price",
        "Percentage Change", "Standard Deviation", "Volume", "Volume Change",
    )
    tree = ttk.Treeview(parent, columns=columns, show="headings")
    column_widths = {
        "Ticker": 70, "Company Name": 180, "Sector": 120, "Last Price": 90,
        "Percentage Change": 90, "Standard Deviation": 90, "Volume": 90, "Volume Change": 100,
    }
    for col in columns:
        tree.heading(col, text=col, command=lambda col=col: sort_tickers(tree, col, False))
        tree.column(col, width=column_widths[col], minwidth=60, stretch=True)

    for row in rows:
        pct = row["percentage_change"]
        tag = "positive" if pct > 0 else "negative"
        tree.insert(
            "",
            tk.END,
            values=(
                row["ticker"],
                row["company_name"],
                row["sector"],
                f"{row['last_price']:.2f}",
                f"{pct:.2f}",
                f"{row['std_dev']:.2f}",
                volume_to_string(row["volume"]),
                f"{row['volume_change']:.2f}",
            ),
            tags=(tag,),
        )

    bind_tree_double_click(tree)
    attach_tree_scrollbar(parent, tree)
    apply_row_stripes(tree)
    return tree


def display_tickers(rows: list[dict]) -> None:
    root = tk.Tk()
    root.title(f"Top Moving Tickers ({len(rows)})")
    root.geometry("980x560")
    root.minsize(720, 420)
    style_table(root)

    frame = tk.Frame(root, bg=Colors.BACKGROUND)
    frame.pack(padx=12, pady=12, fill=tk.BOTH, expand=True)

    tk.Label(
        frame,
        text=f"{len(rows)} tickers · {DOUBLE_CLICK_HINT}",
        bg=Colors.BACKGROUND,
        fg=Colors.MUTED,
        font=(Fonts.sans_name, 11),
        anchor=tk.W,
    ).pack(fill=tk.X, pady=(0, 8))

    _build_table(frame, rows)
    root.mainloop()


def main() -> None:
    rows = load_rows(progress_cb=_terminal_progress)
    if not rows:
        print(
            "\nNo ticker data loaded.\n"
            "Run once while online so .datacache/ can fill, then retry."
        )
        sys.exit(1)
    print(f"\nReady — opening table with {len(rows)} tickers.")
    display_tickers(rows)


if __name__ == "__main__":
    main()
