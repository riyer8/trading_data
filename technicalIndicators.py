import pandas as pd
import tkinter as tk
from tkinter import ttk
import yfinance as yf
from portfolioInfo import MY_TICKERS

def fetch_all_tickers():
    return sorted(set(MY_TICKERS))

def get_company_info(ticker):
    ticker_obj = yf.Ticker(ticker)
    company_name = ticker_obj.info.get('longName', 'N/A')
    sector = ticker_obj.info.get('sector', 'N/A')
    return company_name, sector

def calculate_rsi(data, period=14):
    delta = data['Close'].diff(1)
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

def get_pe_ratio(ticker):
    ticker_obj = yf.Ticker(ticker)
    return ticker_obj.info.get('trailingPE', 'N/A')

def get_moving_average(data, window=50):
    return data['Close'].rolling(window=window).mean().iloc[-1]

def get_short_percent_float(ticker):
    ticker_obj = yf.Ticker(ticker)
    return ticker_obj.info.get('shortPercentFloat', 'N/A')

def get_spx_beta(ticker):
    ticker_obj = yf.Ticker(ticker)
    return ticker_obj.info.get('beta', 'N/A')

def collect_technical_data(ticker):
    data = yf.download(ticker, period="6mo", interval="1d")
    last_price = data['Close'].iloc[-1]
    rsi = calculate_rsi(data)
    pe_ratio = get_pe_ratio(ticker)
    ma_50 = get_moving_average(data, 50)
    short_percent_float = get_short_percent_float(ticker)
    spx_beta = get_spx_beta(ticker)
    return last_price, rsi, pe_ratio, ma_50, short_percent_float, spx_beta

def sort_treeview_column(treeview, column, reverse):
    column_indices = {
        "Ticker": 0, "Company Name": 1, "Sector": 2, 
        "Last Price": 3, "RSI": 4, "P/E Ratio": 5, 
        "50-Day MA": 6, "Short % Float": 7, "SPX Beta": 8
    }
    col_index = column_indices[column]
    items = [(treeview.item(child)['values'], child) for child in treeview.get_children()]
    
    if column in ["RSI", "P/E Ratio", "50-Day MA", "Last Price", "Short % Float", "SPX Beta"]:
        items.sort(key=lambda x: float(x[0][col_index]) if x[0][col_index] not in ["N/A", ""] else float('inf'), reverse=reverse)
    else:
        items.sort(key=lambda x: x[0][col_index], reverse=reverse)

    treeview.delete(*treeview.get_children())
    for values, item in items:
        treeview.insert("", tk.END, iid=item, values=values)

    for col in column_indices:
        if col == column:
            arrow = "↓" if reverse else "↑"
            treeview.heading(col, text=f"{col} {arrow}", command=lambda c=col: sort_treeview_column(treeview, c, not reverse))
        else:
            treeview.heading(col, text=col, command=lambda c=col: sort_treeview_column(treeview, c, False))

def create_technical_indicators_screen():
    root = tk.Tk()
    root.title("Technical Indicators")
    frame = tk.Frame(root)
    frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    tickers = fetch_all_tickers()
    columns = ("Ticker", "Company Name", "Sector", "Last Price", "RSI", "P/E Ratio", "50-Day MA", "Short % Float", "SPX Beta")
    tree = ttk.Treeview(frame, columns=columns, show='headings')

    column_widths = {
        "Ticker": 50, "Company Name": 150, "Sector": 100, 
        "Last Price": 100, "RSI": 80, "P/E Ratio": 80, 
        "50-Day MA": 100, "Short % Float": 100, "SPX Beta": 100
    }

    for col in columns:
        tree.heading(col, text=col, command=lambda c=col: sort_treeview_column(tree, c, False))
        tree.column(col, width=column_widths[col])

    for ticker in tickers:
        company_name, sector = get_company_info(ticker)
        last_price, rsi, pe_ratio, ma_50, short_percent_float, spx_beta = collect_technical_data(ticker)
        
        pe_ratio_display = f"{float(pe_ratio):.2f}" if pe_ratio != 'N/A' else pe_ratio
        rsi_display = f"{rsi:.2f}"
        ma_50_display = f"{ma_50:.2f}"
        last_price_display = f"{last_price:.2f}"
        short_percent_float_display = f"{short_percent_float:.2%}" if short_percent_float != 'N/A' else short_percent_float
        spx_beta_display = f"{spx_beta:.2f}" if spx_beta != 'N/A' else spx_beta

        tree.insert("", tk.END, values=(ticker, company_name, sector, last_price_display, rsi_display, pe_ratio_display, ma_50_display, short_percent_float_display, spx_beta_display))

    tree.pack(expand=True, fill=tk.BOTH)
    root.mainloop()

if __name__ == "__main__":
    create_technical_indicators_screen()