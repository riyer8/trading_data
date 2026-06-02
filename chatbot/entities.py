"""Merge tickers / lookback from conversation text, LLM entities, and action args."""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field
from functools import lru_cache

from chatbot.tool_specs import TOOL_SPECS

TICKER_RE = re.compile(r"\b([A-Z]{1,5}(?:,[A-Z]{1,5})*)\b")
CONTEXT_TICKER_RE = re.compile(
    r"\b(?:to|for|on|of|with|symbol|ticker)\s+([A-Za-z]{1,5})\b",
    re.I,
)
LOOKBACK_RE = re.compile(r"\b(\d+)\s*(?:months?|mo)\b", re.I)
LOOKBACK_ONLY_RE = re.compile(r"\b(?:lookback|period|range)\s*(?:of\s*)?(\d+)\b", re.I)

_NON_TICKERS = frozenset(
    {
        "A", "I", "OR", "TO", "FOR", "ALL", "THE", "AND", "OPEN", "CLOSE",
        "VWAP", "RSI", "EPS", "MA", "PE", "UI", "API", "SYS", "ASST", "YOU",
        "ME", "SHOW", "CHART", "CHARTS", "STOCK", "STOCKS", "WHAT", "MOVED",
        "TODAY", "FIND", "LIKE", "USE", "HOW", "MANY", "MONTHS", "MONTH",
        "LOOKBACK", "PERIOD", "SCREENER", "SCREENERS", "TOOLS", "TOOL", "DATA",
        "HELP", "NEED", "WANT", "VIEW", "SEE", "DAILY", "MOVERS", "ASK", "TYPE",
        "WITH", "FROM", "INTO", "ABOUT", "THAT", "THIS", "THAN", "THEN", "WHEN",
        "YOUR", "CAN", "RUN", "APP", "APPS", "WAS", "HAS", "HAD", "ARE", "WERE",
        "BE", "AM", "IS", "IT", "AT", "IN", "AN", "AS", "DO", "DID", "GET",
        "GOT", "LET", "PUT", "SAY", "SAW", "TRY", "YES", "NOT", "BUT", "OUT",
        "OFF", "UP", "DOWN", "NEW", "OLD", "BIG", "TOP", "LOW", "HIGH", "WILL",
        "LAUNCH", "PER", "MY", "OF", "USE", "MANY", "SHOULD",
    }
)

_COMMON_TYPOS = {
    "APPL": "AAPL",
    "GOOG": "GOOGL",
    "AMZN": "AMZN",
}

# Longer phrases first — "stock chart" must win over generic chart-adjacent tools.
_INTENT_MODULES: list[tuple[tuple[str, ...], str]] = [
    (("stock chart", "stockchart", "candlestick", "candlesticks"), "charts.stockChart"),
    (("open single ticker", "single ticker app"), "launchers.openSingleTickerApp"),
    (("vwap",), "charts.vwap"),
    (("rsi",), "charts.rsi_trend"),
    (("ema", "moving average"), "charts.ema"),
    (("daily mover", "daily movers", "what moved", "movers"), "screeners.dailyMovers"),
    (("heat map", "heatmap"), "screeners.marketHeatMap"),
    (("sector",), "screeners.sectorAnalysis"),
    (("technical indicator", "technical indicators"), "screeners.technicalIndicators"),
    (("earnings",), "screeners.earningsTracker"),
    (("correlat", "similar stocks", "stocks like"), "screeners.correlation"),
    (("movement", "days of movement"), "screeners.daysOfMovement"),
    (("market cap", "marketcap"), "fundamentals.marketcap"),
    (("operating margin", "operating dollar"), "fundamentals.operatingdollars"),
    (("eps",), "fundamentals.eps"),
    (("all screener", "all screeners", "all dashboard", "open everything"), "launchers.openAllTickerApps"),
]

_MODULE_LABELS = {
    "charts.stockChart": "Stock chart",
    "charts.vwap": "VWAP",
    "charts.rsi_trend": "RSI",
    "charts.ema": "EMA",
    "launchers.openSingleTickerApp": "Ticker charts bundle",
}


@dataclass
class ExtractedEntities:
    tickers: list[str] = field(default_factory=list)
    lookback_months: int | None = None


@lru_cache(maxsize=1)
def known_tickers() -> frozenset[str]:
    try:
        from portfolio.portfolioInfo import MY_TICKERS

        return frozenset(MY_TICKERS)
    except Exception:
        return frozenset()


def normalize_ticker(symbol: str, *, fuzzy: bool = True) -> str:
    cleaned = symbol.strip().upper()
    if not cleaned:
        return cleaned
    if cleaned in _COMMON_TYPOS:
        return _COMMON_TYPOS[cleaned]
    universe = known_tickers()
    if cleaned in universe:
        return cleaned
    if fuzzy and len(cleaned) >= 3 and universe:
        match = difflib.get_close_matches(cleaned, list(universe), n=1, cutoff=0.86)
        if match:
            return match[0]
    return cleaned


def _is_ticker(token: str) -> bool:
    symbol = token.strip().upper()
    return bool(symbol) and symbol.isalpha() and symbol not in _NON_TICKERS


def extract_tickers_from_text(text: str) -> list[str]:
    found: list[str] = []
    for match in CONTEXT_TICKER_RE.finditer(text):
        symbol = normalize_ticker(match.group(1))
        if _is_ticker(symbol):
            found.append(symbol)
    for match in TICKER_RE.finditer(text.upper()):
        for part in match.group(1).split(","):
            symbol = normalize_ticker(part.strip())
            if _is_ticker(symbol):
                found.append(symbol)
    return list(dict.fromkeys(found))


def extract_lookback_from_text(text: str) -> int | None:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.isdigit():
            value = int(stripped)
            if 1 <= value <= 120:
                return value
    match = LOOKBACK_RE.search(text) or LOOKBACK_ONLY_RE.search(text)
    return int(match.group(1)) if match else None


def gather_user_messages(history: list[dict[str, str]] | None, user_message: str) -> str:
    parts = [user_message]
    if history:
        for message in history[-12:]:
            if message.get("role") == "user":
                parts.append(message.get("content", ""))
    return "\n".join(part for part in parts if part)


def tickers_from_action_args(args: list[str]) -> list[str]:
    found: list[str] = []
    for arg in args:
        if arg.isdigit():
            continue
        for part in arg.split(","):
            symbol = normalize_ticker(part.strip())
            if _is_ticker(symbol):
                found.append(symbol)
    return list(dict.fromkeys(found))


def resolve_entities(
    context_text: str,
    llm_entities: ExtractedEntities | None = None,
    action_args: list[str] | None = None,
    *,
    user_text: str | None = None,
) -> ExtractedEntities:
    ticker_source = user_text if user_text is not None else context_text
    tickers = extract_tickers_from_text(ticker_source)
    lookback = extract_lookback_from_text(context_text)

    if llm_entities:
        for symbol in llm_entities.tickers:
            sym = normalize_ticker(symbol)
            if _is_ticker(sym) and sym not in tickers:
                tickers.append(sym)
        if llm_entities.lookback_months is not None:
            lookback = llm_entities.lookback_months

    for symbol in tickers_from_action_args(action_args or []):
        if symbol not in tickers:
            tickers.append(symbol)

    return ExtractedEntities(tickers=tickers, lookback_months=lookback)


def gather_conversation_context(
    history: list[dict[str, str]] | None,
    user_message: str,
) -> str:
    """User + assistant messages so follow-ups like '5' keep prior intent."""
    parts = [user_message]
    if history:
        for message in history[-12:]:
            parts.append(message.get("content", ""))
    return "\n".join(part for part in parts if part)


def gather_user_context(history: list[dict[str, str]] | None, user_message: str) -> str:
    return gather_conversation_context(history, user_message)


def infer_modules_from_context(context_text: str, rag_modules: list[str]) -> list[str]:
    text = context_text.lower()
    scored: list[tuple[int, str]] = []
    for keywords, module in _INTENT_MODULES:
        for keyword in keywords:
            if keyword in text:
                scored.append((len(keyword), module))

    scored.sort(key=lambda item: item[0], reverse=True)
    modules: list[str] = []
    for _, module in scored:
        if module not in modules:
            modules.append(module)

    for module in rag_modules:
        if module and module not in modules:
            modules.append(module)
    return modules


def infer_module(user_message: str, rag_modules: list[str]) -> str | None:
    modules = infer_modules_from_context(user_message, rag_modules)
    return modules[0] if modules else None


def module_label(module: str) -> str:
    return _MODULE_LABELS.get(module, module.rsplit(".", 1)[-1])


def missing_requirement(module: str, entities: ExtractedEntities) -> str | None:
    spec = TOOL_SPECS.get(module)
    if spec is None:
        return None
    if spec.min_tickers and len(entities.tickers) < spec.min_tickers:
        if spec.min_tickers == 1:
            return "Which ticker symbol should I use?"
        return f"Which ticker symbols should I use? I need {spec.min_tickers}."
    if spec.needs_lookback_months and entities.lookback_months is None:
        return "How many months of lookback should I use?"
    return None


def build_launch_args(module: str, entities: ExtractedEntities) -> list[str]:
    if not entities.tickers and module != "fundamentals.eps":
        spec = TOOL_SPECS.get(module)
        if spec and spec.min_tickers:
            return []

    tickers = [normalize_ticker(t) for t in entities.tickers]

    if module == "launchers.openSingleTickerApp":
        if not tickers or entities.lookback_months is None:
            return []
        return [",".join(tickers), str(entities.lookback_months)]

    if module == "fundamentals.eps":
        return [",".join(tickers)] if tickers else []

    spec = TOOL_SPECS.get(module)
    if spec and spec.min_tickers:
        if module == "charts.stockChart":
            if entities.lookback_months is None:
                return []
            return [tickers[0], str(entities.lookback_months)]
        return [tickers[0]]

    return []


def normalize_action_args(module: str, args: list[str]) -> list[str]:
    normalized: list[str] = []
    for arg in args:
        if arg.isdigit():
            normalized.append(arg)
            continue
        parts = [normalize_ticker(part.strip()) for part in arg.split(",") if part.strip()]
        normalized.append(",".join(parts))
    return normalized
