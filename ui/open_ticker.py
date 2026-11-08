"""Open a ticker's chart and snapshot from any table."""

from __future__ import annotations

import os
import subprocess
import sys
import time
import tkinter as tk

from ui.theme import Colors, Fonts

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOUBLE_CLICK_HINT = "Double-click a row to open the chart and snapshot."

_opened_at: dict[str, float] = {}


def open_ticker_views(ticker: str, lookback_months: int = 6) -> None:
    """Launch the candlestick chart and the snapshot window for one ticker."""
    symbol = str(ticker).strip().upper()
    if not symbol or symbol in {"N/A", "—", "-"}:
        return

    now = time.monotonic()
    if now - _opened_at.get(symbol, 0.0) < 1.2:
        return
    _opened_at[symbol] = now

    lookback = str(lookback_months)
    subprocess.Popen(
        [sys.executable, "-m", "charts.stockChart", symbol, lookback],
        cwd=PROJECT_ROOT,
    )
    subprocess.Popen(
        [sys.executable, "-m", "charts.stockDetail", symbol],
        cwd=PROJECT_ROOT,
    )


def bind_tree_double_click(tree, ticker_column: int = 0) -> None:
    """Open chart + snapshot when a data row is double-clicked."""

    def on_double_click(event):
        if tree.identify_region(event.x, event.y) != "cell":
            return
        row_id = tree.identify_row(event.y)
        if not row_id:
            return
        values = tree.item(row_id, "values")
        if not values or ticker_column >= len(values):
            return
        open_ticker_views(values[ticker_column])

    tree.bind("<Double-1>", on_double_click)


def pack_open_hint(parent, text: str | None = None) -> tk.Label:
    label = tk.Label(
        parent,
        text=text or DOUBLE_CLICK_HINT,
        bg=Colors.BACKGROUND,
        fg=Colors.MUTED,
        font=(Fonts.sans_name, 11),
        anchor=tk.W,
    )
    label.pack(fill=tk.X, pady=(0, 8))
    return label
