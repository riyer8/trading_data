"""Central "trading desk" theme for every chart and table UI in the project.

All fonts, colors, and sizes live here instead of being hard-coded across each
chart/screen. Typical usage:

    from ui.theme import Colors, Fonts, apply_chart_theme, value_tag

    apply_chart_theme()            # call once before building a figure
    fig, ax = plt.subplots()
    ax.plot(..., color=Colors.BULL)

For matplotlib charts call ``apply_chart_theme()`` first. For mplfinance
candlesticks pass ``style=candlestick_style()``. For tkinter tables call
``style_table(root)`` (and ``apply_row_stripes`` / the ``positive`` /
``negative`` row tags), and for tksheet grids call ``style_sheet(sheet)``.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class _Palette:
    """A dark, terminal-style palette inspired by professional trading desks."""

    # Surfaces (darkest -> lightest)
    BACKGROUND: str = "#0b0e14"   # window / figure background
    PANEL: str = "#131722"        # plotting area / table body
    HEADER: str = "#1c2030"       # table headers / chrome
    GRID: str = "#2a2e39"         # gridlines, spines, separators

    # Text
    TEXT: str = "#d1d4dc"         # primary text
    MUTED: str = "#787b86"        # secondary / axis text

    # Directional (up / down)
    BULL: str = "#26a69a"         # gains, bullish
    BEAR: str = "#ef5350"         # losses, bearish
    BULL_FILL: str = "#1b3d3a"    # translucent-looking bullish fill
    BEAR_FILL: str = "#4a2326"    # translucent-looking bearish fill

    # Accents for series / overlays
    ACCENT: str = "#2962ff"       # primary blue
    ACCENT_2: str = "#ff9800"     # orange
    ACCENT_3: str = "#ab47bc"     # purple
    ACCENT_4: str = "#26c6da"     # cyan
    ACCENT_5: str = "#ffca28"     # amber

    SELECTION: str = "#26a69a"    # zoom-selection highlight


Colors = _Palette()


@dataclass(frozen=True)
class _Fonts:
    """Font families and a consistent type scale (in points)."""

    # Family fallbacks; matplotlib/tk pick the first that is installed.
    SANS: tuple = ("Helvetica Neue", "Arial", "DejaVu Sans", "Liberation Sans")
    MONO: tuple = ("SF Mono", "Menlo", "Monaco", "Roboto Mono", "DejaVu Sans Mono")

    # Type scale
    TITLE: int = 15
    SUBTITLE: int = 12
    LABEL: int = 11
    TICK: int = 9
    LEGEND: int = 9
    ANNOTATION: int = 9

    @property
    def sans_name(self) -> str:
        return self.SANS[0]

    @property
    def mono_name(self) -> str:
        return self.MONO[0]


Fonts = _Fonts()

# Ordered palette used to auto-color an arbitrary number of overlay series.
_SERIES_CYCLE = [
    Colors.ACCENT,
    Colors.ACCENT_2,
    Colors.ACCENT_3,
    Colors.ACCENT_4,
    Colors.ACCENT_5,
]


def apply_chart_theme():
    """Apply the trading-desk look to matplotlib via rcParams.

    Call this once before creating a figure. It centralizes every font size,
    color, and grid setting so individual charts no longer hard-code them.
    """
    import matplotlib as mpl

    mpl.rcParams.update({
        # Fonts
        "font.family": "sans-serif",
        "font.sans-serif": list(Fonts.SANS),
        "font.monospace": list(Fonts.MONO),
        "font.size": Fonts.LABEL,

        # Figure / axes surfaces
        "figure.facecolor": Colors.BACKGROUND,
        "figure.edgecolor": Colors.BACKGROUND,
        "axes.facecolor": Colors.PANEL,
        "axes.edgecolor": Colors.GRID,
        "savefig.facecolor": Colors.BACKGROUND,

        # Text colors
        "text.color": Colors.TEXT,
        "axes.labelcolor": Colors.MUTED,
        "xtick.color": Colors.MUTED,
        "ytick.color": Colors.MUTED,
        "axes.titlecolor": Colors.TEXT,

        # Title / label sizing & weight
        "axes.titlesize": Fonts.TITLE,
        "axes.titleweight": "bold",
        "axes.titlepad": 12,
        "axes.labelsize": Fonts.LABEL,
        "xtick.labelsize": Fonts.TICK,
        "ytick.labelsize": Fonts.TICK,

        # Spines: keep only left/bottom for a clean look
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.linewidth": 0.8,

        # Grid
        "axes.grid": True,
        "axes.grid.axis": "both",
        "grid.color": Colors.GRID,
        "grid.linestyle": "-",
        "grid.linewidth": 0.6,
        "grid.alpha": 0.5,

        # Lines
        "lines.linewidth": 1.6,
        "lines.solid_capstyle": "round",

        # Legend
        "legend.fontsize": Fonts.LEGEND,
        "legend.facecolor": Colors.HEADER,
        "legend.edgecolor": Colors.GRID,
        "legend.framealpha": 0.95,
        "legend.labelcolor": Colors.TEXT,

        # Misc
        "figure.autolayout": False,
        "axes.axisbelow": True,
    })


def candlestick_style():
    """Return an mplfinance style matching the trading-desk theme."""
    import mplfinance as mpf

    market_colors = mpf.make_marketcolors(
        up=Colors.BULL,
        down=Colors.BEAR,
        edge={"up": Colors.BULL, "down": Colors.BEAR},
        wick={"up": Colors.BULL, "down": Colors.BEAR},
        volume={"up": Colors.BULL, "down": Colors.BEAR},
    )

    return mpf.make_mpf_style(
        base_mpf_style="nightclouds",
        marketcolors=market_colors,
        facecolor=Colors.PANEL,
        figcolor=Colors.BACKGROUND,
        edgecolor=Colors.GRID,
        gridcolor=Colors.GRID,
        gridstyle="-",
        rc={
            "font.family": "sans-serif",
            "font.sans-serif": list(Fonts.SANS),
            "axes.labelcolor": Colors.MUTED,
            "xtick.color": Colors.MUTED,
            "ytick.color": Colors.MUTED,
            "text.color": Colors.TEXT,
            "axes.titlesize": Fonts.TITLE,
            "axes.titleweight": "bold",
            "axes.labelsize": Fonts.LABEL,
            "xtick.labelsize": Fonts.TICK,
            "ytick.labelsize": Fonts.TICK,
        },
    )


def moving_average_colors(count):
    """Return ``count`` distinct overlay colors from the accent cycle."""
    return [_SERIES_CYCLE[i % len(_SERIES_CYCLE)] for i in range(count)]


def style_legend(ax, loc="upper left"):
    """Apply a consistent panel-style legend to an axes."""
    legend = ax.legend(loc=loc, fontsize=Fonts.LEGEND)
    if legend is not None:
        frame = legend.get_frame()
        frame.set_facecolor(Colors.HEADER)
        frame.set_edgecolor(Colors.GRID)
        frame.set_alpha(0.95)
        for text in legend.get_texts():
            text.set_color(Colors.TEXT)
    return legend


def value_tag(ax, x, y, text, color):
    """Draw a small rounded "price tag" label at (x, y) on the right edge.

    Used to annotate the latest value of a series, the way live tickers do.
    """
    ax.annotate(
        text,
        xy=(x, y),
        xytext=(6, 0),
        textcoords="offset points",
        va="center",
        ha="left",
        fontsize=Fonts.ANNOTATION,
        fontweight="bold",
        fontfamily="monospace",
        color="#ffffff",
        bbox=dict(boxstyle="round,pad=0.3", facecolor=color, edgecolor="none", alpha=0.95),
        clip_on=False,
    )


def set_window_title(fig, title):
    """Set the OS window title for a figure (best-effort)."""
    try:
        fig.canvas.manager.set_window_title(title)
    except Exception:
        pass


# --------------------------------------------------------------------------- #
# Tkinter / ttk table styling
# --------------------------------------------------------------------------- #

def style_table(root, rowheight=28):
    """Style a tkinter window + its ttk.Treeview widgets as a dark data grid.

    Returns the configured ``ttk.Style``. Tables should also tag rows with
    ``positive`` / ``negative`` (configured here) for up/down coloring, and may
    call :func:`apply_row_stripes` for alternating row shading.
    """
    import tkinter as tk
    from tkinter import ttk

    root.configure(bg=Colors.BACKGROUND)
    try:
        root.option_add("*Font", (Fonts.sans_name, 11))
    except tk.TclError:
        pass

    style = ttk.Style(root)
    # 'clam' honors custom background/foreground colors (the default macOS
    # 'aqua' theme ignores them).
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure(
        "Treeview",
        background=Colors.PANEL,
        fieldbackground=Colors.PANEL,
        foreground=Colors.TEXT,
        rowheight=rowheight,
        borderwidth=0,
        font=(Fonts.mono_name, 11),
    )
    style.configure(
        "Treeview.Heading",
        background=Colors.HEADER,
        foreground=Colors.TEXT,
        relief="flat",
        borderwidth=0,
        padding=(8, 6),
        font=(Fonts.sans_name, 11, "bold"),
    )
    style.map(
        "Treeview.Heading",
        background=[("active", Colors.GRID)],
        foreground=[("active", Colors.ACCENT_4)],
    )
    style.map(
        "Treeview",
        background=[("selected", Colors.ACCENT)],
        foreground=[("selected", "#ffffff")],
    )
    return style


def apply_row_stripes(tree, items_with_tags=None):
    """Configure and apply alternating ('even'/'odd') row shading to a Treeview.

    Also (re)configures the shared ``positive`` / ``negative`` directional tags.
    Call after inserting rows; it walks existing children and stripes them.
    """
    # Stripe tags set background only and directional tags set foreground only,
    # so a row can carry both (e.g. a green value on a striped row) without one
    # clobbering the other.
    tree.tag_configure("even", background=Colors.PANEL)
    tree.tag_configure("odd", background=Colors.HEADER)
    tree.tag_configure("positive", foreground=Colors.BULL)
    tree.tag_configure("negative", foreground=Colors.BEAR)

    for index, child in enumerate(tree.get_children()):
        existing = list(tree.item(child, "tags"))
        stripe = "even" if index % 2 == 0 else "odd"
        # Preserve directional tags but refresh the stripe tag.
        existing = [t for t in existing if t not in ("even", "odd")]
        tree.item(child, tags=tuple(existing + [stripe]))


# --------------------------------------------------------------------------- #
# tksheet styling
# --------------------------------------------------------------------------- #

def style_sheet(sheet):
    """Apply the dark trading-desk theme to a tksheet ``Sheet`` widget."""
    try:
        sheet.set_options(
            table_bg=Colors.PANEL,
            table_fg=Colors.TEXT,
            table_grid_fg=Colors.GRID,
            header_bg=Colors.HEADER,
            header_fg=Colors.TEXT,
            header_grid_fg=Colors.GRID,
            index_bg=Colors.HEADER,
            index_fg=Colors.TEXT,
            index_grid_fg=Colors.GRID,
            top_left_bg=Colors.BACKGROUND,
            top_left_fg=Colors.MUTED,
            table_selected_cells_border_fg=Colors.ACCENT_4,
            table_selected_cells_bg=Colors.GRID,
            table_selected_rows_bg=Colors.GRID,
            table_selected_columns_bg=Colors.GRID,
            font=(Fonts.mono_name, 11, "normal"),
            header_font=(Fonts.sans_name, 11, "bold"),
        )
    except Exception:
        # Older tksheet versions use a different option surface; ignore so the
        # grid still renders even if it can't be fully themed.
        pass
