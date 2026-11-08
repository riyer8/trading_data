from __future__ import annotations

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ui.bootstrap  # noqa: F401

import datacache
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

from ui.theme import Colors, Fonts, apply_chart_theme, set_window_title

from portfolio.portfolioInfo import (
    SEMICONDUCTOR_COMPANIES, TECHNOLOGY_COMPANIES,
    CONSUMER_DISCRETIONARY_COMPANIES, ENERGY_COMPANIES, HEALTHCARE_COMPANIES,
    FINANCIAL_COMPANIES, CONSUMER_STAPLES_COMPANIES,
    COMMUNICATION_COMPANIES, UTILITIES_COMPANIES, MATERIALS_COMPANIES,
    TRAVEL_COMPANIES
)

SECTORS = {
    'Semiconductor': SEMICONDUCTOR_COMPANIES,
    'Technology': TECHNOLOGY_COMPANIES,
    'Consumer Discretionary': CONSUMER_DISCRETIONARY_COMPANIES,
    'Energy': ENERGY_COMPANIES,
    'Healthcare': HEALTHCARE_COMPANIES,
    'Financial': FINANCIAL_COMPANIES,
    'Consumer Staples': CONSUMER_STAPLES_COMPANIES,
    'Communication Services': COMMUNICATION_COMPANIES,
    'Utilities': UTILITIES_COMPANIES,
    'Materials': MATERIALS_COMPANIES,
    'Travels': TRAVEL_COMPANIES
}

def calculate_sector_performance(tickers):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    data = datacache.download(tickers, start=start_date, end=end_date)
    if data is None or data.empty:
        return None, None, None

    fields = data.columns.get_level_values(0) if isinstance(data.columns, pd.MultiIndex) else data.columns
    price_field = 'Adj Close' if 'Adj Close' in fields else 'Close'

    adj_close = data[price_field].copy()
    volume = data['Volume'].copy()

    adj_close = adj_close.dropna(axis=1, how='all')
    volume = volume.dropna(axis=1, how='all')
    if adj_close.empty or len(adj_close) < 2:
        return None, None, None

    first_price = adj_close.iloc[0]
    last_price = adj_close.iloc[-1]
    price_change = (last_price - first_price) / first_price.replace(0, pd.NA) * 100
    avg_price_change = float(price_change.mean(skipna=True))

    first_volume = volume.iloc[0]
    last_volume = volume.iloc[-1]
    volume_change = (last_volume - first_volume) / first_volume.replace(0, pd.NA) * 100
    avg_volume_change = float(volume_change.mean(skipna=True))

    stock_price_change = adj_close.sum(axis=1)
    if len(stock_price_change) < 2 or stock_price_change.iloc[0] == 0:
        stock_price_change_pct = 0.0
    else:
        stock_price_change_pct = float(
            (stock_price_change.iloc[-1] - stock_price_change.iloc[0])
            / stock_price_change.iloc[0]
            * 100
        )

    return avg_price_change, avg_volume_change, stock_price_change_pct


def compute_sector_data():
    sector_performance = {}
    sector_volume_change = {}
    sector_sum_price_change = {}

    for sector, tickers in SECTORS.items():
        price_performance, volume_performance, sum_price_performance = calculate_sector_performance(tickers)
        if price_performance is None:
            continue
        sector_performance[sector] = price_performance
        sector_volume_change[sector] = volume_performance
        sector_sum_price_change[sector] = sum_price_performance

    if not sector_performance:
        return None, None, None

    performance_df = pd.DataFrame.from_dict(sector_performance, orient='index', columns=['Performance'])
    volume_df = pd.DataFrame.from_dict(sector_volume_change, orient='index', columns=['Volume Change'])
    sum_price_df = pd.DataFrame.from_dict(sector_sum_price_change, orient='index', columns=['Stock Price Change'])
    return performance_df, volume_df, sum_price_df


def add_labels(ax):
    for patch in ax.patches:
        height = patch.get_height()
        offset = 6 if height >= 0 else -12
        ax.annotate(f'{height:+.2f}%',
                    (patch.get_x() + patch.get_width() / 2., height),
                    ha='center', va='center', fontsize=Fonts.ANNOTATION,
                    fontweight='bold', fontfamily='monospace', color=Colors.TEXT,
                    xytext=(0, offset), textcoords='offset points')


def plot_graph(df, criteria, y_label, title, note):
    fig, ax = plt.subplots(figsize=(8.5, 5.2))
    set_window_title(fig, title)
    sorted_df = df.sort_values(by=criteria, ascending=False)
    bar_colors = [Colors.BULL if v >= 0 else Colors.BEAR for v in sorted_df[criteria]]
    sorted_df.plot(kind='bar', legend=False, ax=ax, color=bar_colors,
                   edgecolor=Colors.BACKGROUND, width=0.7)
    ax.axhline(0, color=Colors.MUTED, linewidth=0.8)
    ax.grid(axis='x', visible=False)
    ax.set_title(title, pad=18)
    ax.text(0.0, 1.02, note, transform=ax.transAxes, color=Colors.MUTED, fontsize=Fonts.TICK, va="bottom", clip_on=False)
    ax.set_ylabel(y_label)
    ax.set_xlabel('')
    ax.tick_params(axis='x', rotation=45)
    for label in ax.get_xticklabels():
        label.set_ha('right')
    add_labels(ax)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    return fig


def plot_all():
    apply_chart_theme()
    print("Loading sector data…")
    performance_df, volume_df, sum_price_df = compute_sector_data()
    if performance_df is None:
        fig, ax = plt.subplots(figsize=(8, 4))
        set_window_title(fig, "Sector Analysis")
        ax.axis("off")
        ax.text(
            0.5, 0.5,
            "No sector data loaded.\nCheck your connection or .datacache/.",
            ha="center", va="center", color=Colors.TEXT, fontsize=12,
        )
        plt.show()
        return

    plot_graph(
        performance_df, 'Performance', 'Average % change',
        'Average price change by sector',
        'Last month. Each bar is the average move of the stocks in that sector.',
    )
    plot_graph(
        volume_df, 'Volume Change', 'Average volume change',
        'Volume change by sector',
        'Last month. This is how much trading activity changed, not the share price.',
    )
    plot_graph(
        sum_price_df, 'Stock Price Change', 'Combined % change',
        'Combined price change by sector',
        'Last month. Adds the sector\'s prices together, then measures that total.',
    )
    plt.show()


if __name__ == "__main__":
    plot_all()
