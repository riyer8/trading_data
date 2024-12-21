import subprocess
import sys
import os
import time

def run_earnings_tracker():
    """Runs the earnings tracker application."""
    earnings_tracker_script = os.path.join(os.getcwd(), 'earningsTracker.py')
    subprocess.Popen([sys.executable, earnings_tracker_script])

def run_daily_movers():
    """Runs the daily movers application."""
    daily_movers_script = os.path.join(os.getcwd(), 'dailyMovers.py')
    subprocess.Popen([sys.executable, daily_movers_script])

def run_market_heat_map():
    """Runs the market heat map application."""
    market_heat_map = os.path.join(os.getcwd(), 'marketHeatMap.py')
    subprocess.Popen([sys.executable, market_heat_map])

def run_sector_analysis():
    """Runs sector analysis application."""
    sector_analysis = os.path.join(os.getcwd(), 'sectorAnalysis.py')
    subprocess.Popen([sys.executable, sector_analysis])

def run_technical_indicators():
    """Runs sector analysis application."""
    tech_indicators = os.path.join(os.getcwd(), 'technicalIndicators.py')
    subprocess.Popen([sys.executable, tech_indicators])

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