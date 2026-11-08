from __future__ import annotations

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ui.bootstrap  # noqa: F401

import threading
import tkinter as tk
from datetime import datetime, timedelta

import matplotlib
import matplotlib.colors as mcolors
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

import datacache
from portfolio.portfolioInfo import MY_TICKERS
from ui.theme import Colors, Fonts, apply_chart_theme
from ui.data_utils import flatten_columns
from ui.loading import build_loading_panel

HIGHLIGHT_TICKER = 'PYPL'


def get_historical_market_cap(ticker, start_date, end_date):
    history = flatten_columns(datacache.ticker_history(ticker, start=start_date, end=end_date))
    shares = datacache.ticker_info(ticker).get('sharesOutstanding')
    if history.empty or not shares:
        return None
    return history['Close'] * shares


def _distinct_colors(n):
    cmap = matplotlib.colormaps['turbo']
    if n <= 1:
        return [cmap(0.5)]
    return [cmap(i / (n - 1)) for i in range(n)]


def _bind_mousewheel(canvas, container):
    def _scroll_amount(event):
        if getattr(event, "num", None) == 4:
            return -3
        if getattr(event, "num", None) == 5:
            return 3
        delta = getattr(event, "delta", 0)
        if sys.platform == "darwin":
            return int(-delta)
        return int(-delta / 120) or (-1 if delta > 0 else 1)

    def _on_wheel(event):
        canvas.yview_scroll(_scroll_amount(event), "units")
        return "break"

    def _bind_to(widget):
        widget.bind("<MouseWheel>", _on_wheel, add="+")
        widget.bind("<Button-4>", _on_wheel, add="+")
        widget.bind("<Button-5>", _on_wheel, add="+")

    def _still_over_legend():
        x, y = container.winfo_pointerxy()
        widget = container.winfo_containing(x, y)
        while widget is not None:
            if widget == container:
                return True
            widget = widget.master
        return False

    def _bind_all(_event=None):
        root = container.winfo_toplevel()
        root.bind_all("<MouseWheel>", _on_wheel, add="+")
        root.bind_all("<Button-4>", _on_wheel, add="+")
        root.bind_all("<Button-5>", _on_wheel, add="+")

    def _unbind_all(_event=None):
        container.after_idle(_maybe_unbind)

    def _maybe_unbind():
        if not _still_over_legend():
            root = container.winfo_toplevel()
            root.unbind_all("<MouseWheel>")
            root.unbind_all("<Button-4>")
            root.unbind_all("<Button-5>")

    for widget in (container, canvas):
        widget.bind("<Enter>", _bind_all, add="+")
        widget.bind("<Leave>", _unbind_all, add="+")

    def _bind_tree(widget):
        _bind_to(widget)
        for child in widget.winfo_children():
            _bind_tree(child)

    return _bind_tree, _bind_to


def _build_scrollable_legend(parent, entries):
    container = tk.Frame(parent, bg=Colors.HEADER)

    header = tk.Label(container, text="TICKERS", bg=Colors.HEADER, fg=Colors.MUTED,
                      font=(Fonts.sans_name, 10, "bold"), anchor="w", padx=10, pady=6)
    header.pack(side="top", fill="x")

    body = tk.Frame(container, bg=Colors.HEADER)
    body.pack(side="top", fill="both", expand=True)

    canvas = tk.Canvas(body, bg=Colors.PANEL, highlightthickness=0, width=180)
    scrollbar = tk.Scrollbar(body, orient="vertical", command=canvas.yview)
    inner = tk.Frame(canvas, bg=Colors.PANEL)

    def _on_inner_configure(_event):
        canvas.configure(scrollregion=canvas.bbox("all"))

    def _on_canvas_configure(event):
        canvas.itemconfig(canvas_window, width=event.width)

    inner.bind("<Configure>", _on_inner_configure)
    canvas_window = canvas.create_window((0, 0), window=inner, anchor="nw")
    canvas.bind("<Configure>", _on_canvas_configure)
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    bind_tree, bind_to = _bind_mousewheel(canvas, container)
    bind_to(header)
    bind_to(body)
    bind_to(canvas)
    bind_to(scrollbar)
    bind_to(inner)

    for ticker, hex_color, highlight in entries:
        row = tk.Frame(inner, bg=Colors.PANEL)
        row.pack(fill="x", anchor="w", padx=8, pady=1)

        swatch = tk.Label(row, text="  ", bg=hex_color)
        swatch.pack(side="left", padx=(0, 8), pady=2)

        weight = "bold" if highlight else "normal"
        label = tk.Label(row, text=ticker, bg=Colors.PANEL,
                         fg=Colors.TEXT if highlight else Colors.MUTED,
                         font=(Fonts.mono_name, 10, weight), anchor="w")
        label.pack(side="left")
        bind_tree(row)

    bind_tree(container)
    return container


def _load_market_caps(tickers, start_date, end_date, progress_cb=None):
    market_caps = {}
    total = len(tickers)

    for index, ticker in enumerate(tickers, start=1):
        if progress_cb:
            progress_cb(index, total, ticker)
        historical_market_cap = get_historical_market_cap(ticker, start_date, end_date)
        if historical_market_cap is not None and not historical_market_cap.empty:
            market_caps[ticker] = historical_market_cap

    if not market_caps:
        return None

    colors = _distinct_colors(len(market_caps))
    legend_entries = []
    for ticker, color in zip(market_caps.keys(), colors):
        legend_entries.append((ticker, mcolors.to_hex(color), ticker == HIGHLIGHT_TICKER))

    return market_caps, legend_entries, colors


def _render_chart(parent, market_caps, legend_entries, colors):
    apply_chart_theme()
    fig = Figure(figsize=(11, 6))
    ax = fig.add_subplot(111)

    for (ticker, market_cap), color in zip(market_caps.items(), colors):
        highlight = ticker == HIGHLIGHT_TICKER
        ax.plot(market_cap.index, market_cap.values, color=color,
                linewidth=3 if highlight else 1.3, alpha=1.0 if highlight else 0.85)

    ax.set_xlabel('Date')
    ax.set_ylabel('Market cap')
    ax.set_title('Market cap over the last year', pad=18)
    ax.text(
        0.0, 1.02,
        "Share price times shares outstanding. One line per company.",
        transform=ax.transAxes, ha="left", color=Colors.MUTED, fontsize=Fonts.TICK, va="bottom", clip_on=False,
    )
    ax.yaxis.set_major_formatter(lambda x, _pos: f"${x / 1e9:.0f}B")
    ax.margins(x=0.01)
    fig.autofmt_xdate(rotation=30)
    fig.tight_layout(rect=(0, 0, 1, 0.94))

    legend = _build_scrollable_legend(parent, legend_entries)
    legend.pack(side="right", fill="y")

    chart_frame = tk.Frame(parent, bg=Colors.BACKGROUND)
    chart_frame.pack(side="left", fill="both", expand=True)

    canvas = FigureCanvasTkAgg(fig, master=chart_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(side="top", fill="both", expand=True)
    NavigationToolbar2Tk(canvas, chart_frame)


def compare_market_caps(tickers, start_date, end_date):
    root = tk.Tk()
    root.title("Market Capitalization")
    root.configure(bg=Colors.BACKGROUND)
    root.geometry("1200x680")

    shell = tk.Frame(root, bg=Colors.BACKGROUND)
    shell.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

    status_frame, status_label, detail_label, progress = build_loading_panel(
        shell, "Loading market capitalization history…"
    )

    def update_progress(done, total, ticker):
        progress.configure(maximum=max(total, 1), value=done)
        status_label.configure(text=f"Loading market caps… ({done}/{total})")
        detail_label.configure(text=f"Fetching {ticker}")

    def on_loaded(result):
        status_frame.destroy()
        if not result:
            tk.Label(
                shell,
                text="No market cap data loaded.\nCheck your connection or .datacache/.",
                bg=Colors.BACKGROUND,
                fg=Colors.ACCENT_5,
                font=(Fonts.sans_name, 12),
                justify=tk.LEFT,
            ).pack(expand=True)
            return

        market_caps, legend_entries, colors = result
        _render_chart(shell, market_caps, legend_entries, colors)

    def worker():
        try:
            result = _load_market_caps(
                tickers,
                start_date,
                end_date,
                progress_cb=lambda d, t, s: root.after(0, update_progress, d, t, s),
            )
            root.after(0, lambda: on_loaded(result))
        except Exception as exc:
            print(exc)
            root.after(0, lambda: on_loaded(None))

    threading.Thread(target=worker, daemon=True).start()
    root.mainloop()


if __name__ == "__main__":
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=365)
    compare_market_caps(MY_TICKERS, start_date, end_date)
