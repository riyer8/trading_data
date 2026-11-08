"""One window that pulls a ticker's price, technicals, and fundamentals together."""

from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ui.bootstrap  # noqa: F401

import tkinter as tk
from tkinter import ttk

import datacache
from ui.data_utils import flatten_columns, next_earnings_date, to_scalar
from ui.loading import run_in_background
from ui.theme import Colors, Fonts, style_table

NA = "—"


def _number(value):
    number = to_scalar(value)
    if number is None:
        return None
    try:
        number = float(number)
    except (TypeError, ValueError):
        return None
    if math.isnan(number) or math.isinf(number):
        return None
    return number


def _compact(value, prefix: str = "") -> str:
    number = _number(value)
    if number is None:
        return NA
    sign = "-" if number < 0 else ""
    magnitude = abs(number)
    if magnitude >= 1e12:
        body = f"{magnitude / 1e12:.2f}T"
    elif magnitude >= 1e9:
        body = f"{magnitude / 1e9:.2f}B"
    elif magnitude >= 1e6:
        body = f"{magnitude / 1e6:.2f}M"
    elif magnitude >= 1e3:
        body = f"{magnitude / 1e3:.2f}K"
    else:
        body = f"{magnitude:,.2f}"
    return f"{sign}{prefix}{body}"


def _price(value) -> str:
    number = _number(value)
    if number is None:
        return NA
    return f"${number:,.2f}"


def _signed_percent(value) -> str:
    number = _number(value)
    if number is None:
        return NA
    return f"{number:+.2f}%"


def _ratio_percent(value) -> str:
    """Yahoo stores most margins and short interest as fractions (0.31 = 31%)."""
    number = _number(value)
    if number is None:
        return NA
    if abs(number) <= 2:
        number *= 100
    return f"{number:.2f}%"


def _dividend_yield(info: dict, price) -> str:
    """Yield from the annual dividend and price. Yahoo's yield field is inconsistent."""
    rate = _number(info.get("dividendRate"))
    if rate is None:
        rate = _number(info.get("trailingAnnualDividendRate"))
    price_number = _number(price)
    if rate is not None and price_number:
        return f"{(rate / price_number) * 100:.2f}%"

    trailing = _number(info.get("trailingAnnualDividendYield"))
    if trailing is not None:
        if abs(trailing) <= 1:
            trailing *= 100
        return f"{trailing:.2f}%"
    return _ratio_percent(info.get("dividendYield"))


def _plain(value, fmt: str = "{:.2f}") -> str:
    number = _number(value)
    if number is None:
        return NA
    return fmt.format(number)


def _text(value) -> str:
    if value is None:
        return NA
    text = str(value).strip()
    return text or NA


def _rsi(close, period: int = 14):
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, math.nan)
    series = 100 - (100 / (1 + rs))
    if series.dropna().empty:
        return None
    return _number(series.iloc[-1])


def _ma(close, window: int):
    if len(close.dropna()) < window:
        return None
    return _number(close.rolling(window).mean().iloc[-1])


def _latest_operating_margin(ticker: str):
    try:
        financials = datacache.ticker_quarterly_financials(ticker)
    except Exception:
        return None
    if financials is None or getattr(financials, "empty", True):
        return None
    from ui.data_utils import find_financial_row

    revenue = find_financial_row(financials, "Total Revenue", "Total Revenues")
    operating = find_financial_row(financials, "Operating Income")
    if revenue is None or operating is None:
        return None
    margin = (operating / revenue) * 100
    margin = margin.sort_index().dropna()
    if margin.empty:
        return None
    return _number(margin.iloc[-1])


def collect_snapshot(ticker: str) -> dict:
    symbol = ticker.strip().upper()
    info = {}
    try:
        info = datacache.ticker_info(symbol) or {}
    except Exception as exc:
        print(f"info skip {symbol}: {exc}")

    history = None
    try:
        history = flatten_columns(datacache.ticker_history(symbol, period="1y", interval="1d"))
    except Exception as exc:
        print(f"history skip {symbol}: {exc}")

    price = change = prev_close = volume = day_high = day_low = rsi = ma50 = ma200 = None
    if history is not None and not history.empty and "Close" in history.columns:
        close = history["Close"].dropna()
        if len(close) >= 1:
            price = _number(close.iloc[-1])
        if len(close) >= 2 and price is not None:
            prev_close = _number(close.iloc[-2])
            if prev_close:
                change = ((price - prev_close) / prev_close) * 100
        if "Volume" in history.columns and len(history) >= 1:
            volume = _number(history["Volume"].iloc[-1])
        if "High" in history.columns and len(history) >= 1:
            day_high = _number(history["High"].iloc[-1])
        if "Low" in history.columns and len(history) >= 1:
            day_low = _number(history["Low"].iloc[-1])
        rsi = _rsi(close)
        ma50 = _ma(close, 50)
        ma200 = _ma(close, 200)

    if price is None:
        price = _number(info.get("currentPrice") or info.get("regularMarketPrice"))
    if prev_close is None:
        prev_close = _number(info.get("previousClose"))
    if volume is None:
        volume = _number(info.get("volume") or info.get("regularMarketVolume"))

    earnings = None
    try:
        upcoming = next_earnings_date(datacache.ticker_calendar(symbol))
        if upcoming is not None:
            earnings = upcoming.strftime("%b %d, %Y")
    except Exception as exc:
        print(f"earnings skip {symbol}: {exc}")

    operating_margin = _number(info.get("operatingMargins"))
    latest_quarter_margin = _latest_operating_margin(symbol)

    summary = info.get("longBusinessSummary") or ""
    summary = " ".join(str(summary).split())

    return {
        "ticker": symbol,
        "name": _text(info.get("longName") or info.get("shortName")),
        "sector": _text(info.get("sector")),
        "industry": _text(info.get("industry")),
        "website": _text(info.get("website")),
        "summary": summary,
        "price": price,
        "change": change,
        "prev_close": _price(prev_close),
        "volume": _compact(volume),
        "avg_volume": _compact(info.get("averageVolume")),
        "market_cap": _compact(info.get("marketCap"), prefix="$"),
        "day_range": _range(day_low, day_high),
        "range_52w": _range(info.get("fiftyTwoWeekLow"), info.get("fiftyTwoWeekHigh")),
        "rsi": _plain(rsi),
        "ma_50": _price(ma50),
        "ma_200": _price(ma200),
        "beta": _plain(info.get("beta")),
        "short_float": _ratio_percent(info.get("shortPercentOfFloat")),
        "pe": _plain(info.get("trailingPE")),
        "forward_pe": _plain(info.get("forwardPE")),
        "eps": _price(info.get("trailingEps")),
        "forward_eps": _price(info.get("forwardEps")),
        "gross_margin": _ratio_percent(info.get("grossMargins")),
        "operating_margin": _ratio_percent(operating_margin) if operating_margin is not None else (
            f"{latest_quarter_margin:.2f}%" if latest_quarter_margin is not None else NA
        ),
        "profit_margin": _ratio_percent(info.get("profitMargins")),
        "revenue": _compact(info.get("totalRevenue"), prefix="$"),
        "dividend_yield": _dividend_yield(info, price),
        "employees": _employees(info.get("fullTimeEmployees")),
        "earnings": earnings or NA,
    }


def _range(low, high) -> str:
    left = _price(low)
    right = _price(high)
    if left == NA and right == NA:
        return NA
    return f"{left} – {right}"


def _employees(value) -> str:
    number = _number(value)
    if number is None:
        return NA
    return f"{int(number):,}"


def _rows(*pairs: tuple[str, str]) -> list[tuple[str, str]]:
    return [(label, value) for label, value in pairs if value and value != NA]


def _card(parent, title: str, rows: list[tuple[str, str]], row: int, column: int, columnspan: int = 1):
    if not rows:
        return None
    card = tk.Frame(
        parent,
        bg=Colors.PANEL,
        highlightbackground=Colors.GRID,
        highlightthickness=1,
    )
    card.grid(row=row, column=column, columnspan=columnspan, sticky="nsew", padx=6, pady=6)

    tk.Label(
        card,
        text=title,
        bg=Colors.PANEL,
        fg=Colors.MUTED,
        font=(Fonts.sans_name, 10, "bold"),
        anchor=tk.W,
    ).pack(fill=tk.X, padx=16, pady=(14, 6))

    for label, value in rows:
        line = tk.Frame(card, bg=Colors.PANEL)
        line.pack(fill=tk.X, padx=16, pady=3)
        tk.Label(
            line,
            text=label,
            bg=Colors.PANEL,
            fg=Colors.MUTED,
            font=(Fonts.sans_name, 12),
            anchor=tk.W,
        ).pack(side=tk.LEFT)
        tk.Label(
            line,
            text=value,
            bg=Colors.PANEL,
            fg=Colors.TEXT,
            font=(Fonts.mono_name, 12),
            anchor=tk.E,
        ).pack(side=tk.RIGHT)

    tk.Frame(card, bg=Colors.PANEL, height=12).pack(fill=tk.X)
    return card


def _section_title(text: str) -> str:
    return text.upper()


def render_snapshot(parent, snapshot: dict) -> None:
    for child in parent.winfo_children():
        child.destroy()

    header = tk.Frame(parent, bg=Colors.BACKGROUND)
    header.pack(fill=tk.X, padx=8, pady=(4, 2))

    title_row = tk.Frame(header, bg=Colors.BACKGROUND)
    title_row.pack(fill=tk.X)
    tk.Label(
        title_row,
        text=snapshot["ticker"],
        bg=Colors.BACKGROUND,
        fg=Colors.TEXT,
        font=(Fonts.mono_name, 28, "bold"),
        anchor=tk.W,
    ).pack(side=tk.LEFT)
    meta = "  ·  ".join(
        part for part in (snapshot["sector"], snapshot["industry"]) if part != NA
    )
    if meta:
        tk.Label(
            title_row,
            text=meta,
            bg=Colors.BACKGROUND,
            fg=Colors.MUTED,
            font=(Fonts.sans_name, 12),
            anchor=tk.E,
        ).pack(side=tk.RIGHT, padx=(12, 0))

    if snapshot["name"] != NA:
        tk.Label(
            header,
            text=snapshot["name"],
            bg=Colors.BACKGROUND,
            fg=Colors.TEXT,
            font=(Fonts.sans_name, 14),
            anchor=tk.W,
        ).pack(fill=tk.X, pady=(2, 0))

    price_row = tk.Frame(header, bg=Colors.BACKGROUND)
    price_row.pack(fill=tk.X, pady=(14, 4))
    tk.Label(
        price_row,
        text=_price(snapshot["price"]),
        bg=Colors.BACKGROUND,
        fg=Colors.TEXT,
        font=(Fonts.mono_name, 26, "bold"),
        anchor=tk.W,
    ).pack(side=tk.LEFT)

    change = snapshot["change"]
    if change is not None:
        color = Colors.BULL if change >= 0 else Colors.BEAR
        tk.Label(
            price_row,
            text=_signed_percent(change),
            bg=Colors.BACKGROUND,
            fg=color,
            font=(Fonts.mono_name, 18, "bold"),
            anchor=tk.W,
        ).pack(side=tk.LEFT, padx=(14, 0), pady=(6, 0))

    if snapshot["prev_close"] != NA:
        tk.Label(
            header,
            text=f"Prior close {snapshot['prev_close']}",
            bg=Colors.BACKGROUND,
            fg=Colors.MUTED,
            font=(Fonts.sans_name, 11),
            anchor=tk.W,
        ).pack(fill=tk.X)

    grid = tk.Frame(parent, bg=Colors.BACKGROUND)
    grid.pack(fill=tk.X, pady=(10, 0))
    grid.columnconfigure(0, weight=1)
    grid.columnconfigure(1, weight=1)

    _card(
        grid,
        _section_title("Trading"),
        _rows(
            ("Volume", snapshot["volume"]),
            ("Avg volume", snapshot["avg_volume"]),
            ("Market cap", snapshot["market_cap"]),
            ("Day range", snapshot["day_range"]),
            ("52-week range", snapshot["range_52w"]),
        ),
        0,
        0,
    )
    _card(
        grid,
        _section_title("Technical"),
        _rows(
            ("RSI (14)", snapshot["rsi"]),
            ("50-day MA", snapshot["ma_50"]),
            ("200-day MA", snapshot["ma_200"]),
            ("Beta", snapshot["beta"]),
            ("Short % float", snapshot["short_float"]),
        ),
        0,
        1,
    )
    _card(
        grid,
        _section_title("Fundamentals"),
        _rows(
            ("Trailing P/E", snapshot["pe"]),
            ("Forward P/E", snapshot["forward_pe"]),
            ("EPS (ttm)", snapshot["eps"]),
            ("Forward EPS", snapshot["forward_eps"]),
            ("Revenue (ttm)", snapshot["revenue"]),
            ("Gross margin", snapshot["gross_margin"]),
            ("Operating margin", snapshot["operating_margin"]),
            ("Profit margin", snapshot["profit_margin"]),
        ),
        1,
        0,
    )
    _card(
        grid,
        _section_title("Company"),
        _rows(
            ("Next earnings", snapshot["earnings"]),
            ("Dividend yield", snapshot["dividend_yield"]),
            ("Employees", snapshot["employees"]),
            ("Website", snapshot["website"]),
        ),
        1,
        1,
    )

    if snapshot["summary"]:
        about = tk.Frame(
            parent,
            bg=Colors.PANEL,
            highlightbackground=Colors.GRID,
            highlightthickness=1,
        )
        about.pack(fill=tk.X, padx=6, pady=(6, 8))
        tk.Label(
            about,
            text=_section_title("About"),
            bg=Colors.PANEL,
            fg=Colors.MUTED,
            font=(Fonts.sans_name, 10, "bold"),
            anchor=tk.W,
        ).pack(fill=tk.X, padx=16, pady=(14, 6))
        body = tk.Label(
            about,
            text=snapshot["summary"],
            bg=Colors.PANEL,
            fg=Colors.TEXT,
            font=(Fonts.sans_name, 12),
            anchor=tk.W,
            justify=tk.LEFT,
            wraplength=760,
        )
        body.pack(fill=tk.X, padx=16, pady=(0, 16))

        def _reflow(event, label=body):
            if event.widget is parent:
                label.configure(wraplength=max(event.width - 56, 240))

        parent.bind("<Configure>", _reflow, add="+")


def _scrollable(root):
    canvas = tk.Canvas(root, bg=Colors.BACKGROUND, highlightthickness=0, bd=0)
    scrollbar = ttk.Scrollbar(root, orient=tk.VERTICAL, command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    inner = tk.Frame(canvas, bg=Colors.BACKGROUND)
    window_id = canvas.create_window((0, 0), window=inner, anchor="nw")

    def _on_inner(_event):
        canvas.configure(scrollregion=canvas.bbox("all"))

    def _on_canvas(event):
        canvas.itemconfigure(window_id, width=event.width)

    def _on_wheel(event):
        canvas.yview_scroll(int(-event.delta / 120) or (-1 if event.delta > 0 else 1), "units")

    inner.bind("<Configure>", _on_inner)
    canvas.bind("<Configure>", _on_canvas)
    canvas.bind("<Enter>", lambda _e: canvas.bind_all("<MouseWheel>", _on_wheel))
    canvas.bind("<Leave>", lambda _e: canvas.unbind_all("<MouseWheel>"))
    return inner


def show_snapshot(ticker: str) -> None:
    root = tk.Tk()
    symbol = ticker.strip().upper()
    root.title(f"{symbol} · Snapshot")
    root.geometry("920x740")
    root.minsize(720, 520)
    style_table(root)

    inner = _scrollable(root)
    status = tk.Label(
        inner,
        text=f"Loading {symbol}…",
        bg=Colors.BACKGROUND,
        fg=Colors.TEXT,
        font=(Fonts.sans_name, 16),
        anchor=tk.W,
    )
    status.pack(fill=tk.X, padx=16, pady=20)
    detail = tk.Label(
        inner,
        text="Pulling price, technicals, and fundamentals.",
        bg=Colors.BACKGROUND,
        fg=Colors.MUTED,
        font=(Fonts.sans_name, 12),
        anchor=tk.W,
    )
    detail.pack(fill=tk.X, padx=16)

    def populate(snapshot):
        if not snapshot:
            status.configure(text=f"No data for {symbol}")
            detail.configure(text="Check your connection or .datacache/.")
            return
        render_snapshot(inner, snapshot)

    def on_error(exc):
        status.configure(text=f"Could not load {symbol}", fg=Colors.BEAR)
        detail.configure(text=str(exc), fg=Colors.BEAR)

    run_in_background(root, lambda: collect_snapshot(symbol), populate, on_error=on_error)
    root.mainloop()


def main(ticker: str) -> None:
    show_snapshot(ticker)


if __name__ == "__main__":
    symbol = sys.argv[1].strip().upper() if len(sys.argv) > 1 else input("Enter the stock ticker symbol (e.g., AAPL): ").strip().upper()
    if not symbol:
        print("A ticker symbol is required.")
        sys.exit(1)
    main(symbol)
