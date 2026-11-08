"""Shared data helpers for charts and screeners."""

from __future__ import annotations

import math
from datetime import date, datetime

import pandas as pd


def flatten_columns(data: pd.DataFrame) -> pd.DataFrame:
    """Flatten yfinance MultiIndex columns to a single level."""
    if isinstance(data.columns, pd.MultiIndex):
        data = data.copy()
        data.columns = data.columns.get_level_values(0)
    return data


def to_scalar(value):
    """Coerce a pandas/numpy cell to a plain Python scalar."""
    if value is None:
        return None
    if isinstance(value, pd.Series):
        if value.empty:
            return None
        value = value.iloc[-1]
    if hasattr(value, "item"):
        try:
            return value.item()
        except (ValueError, TypeError):
            pass
    return value


def safe_pct_change(current, previous) -> float | None:
    if current is None or previous is None:
        return None
    try:
        previous = float(previous)
        current = float(current)
    except (TypeError, ValueError):
        return None
    if previous == 0:
        return None
    return ((current - previous) / previous) * 100


def format_metric(value, fmt: str = "{:.2f}", na: str = "N/A") -> str:
    if value is None or value == na:
        return na
    try:
        number = float(value)
        if math.isnan(number) or math.isinf(number):
            return na
        return fmt.format(number)
    except (TypeError, ValueError):
        return na


def format_percent(value, na: str = "N/A") -> str:
    text = format_metric(value, "{:.2f}", na=na)
    return text if text == na else f"{text}%"


def _coerce_date(value) -> date | None:
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if hasattr(value, "date"):
        try:
            return value.date()
        except Exception:
            pass
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value[:10]).date()
        except ValueError:
            return None
    return None


def earnings_dates(calendar) -> list[date]:
    """Normalize yfinance calendar earnings to sorted date objects."""
    if calendar is None:
        return []

    raw = None
    if isinstance(calendar, dict):
        raw = calendar.get("Earnings Date") or calendar.get("EarningsDate")
    elif isinstance(calendar, pd.DataFrame):
        if "Earnings Date" in calendar.index:
            raw = calendar.loc["Earnings Date"]
        elif "Earnings Date" in calendar.columns:
            raw = calendar["Earnings Date"]
    elif hasattr(calendar, "get"):
        raw = calendar.get("Earnings Date")

    if raw is None:
        return []

    if isinstance(raw, pd.Series):
        items = raw.tolist()
    elif isinstance(raw, (list, tuple)):
        items = list(raw)
    else:
        items = [raw]

    dates: list[date] = []
    for item in items:
        parsed = _coerce_date(item)
        if parsed is not None:
            dates.append(parsed)
    return sorted(set(dates))


def next_earnings_date(calendar, today: date | None = None) -> date | None:
    today = today or date.today()
    upcoming = [item for item in earnings_dates(calendar) if item >= today]
    if upcoming:
        return upcoming[0]
    dates = earnings_dates(calendar)
    return dates[0] if dates else None


def find_financial_row(financials: pd.DataFrame, *names: str):
    for name in names:
        if name in financials.index:
            return financials.loc[name]
    lowered = {str(index).lower(): index for index in financials.index}
    for name in names:
        key = name.lower()
        if key in lowered:
            return financials.loc[lowered[key]]
    return None
