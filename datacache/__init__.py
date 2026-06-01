"""Lightweight shared on-disk cache for Yahoo Finance lookups.

Every tool fetches market data through these wrappers instead of calling
``yfinance`` directly. Results are pickled into a temporary cache folder keyed
by the request, and reused for ``CACHE_TTL_SECONDS`` (default 30 minutes). The
cache lives on disk, so it is shared *across apps* — e.g. the daily movers
screener and a chart launched from it won't re-download the same ticker.

Public API mirrors the yfinance calls the project uses:

    from datacache import download, ticker_history, ticker_info, ticker_calendar

    data = download("AAPL", period="6mo", interval="1d")
    info = ticker_info("AAPL")

Set the ``TRADING_DATA_CACHE_TTL`` env var (seconds) to change the window, or
``TRADING_DATA_CACHE_DIR`` to relocate the folder. Call :func:`clear_cache` to
wipe it, or :func:`purge_expired` to drop only stale entries.
"""

import hashlib
import os
import pickle
import time

# 30 minutes by default; override with TRADING_DATA_CACHE_TTL (in seconds).
CACHE_TTL_SECONDS = int(os.environ.get("TRADING_DATA_CACHE_TTL", 30 * 60))

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.environ.get(
    "TRADING_DATA_CACHE_DIR", os.path.join(_PROJECT_ROOT, ".datacache")
)


def _key_to_path(key):
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:32]
    return os.path.join(CACHE_DIR, f"{digest}.pkl")


def _normalize(value):
    """Stable string form for cache keys (handles lists, dates, kwargs)."""
    if isinstance(value, (list, tuple)):
        return ",".join(sorted(_normalize(v) for v in value))
    if isinstance(value, dict):
        return ",".join(f"{k}={_normalize(v)}" for k, v in sorted(value.items()))
    return str(value)


def _read(key):
    """Return cached value if present and fresh, else None."""
    path = _key_to_path(key)
    try:
        age = time.time() - os.path.getmtime(path)
        if age > CACHE_TTL_SECONDS:
            return None
        with open(path, "rb") as handle:
            return pickle.load(handle)
    except (OSError, pickle.UnpicklingError, EOFError, ValueError):
        return None


def _write(key, value):
    """Atomically persist a value so parallel apps never read a half-written file."""
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        path = _key_to_path(key)
        tmp = f"{path}.{os.getpid()}.tmp"
        with open(tmp, "wb") as handle:
            pickle.dump(value, handle, protocol=pickle.HIGHEST_PROTOCOL)
        os.replace(tmp, path)  # atomic on the same filesystem
    except (OSError, pickle.PicklingError):
        # Caching is best-effort; never let a cache failure break a fetch.
        pass


def _is_empty(value):
    """True for results not worth caching (None / empty frame / empty dict)."""
    if value is None:
        return True
    if hasattr(value, "empty"):
        return bool(value.empty)
    if isinstance(value, (dict, list, tuple)):
        return len(value) == 0
    return False


def download(tickers, **kwargs):
    """Cached wrapper around ``yfinance.download``."""
    key = "download|" + _normalize(tickers) + "|" + _normalize(kwargs)
    cached = _read(key)
    if cached is not None:
        return cached

    import yfinance as yf
    data = yf.download(tickers, **kwargs)
    if not _is_empty(data):
        _write(key, data)
    return data


def ticker_history(ticker, **kwargs):
    """Cached wrapper around ``yfinance.Ticker(ticker).history(**kwargs)``."""
    key = "history|" + _normalize(ticker) + "|" + _normalize(kwargs)
    cached = _read(key)
    if cached is not None:
        return cached

    import yfinance as yf
    data = yf.Ticker(ticker).history(**kwargs)
    if not _is_empty(data):
        _write(key, data)
    return data


def ticker_info(ticker):
    """Cached wrapper around ``yfinance.Ticker(ticker).info``."""
    key = "info|" + _normalize(ticker)
    cached = _read(key)
    if cached is not None:
        return cached

    import yfinance as yf
    info = yf.Ticker(ticker).info
    if not _is_empty(info):
        _write(key, info)
    return info


def ticker_calendar(ticker):
    """Cached wrapper around ``yfinance.Ticker(ticker).calendar``."""
    key = "calendar|" + _normalize(ticker)
    cached = _read(key)
    if cached is not None:
        return cached

    import yfinance as yf
    calendar = yf.Ticker(ticker).calendar
    if not _is_empty(calendar):
        _write(key, calendar)
    return calendar


def ticker_quarterly_financials(ticker):
    """Cached wrapper around ``yfinance.Ticker(ticker).quarterly_financials``."""
    key = "qfin|" + _normalize(ticker)
    cached = _read(key)
    if cached is not None:
        return cached

    import yfinance as yf
    financials = yf.Ticker(ticker).quarterly_financials
    if not _is_empty(financials):
        _write(key, financials)
    return financials


def purge_expired():
    """Delete only cache entries older than the TTL. Returns count removed."""
    removed = 0
    try:
        entries = os.listdir(CACHE_DIR)
    except OSError:
        return 0
    now = time.time()
    for name in entries:
        path = os.path.join(CACHE_DIR, name)
        try:
            if now - os.path.getmtime(path) > CACHE_TTL_SECONDS:
                os.remove(path)
                removed += 1
        except OSError:
            continue
    return removed


def clear_cache():
    """Delete the entire cache folder. Returns count removed."""
    removed = 0
    try:
        entries = os.listdir(CACHE_DIR)
    except OSError:
        return 0
    for name in entries:
        try:
            os.remove(os.path.join(CACHE_DIR, name))
            removed += 1
        except OSError:
            continue
    return removed


__all__ = [
    "CACHE_TTL_SECONDS",
    "CACHE_DIR",
    "download",
    "ticker_history",
    "ticker_info",
    "ticker_calendar",
    "ticker_quarterly_financials",
    "purge_expired",
    "clear_cache",
]
