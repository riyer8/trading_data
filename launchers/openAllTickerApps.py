from __future__ import annotations

import os
import subprocess
import sys
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

import ui.bootstrap  # noqa: F401

_SCREENERS = (
    "screeners.earningsTracker",
    "screeners.dailyMovers",
    "screeners.marketHeatMap",
    "screeners.sectorAnalysis",
    "screeners.technicalIndicators",
)


def _launch(module: str) -> None:
    """Launch a screener module as an independent process."""
    subprocess.Popen(
        [sys.executable, "-m", module],
        cwd=PROJECT_ROOT,
    )


def main() -> None:
    """Run all screener apps in parallel."""
    for index, module in enumerate(_SCREENERS):
        _launch(module)
        if index + 1 < len(_SCREENERS):
            time.sleep(1)


if __name__ == "__main__":
    main()
