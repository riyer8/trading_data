"""Which CLI arguments each module needs before it can be launched."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModuleSpec:
    min_tickers: int = 0
    needs_lookback_months: bool = False


# Keys are ``python -m`` module paths from the README.
TOOL_SPECS: dict[str, ModuleSpec] = {
    "charts.vwap": ModuleSpec(min_tickers=1),
    "charts.ema": ModuleSpec(min_tickers=1),
    "charts.rsi_trend": ModuleSpec(min_tickers=1),
    "charts.stockChart": ModuleSpec(min_tickers=1, needs_lookback_months=True),
    "fundamentals.operatingdollars": ModuleSpec(min_tickers=1),
    "fundamentals.eps": ModuleSpec(min_tickers=0),
    "launchers.openSingleTickerApp": ModuleSpec(min_tickers=1, needs_lookback_months=True),
    "screeners.correlation": ModuleSpec(min_tickers=1),
    "screeners.daysOfMovement": ModuleSpec(min_tickers=1),
}


def module_requires_args(module: str) -> bool:
    spec = TOOL_SPECS.get(module)
    if spec is None:
        return False
    return spec.min_tickers > 0 or spec.needs_lookback_months
