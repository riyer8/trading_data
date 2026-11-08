from __future__ import annotations

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ui.bootstrap  # noqa: F401

import matplotlib.pyplot as plt
import pandas as pd

import datacache
from ui.theme import Colors, Fonts, apply_chart_theme, style_legend, set_window_title
from ui.data_utils import find_financial_row

MAX_QUARTERS = 12


def get_financial_data(ticker):
    financials = datacache.ticker_quarterly_financials(ticker)

    if financials is None or financials.empty:
        print(f"Data unavailable for {ticker}.")
        return None, None

    revenue = find_financial_row(financials, 'Total Revenue', 'Total Revenues')
    operating_income = find_financial_row(financials, 'Operating Income', 'Operating Income')
    if revenue is None or operating_income is None:
        print(f"Operating margin data unavailable for {ticker}.")
        return None, None

    operating_margin = (operating_income / revenue) * 100

    # Data-driven: sort chronologically, drop quarters without data, and keep
    # the most recent ones. No hardcoded quarter dates so it works per-ticker.
    operating_margin = operating_margin.sort_index().dropna()
    operating_margin = operating_margin.iloc[-MAX_QUARTERS:]

    if operating_margin.empty:
        print(f"No usable operating margin data for {ticker}.")
        return None, None

    quarters = list(operating_margin.index)
    values = list(operating_margin.values)
    return values, quarters


def plot_operating_margins(ticker):
    operating_margin_percentage, quarters = get_financial_data(ticker)

    if operating_margin_percentage is None:
        return

    apply_chart_theme()
    fig, ax = plt.subplots(figsize=(11, 6))
    set_window_title(fig, f"{ticker.upper()} · Operating Margin")

    ax.plot(quarters, operating_margin_percentage, color=Colors.ACCENT_4,
            marker='o', markersize=5, linewidth=2.4, label=ticker.upper())

    for quarter, value in zip(quarters, operating_margin_percentage):
        ax.annotate(f"{value:.1f}%", (quarter, value),
                    textcoords="offset points", xytext=(0, 12), ha='center',
                    fontsize=Fonts.ANNOTATION, fontweight='bold',
                    fontfamily='monospace', color=Colors.TEXT)

    tick_labels = [f"{q.year} Q{(q.month - 1) // 3 + 1}" for q in quarters]
    ax.set_xticks(quarters)
    ax.set_xticklabels(tick_labels, rotation=20, ha='right')

    ax.set_title(f"{ticker.upper()} operating margin, by quarter", pad=18)
    ax.text(
        0.0, 1.02,
        "Share of sales left after running the business. Higher means more of each dollar stayed as operating profit.",
        transform=ax.transAxes, color=Colors.MUTED, fontsize=Fonts.TICK, va="bottom", clip_on=False,
    )
    ax.set_xlabel("Quarter")
    ax.set_ylabel("Operating margin (%)")
    ax.margins(x=0.03, y=0.15)
    style_legend(ax, loc='upper left')

    fig.tight_layout(rect=(0, 0, 1, 0.94))
    plt.show()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        ticker_input = sys.argv[1].strip().upper()
    else:
        ticker_input = input("Enter a valid stock ticker symbol: ").strip().upper()
    plot_operating_margins(ticker_input)
