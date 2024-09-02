# Trading Data Tools

This repository houses Python scripts designed to create screeners for analyzing stock market data.

## Overview

### **Correlation**

Identifies the most closely correlated tickers to a target ticker, based on factors like sector, industry, market cap, beta, volume, and liquidity, using data from `yfinance`. Users can specify a minimum desired correlation level, and the tool will display all tickers exceeding that threshold.

### **Daily Movers**

Detects the top-moving stocks from a list of tickers, calculates their percentage changes, and ranks them accordingly using `yfinance`.

### **Earnings Tracker**

Lists upcoming earnings dates for selected tickers, categorized by company and sector, with sorting capabilities provided by `yfinance`.

### **Market Heat Map**

Creates a heat map showing stock percentage changes over the last 5 days, using `matplotlib`, with color intensity reflecting the magnitude of the changes.

## Work in Progress 🎉

These tools are currently under development. Features and functionalities may be added or modified in future updates.
