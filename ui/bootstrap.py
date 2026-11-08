"""Shared startup side effects for CLI tools (Python 3.9+, Tk warnings)."""

from __future__ import annotations

import os

os.environ.setdefault("TK_SILENCE_DEPRECATION", "1")
