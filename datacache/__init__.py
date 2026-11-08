"""Lightweight shared on-disk cache for Yahoo Finance lookups.

Every tool fetches market data through these wrappers instead of calling
``yfinance`` directly. Results are pickled into a temporary cache folder keyed
by the request, and reused for ``CACHE_TTL_SECONDS`` (default 30 minutes). The
cache lives on disk, so it is shared *across apps* — e.g. the daily movers
screener and a chart launched from it won't re-download the same ticker.

When the network is unavailable, stale cache entries are served even after the
TTL has expired so charts and screeners can still run on the last fetched data.

Public API mirrors the yfinance calls the project uses:

    from datacache import download, ticker_history, ticker_info, ticker_calendar

    data = download("AAPL", period="6mo", interval="1d")
    info = ticker_info("AAPL")

Set the ``TRADING_DATA_CACHE_TTL`` env var (seconds) to change the window, or
``TRADING_DATA_CACHE_DIR`` to relocate the folder. Call :func:`clear_cache` to
wipe it, or :func:`purge_expired` to drop only stale entries.
"""

from __future__ import annotations

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


def _read(key, *, allow_stale=False):
    """Return cached value if present (and fresh unless allow_stale), else None."""
    path = _key_to_path(key)
    try:
        age = time.time() - os.path.getmtime(path)
        if age > CACHE_TTL_SECONDS and not allow_stale:
            return None
        with open(path, "rb") as handle:
            return pickle.load(handle), age
    except (OSError, pickle.UnpicklingError, EOFError, ValueError):
        return None


def _read_value(key, *, allow_stale=False):
    """Return cached payload only (no age), or None."""
    result = _read(key, allow_stale=allow_stale)
    if result is None:
        return None
    value, _age = result
    return value


def cache_age(key) -> float | None:
    """Return cache age in seconds, or None if the entry is missing."""
    result = _read(key, allow_stale=True)
    if result is None:
        return None
    _value, age = result
    return age


def _online(timeout: float = 1.5) -> bool:
    import socket

    for host, port in (("1.1.1.1", 443), ("8.8.8.8", 53)):
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except OSError:
            continue
    return False


def _cached_fetch(key, fetch_fn, *, allow_stale=True):
    """Return fresh cache, fetch live data, or fall back to stale cache offline."""
    fresh = _read_value(key)
    if fresh is not None:
        return fresh

    stale = _read_value(key, allow_stale=True) if allow_stale else None
    if stale is not None and not _online():
        return stale

    try:
        data = fetch_fn()
    except Exception as exc:
        if allow_stale and stale is not None and _is_network_error(exc):
            return stale
        if allow_stale and stale is not None:
            return stale
        raise

    if not _is_empty(data):
        _write(key, data)
    return data


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


def _is_network_error(exc):
    try:
        import requests
    except ImportError:
        requests = None

    try:
        from urllib.error import URLError
    except ImportError:
        URLError = ()

    if requests is not None and isinstance(exc, requests.RequestException):
        return True
    if isinstance(exc, (URLError, TimeoutError, ConnectionError)):
        return True

    try:
        from curl_cffi.requests.exceptions import RequestException as CurlRequestException
    except ImportError:
        CurlRequestException = ()

    if isinstance(exc, CurlRequestException):
        return True

    if isinstance(exc, OSError):
        err = getattr(exc, "errno", None)
        if err in {50, 51, 52, 53, 54, 60, 61, 64, 65, 101, 110, 111, 113}:
            return True

    cause = getattr(exc, "__cause__", None)
    if cause is not None and cause is not exc:
        return _is_network_error(cause)
    return False


def read_cached(key: str, *, allow_stale: bool = False):
    """Return a cached payload if present (fresh, or stale when allow_stale=True)."""
    return _read_value(key, allow_stale=allow_stale)


def has_cached_data() -> bool:
    """True when the on-disk cache folder contains at least one entry."""
    try:
        return any(name.endswith(".pkl") for name in os.listdir(CACHE_DIR))
    except OSError:
        return False


def download(tickers, **kwargs):
    """Cached wrapper around ``yfinance.download``."""
    key = "download|" + _normalize(tickers) + "|" + _normalize(kwargs)

    def fetch():
        import yfinance as yf

        fetch_kwargs = {**kwargs, "progress": kwargs.get("progress", False)}
        return yf.download(tickers, **fetch_kwargs)

    return _cached_fetch(key, fetch)


def ticker_history(ticker, **kwargs):
    """Cached wrapper around ``yfinance.Ticker(ticker).history(**kwargs)``."""
    key = "history|" + _normalize(ticker) + "|" + _normalize(kwargs)

    def fetch():
        import yfinance as yf

        return yf.Ticker(ticker).history(**kwargs)

    return _cached_fetch(key, fetch)


def ticker_info(ticker):
    """Cached wrapper around ``yfinance.Ticker(ticker).info``."""
    key = "info|" + _normalize(ticker)

    def fetch():
        import yfinance as yf

        return yf.Ticker(ticker).info

    return _cached_fetch(key, fetch)


def ticker_calendar(ticker):
    """Cached wrapper around ``yfinance.Ticker(ticker).calendar``."""
    key = "calendar|" + _normalize(ticker)

    def fetch():
        import yfinance as yf

        return yf.Ticker(ticker).calendar

    return _cached_fetch(key, fetch)


def ticker_quarterly_financials(ticker):
    """Cached wrapper around ``yfinance.Ticker(ticker).quarterly_financials``."""
    key = "qfin|" + _normalize(ticker)

    def fetch():
        import yfinance as yf

        return yf.Ticker(ticker).quarterly_financials

    return _cached_fetch(key, fetch)


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
    "has_cached_data",
    "read_cached",
    "cache_age",
    "purge_expired",
    "clear_cache",
]
