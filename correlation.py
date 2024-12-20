from datetime import date
import tkinter as tk
from tkinter import ttk
import yfinance as yf
from portfolioInfo import PYPL_TICKERS
from scipy.stats import pearsonr

CORRELATION_WEIGHTS = {
    'beta': 0,
    'industry': 0,
    'liquidity': 0,
    'market_cap': 0,
    'sector': 0,
    'volume': 1.0,
    'pearson': 0,
    'returns': 0,
    'dividend_yield': 0,
    'pe_ratio': 0,
    'pb_ratio': 0,
    'gross_margin': 1.0,
    'peg_ratio': 1.0,
}

def ticker_data(ticker):
    ticker_obj = yf.Ticker(ticker)
    return ticker_obj.history(period="1y"), ticker_obj.info

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

def pearson_correlation(target_ticker, compare_ticker):
    if target_ticker == compare_ticker:
        return 1
    target_data, _ = ticker_data(target_ticker)
    compare_data, _ = ticker_data(compare_ticker)

    target_prices = target_data['Close'].dropna()
    compare_prices = compare_data['Close'].dropna()
    aligned_target, aligned_compare = target_prices.align(compare_prices, join='inner')
    
    if len(aligned_target) < 30:
        return 0

    target_returns = aligned_target.pct_change().dropna()
    compare_returns = aligned_compare.pct_change().dropna()
    returns_correlation, _ = pearsonr(target_returns, compare_returns)
    
    return returns_correlation if isinstance(returns_correlation, float) else 0

def returns_correlation(target_ticker, compare_ticker):
    if target_ticker == compare_ticker:
        return 1
    target_data, _ = ticker_data(target_ticker)
    compare_data, _ = ticker_data(compare_ticker)

    target_returns = target_data['Close'].pct_change().dropna()
    compare_returns = compare_data['Close'].pct_change().dropna()
    aligned_target, aligned_compare = target_returns.align(compare_returns, join='inner')
    
    if len(aligned_target) < 30:
        return 0

    return pearsonr(aligned_target, aligned_compare)[0]

def dividend_yield_similarity(target_info, compare_info, target_ticker, compare_ticker):
    if target_ticker == compare_ticker:
        return 1
    div_yield1 = target_info.get('dividendYield', 0) or 0
    div_yield2 = compare_info.get('dividendYield', 0) or 0
    if max(div_yield1, div_yield2) > 0:
        return 1 - abs(div_yield1 - div_yield2) / max(div_yield1, div_yield2)
    return 0

def pe_ratio_similarity(target_info, compare_info, target_ticker, compare_ticker):
    if target_ticker == compare_ticker:
        return 1
    pe1 = target_info.get('trailingPE', 0) or 0
    pe2 = compare_info.get('trailingPE', 0) or 0
    if max(pe1, pe2) > 0:
        return 1 - abs(pe1 - pe2) / max(pe1, pe2)
    return 0

def pb_ratio_similarity(target_info, compare_info, target_ticker, compare_ticker):
    if target_ticker == compare_ticker:
        return 1
    pb1 = target_info.get('priceToBook', 0) or 0
    pb2 = compare_info.get('priceToBook', 0) or 0
    if max(pb1, pb2) > 0:
        return 1 - abs(pb1 - pb2) / max(pb1, pb2)
    return 0

def gross_margin_similarity(target_info, compare_info, target_ticker, compare_ticker):
    if target_ticker == compare_ticker:
        return 1
    gross_margin1 = target_info.get('grossMargins', 0) or 0
    gross_margin2 = compare_info.get('grossMargins', 0) or 0
    if max(gross_margin1, gross_margin2) > 0:
        return 1 - abs(gross_margin1 - gross_margin2) / max(gross_margin1, gross_margin2)
    return 0

def peg_ratio_similarity(target_info, compare_info, target_ticker, compare_ticker):
    if target_ticker == compare_ticker:
        return 1
    peg1 = target_info.get('pegRatio', 0) or 0
    peg2 = compare_info.get('pegRatio', 0) or 0
    if max(peg1, peg2) > 0:
        return 1 - abs(peg1 - peg2) / max(peg1, peg2)
    return 0

def correlation_factor(target_info, compare_info, target_ticker, compare_ticker):
    similarities = [
        sector_similarity(target_info, compare_info),
        industry_similarity(target_info, compare_info),
        market_cap_similarity(target_info, compare_info, target_ticker, compare_ticker),
        beta_correlation(target_info, compare_info, target_ticker, compare_ticker),
        volume_similarity(target_info, compare_info, target_ticker, compare_ticker),
        liquidity_similarity(target_info, compare_info, target_ticker, compare_ticker),
        pearson_correlation(target_ticker, compare_ticker),
        returns_correlation(target_ticker, compare_ticker),
        dividend_yield_similarity(target_info, compare_info, target_ticker, compare_ticker),
        pe_ratio_similarity(target_info, compare_info, target_ticker, compare_ticker),
        pb_ratio_similarity(target_info, compare_info, target_ticker, compare_ticker),
        gross_margin_similarity(target_info, compare_info, target_ticker, compare_ticker),
        peg_ratio_similarity(target_info, compare_info, target_ticker, compare_ticker)
    ]

    weighted_sum = sum(weight * sim for weight, sim in zip(CORRELATION_WEIGHTS.values(), similarities))
    return weighted_sum / sum(CORRELATION_WEIGHTS.values())

def filter_tickers(symbol, min_corr_factor):
    _, target_info = ticker_data(symbol)
    filtered_tickers = []

    for ticker in PYPL_TICKERS:
        _, compare_info = ticker_data(ticker)
        corr_factor = correlation_factor(target_info, compare_info, symbol, ticker)
        if corr_factor >= min_corr_factor:
            company_name = compare_info.get('longName', 'N/A')
            current_price = compare_info.get('last_price', compare_info.get('currentPrice', 0))  # Fetch current price
            filtered_tickers.append((ticker, company_name, corr_factor, current_price))

    return sorted(filtered_tickers, key=lambda x: x[2], reverse=True)

def sort_tickers(treeview, column, reverse):
    column_indices = {
        "Ticker": 0,
        "Company Name": 1,
        "Correlation": 2,
        "Current Price": 3,
    }
    col_index = column_indices[column]

    items = [(treeview.item(child)['values'], child) for child in treeview.get_children()]
    if column in ["Correlation", "Current Price"]:
        items.sort(key=lambda x: float(x[0][col_index]), reverse=reverse)
    else:
        items.sort(key=lambda x: x[0][col_index], reverse=reverse)
    treeview.delete(*treeview.get_children())
    for values, item in items:
        treeview.insert("", tk.END, iid=item, values=values)
    for col in column_indices:
        treeview.heading(col, text=col)
    arrow = "↓" if reverse else "↑"
    treeview.heading(column, text=f"{column} {arrow}", command=lambda: sort_tickers(treeview, column, not reverse))

def display_tickers(symbol, min_corr_factor):
    root = tk.Tk()
    root.title(f"Tickers Correlated with {symbol}")

    frame = tk.Frame(root)
    frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    correlated_tickers = filter_tickers(symbol, min_corr_factor)
    columns = ("Ticker", "Company Name", "Correlation", "Current Price")
    tree = ttk.Treeview(frame, columns=columns, show='headings')

    column_widths = {
        "Ticker": 50,
        "Company Name": 150,
        "Correlation": 120,
        "Current Price": 70,
    }

    for col in columns:
        tree.heading(col, text=col, command=lambda _col=col: sort_tickers(tree, _col, False))
        tree.column(col, width=column_widths[col])

    for ticker, company_name, corr_factor, current_price in correlated_tickers:
        tree.insert("", tk.END, values=(ticker, company_name, f"{corr_factor:.2f}", f"{current_price:.2f}"))

    tree.pack(expand=True, fill=tk.BOTH)
    root.mainloop()

if __name__ == "__main__":
    symbol = input("Enter the symbol to compare: ").strip().upper()
    min_corr_factor = float(input("Enter the minimum correlation factor (0 to 1): "))
    display_tickers(symbol, min_corr_factor)