import subprocess
import sys
import os
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCREENERS_DIR = os.path.join(PROJECT_ROOT, 'screeners')

def _launch(script_name):
    """Launch a screener script as an independent process."""
    subprocess.Popen([sys.executable, os.path.join(SCREENERS_DIR, script_name)])

def run_earnings_tracker():
    """Runs the earnings tracker application."""
    _launch('earningsTracker.py')

def run_daily_movers():
    """Runs the daily movers application."""
    _launch('dailyMovers.py')

def run_market_heat_map():
    """Runs the market heat map application."""
    _launch('marketHeatMap.py')

def run_sector_analysis():
    """Runs the sector analysis application."""
    _launch('sectorAnalysis.py')

def run_technical_indicators():
    """Runs the technical indicators application."""
    _launch('technicalIndicators.py')

def main():
    """Run all applications in parallel."""
    run_earnings_tracker()
    time.sleep(1)
    run_daily_movers()
    time.sleep(1)
    run_market_heat_map()
    time.sleep(1)
    run_sector_analysis()
    time.sleep(1)
    run_technical_indicators()

if __name__ == "__main__":
    main()