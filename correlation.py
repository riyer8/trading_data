from datetime import date
import tkinter as tk
from tkinter import ttk
import yfinance as yf
from portfolioInfo import ALL_TICKERS

CORRELATION_WEIGHTS = {
    'beta': 1.0,
    'industry': 2.0,
    'liquidity': 2.0,
    'market_cap': 1.0,
    'sector': 2.0,
    'volume': 1.0
}

def ticker_data(ticker):
    ticker_obj = yf.Ticker(ticker)
    return ticker_obj.history(period="6mo"), ticker_obj.info

def company_info(ticker):
    _, info = ticker_data(ticker)
    return info.get('longName', 'N/A'), info.get('sector', 'N/A')

def sector_similarity(target_info, compare_info):
    if target_info.get('sector') == compare_info.get('sector'):
        return 1
    return 0

def industry_similarity(target_info, compare_info):
    if target_info.get('industry') == compare_info.get('industry'):
        return 1
    return 0

def market_cap_similarity(target_info, compare_info, target_ticker, compare_ticker):
    market_cap1 = target_info.get('marketCap', 0)
    market_cap2 = compare_info.get('marketCap', 0)
    if target_ticker == compare_ticker:
        return 1
    if max(market_cap1, market_cap2) > 0:
        return 1 - abs(market_cap1 - market_cap2) / max(market_cap1, market_cap2)
    return 0

def beta_correlation(target_info, compare_info, target_ticker, compare_ticker):
    beta1 = target_info.get('beta', 1.0)
    beta2 = compare_info.get('beta', 1.0)
    if target_ticker == compare_ticker:
        return 1
    if max(beta1, beta2) > 0:
        return 1 - abs(beta1 - beta2) / max(beta1, beta2)
    return 0

def volume_similarity(target_info, compare_info, target_ticker, compare_ticker):
    avg_volume1 = target_info.get('averageVolume', 1)
    avg_volume2 = compare_info.get('averageVolume', 1)
    if target_ticker == compare_ticker:
        return 1
    if max(avg_volume1, avg_volume2) > 0:
        return 1 - abs(avg_volume1 - avg_volume2) / max(avg_volume1, avg_volume2)
    return 0

def liquidity_similarity(target_info, compare_info, target_ticker, compare_ticker):
    bid_ask_spread1 = target_info.get('ask', 0) - target_info.get('bid', 0)
    bid_ask_spread2 = compare_info.get('ask', 0) - compare_info.get('bid', 0)
    if target_ticker == compare_ticker:
        return 1
    if max(bid_ask_spread1, bid_ask_spread2) > 0:
        return 1 - abs(bid_ask_spread1 - bid_ask_spread2) / max(bid_ask_spread1, bid_ask_spread2)
    return 0

def correlation_factor(target_info, compare_info, target_ticker, compare_ticker):
    similarities = [
        sector_similarity(target_info, compare_info),
        industry_similarity(target_info, compare_info),
        market_cap_similarity(target_info, compare_info, target_ticker, compare_ticker),
        beta_correlation(target_info, compare_info, target_ticker, compare_ticker),
        volume_similarity(target_info, compare_info, target_ticker, compare_ticker),
        liquidity_similarity(target_info, compare_info, target_ticker, compare_ticker)
    ]

    weighted_sum = sum(weight * sim for weight, sim in zip(CORRELATION_WEIGHTS.values(), similarities))
    return weighted_sum / sum(CORRELATION_WEIGHTS.values())

def find_next_earnings(ticker):
    ticker_obj = yf.Ticker(ticker)
    today_date = date.today()
    calendar = ticker_obj.calendar

    if not calendar.get('Earnings Date'):
        return 'N/A'

    next_earnings = calendar['Earnings Date'][0]
    if next_earnings < today_date:
        if len(calendar['Earnings Date']) < 2:
            return 'N/A'
        return calendar['Earnings Date'][1]
    
    return next_earnings

def filter_tickers(symbol, min_corr_factor):
    _, target_info = ticker_data(symbol)
    filtered_tickers = []

    for ticker in ALL_TICKERS:
        _, compare_info = ticker_data(ticker)
        corr_factor = correlation_factor(target_info, compare_info, symbol, ticker)
        if corr_factor >= min_corr_factor:
            company_name, sector = company_info(ticker)
            last_price = compare_info.get('previousClose', 0)
            earnings_date = find_next_earnings(ticker)
            filtered_tickers.append((ticker, company_name, corr_factor, sector, last_price, earnings_date))

    return sorted(filtered_tickers, key=lambda x: x[2], reverse=True)

def sort_tickers(treeview, column, reverse):
    column_indices = {
        "Ticker": 0,
        "Company Name": 1,
        "Correlation Factor": 2,
        "Sector": 3,
        "Last Price": 4,
        "Earnings Date": 5
    }
    col_index = column_indices[column]

    items = [(treeview.item(child)['values'], child) for child in treeview.get_children()]
    items.sort(key=lambda x: float(x[0][col_index]) if column in ["Correlation Factor", "Last Price"] else x[0][col_index], reverse=reverse)

    treeview.delete(*treeview.get_children())
    for values, item in items:
        treeview.insert("", tk.END, iid=item, values=values)

    arrow = "↓" if reverse else "↑"
    treeview.heading(column, text=f"{column} {arrow}", command=lambda: sort_tickers(treeview, column, not reverse))

def display_tickers(symbol, min_corr_factor):
    root = tk.Tk()
    root.title(f"Tickers Correlated with {symbol}")

    frame = tk.Frame(root)
    frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    correlated_tickers = filter_tickers(symbol, min_corr_factor)
    columns = ("Ticker", "Company Name", "Correlation Factor", "Sector", "Last Price", "Earnings Date")
    tree = ttk.Treeview(frame, columns=columns, show='headings')

    column_widths = {
        "Ticker": 50,
        "Company Name": 150,
        "Correlation Factor": 120,
        "Sector": 100,
        "Last Price": 70,
        "Earnings Date": 100
    }

    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=column_widths[col])

    for ticker, company_name, corr_factor, sector, last_price, earnings_date in correlated_tickers:
        tree.insert("", tk.END, values=(ticker, company_name, f"{corr_factor:.2f}", sector, f"{last_price:.2f}", earnings_date))

    tree.pack(expand=True, fill=tk.BOTH)
    root.mainloop()

if __name__ == "__main__":
    symbol = input("Enter the symbol to compare: ").strip().upper()
    min_corr_factor = float(input("Enter the minimum correlation factor (0 to 1): "))
    display_tickers(symbol, min_corr_factor)