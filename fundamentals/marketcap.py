import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk

import matplotlib
import matplotlib.colors as mcolors
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

import datacache
from portfolio.portfolioInfo import MY_TICKERS
from ui.theme import Colors, Fonts, apply_chart_theme

HIGHLIGHT_TICKER = 'PYPL'


def get_historical_market_cap(ticker, start_date, end_date):
    history = datacache.ticker_history(ticker, start=start_date, end=end_date)
    market_cap = history['Close'] * datacache.ticker_info(ticker)['sharesOutstanding']
    return market_cap


def _distinct_colors(n):
    """Spread n visually distinct colors across the 'turbo' colormap."""
    cmap = matplotlib.colormaps['turbo']
    if n <= 1:
        return [cmap(0.5)]
    return [cmap(i / (n - 1)) for i in range(n)]


def _bind_mousewheel(canvas, container):
    """Enable smooth trackpad / mouse-wheel scrolling over the legend panel."""

    def _scroll_amount(event):
        # macOS trackpad: small deltas (±1–15). Windows mouse wheel: ±120 per notch.
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
        return "break"  # don't propagate to widgets behind the legend

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
        # Defer so moving between header ↔ list doesn't drop the binding mid-swipe.
        container.after_idle(_maybe_unbind)

    def _maybe_unbind():
        if not _still_over_legend():
            root = container.winfo_toplevel()
            root.unbind_all("<MouseWheel>")
            root.unbind_all("<Button-4>")
            root.unbind_all("<Button-5>")

    # While the cursor is anywhere over the legend, capture swipe/scroll globally
    # so two-finger trackpad movement works reliably on macOS.
    for widget in (container, canvas):
        widget.bind("<Enter>", _bind_all, add="+")
        widget.bind("<Leave>", _unbind_all, add="+")

    def _bind_tree(widget):
        _bind_to(widget)
        for child in widget.winfo_children():
            _bind_tree(child)

    return _bind_tree, _bind_to


def _build_scrollable_legend(parent, entries):
    """A vertically scrollable key: a color swatch + ticker per row."""
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


def compare_market_caps(tickers, start_date, end_date):
    market_caps = {}
    for ticker in tickers:
        historical_market_cap = get_historical_market_cap(ticker, start_date, end_date)
        if historical_market_cap is not None and not historical_market_cap.empty:
            market_caps[ticker] = historical_market_cap

    if not market_caps:
        print("No market cap data available for the requested tickers.")
        return

    # Build the figure with the Figure API (not pyplot). On macOS, pyplot would
    # initialize the MacOSX backend's NSApplication, which crashes Tcl/Tk 9
    # ("-[NSApplication macOSVersion]: unrecognized selector"). Embedding a
    # plain Figure in Tk avoids the conflict.
    apply_chart_theme()
    fig = Figure(figsize=(11, 6))
    ax = fig.add_subplot(111)

    colors = _distinct_colors(len(market_caps))
    legend_entries = []
    for (ticker, market_cap), color in zip(market_caps.items(), colors):
        highlight = ticker == HIGHLIGHT_TICKER
        ax.plot(market_cap.index, market_cap.values, color=color,
                linewidth=3 if highlight else 1.3, alpha=1.0 if highlight else 0.85)
        legend_entries.append((ticker, mcolors.to_hex(color), highlight))

    ax.set_xlabel('Date')
    ax.set_ylabel('Market Capitalization')
    ax.set_title('Market Capitalization Growth Over Quarters')
    ax.yaxis.set_major_formatter(lambda x, _pos: f"${x / 1e9:.0f}B")
    ax.margins(x=0.01)
    fig.autofmt_xdate(rotation=30)
    fig.tight_layout()

    # Embed the figure in a Tk window with a scrollable ticker key beside it.
    root = tk.Tk()
    root.title("Market Capitalization")
    root.configure(bg=Colors.BACKGROUND)
    root.geometry("1200x680")

    legend = _build_scrollable_legend(root, legend_entries)
    legend.pack(side="right", fill="y")

    chart_frame = tk.Frame(root, bg=Colors.BACKGROUND)
    chart_frame.pack(side="left", fill="both", expand=True)

    canvas = FigureCanvasTkAgg(fig, master=chart_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(side="top", fill="both", expand=True)
    NavigationToolbar2Tk(canvas, chart_frame)

    root.mainloop()


if __name__ == "__main__":
    start_date = "2023-05-01"
    end_date = "2024-01-01"
    compare_market_caps(MY_TICKERS, start_date, end_date)
