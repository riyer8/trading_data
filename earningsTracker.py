from datetime import date
import tkinter as tk
from tkinter import ttk
import yfinance as yf
from portfolioInfo import MY_TICKERS

def all_tickers():
    print(f"Total Number of Tickers: {len(MY_TICKERS)}")
    return sorted(set(MY_TICKERS))

def company_info(ticker):
    ticker_obj = yf.Ticker(ticker)
    company_name = ticker_obj.info.get('longName', 'N/A')
    sector = ticker_obj.info.get('sector', 'N/A')
    return company_name, sector

def find_next_earnings(ticker):
    ticker_obj = yf.Ticker(ticker)
    today_date = date.today()
    calendar = ticker_obj.calendar

    if len(calendar['Earnings Date']) == 0:
        return 'N/A'
    
    next_earnings = calendar['Earnings Date'][0]
    
    if next_earnings < today_date:
        if len(calendar['Earnings Date']) < 2:
            return 'N/A'
        return calendar['Earnings Date'][1]
    
    return next_earnings

def filter_tickers():
    tickers = all_tickers()
    data = []

    for ticker in tickers:
        company_name, sector = company_info(ticker)
        next_earnings = find_next_earnings(ticker)
        if next_earnings != 'N/A':
            data.append([ticker, company_name, sector, next_earnings])

    return sorted(data, key=lambda x: x[3], reverse=True)

def sort_tickers(treeview, column, reverse):
    column_indices = {"Ticker": 0, "Company Name": 1, "Sector": 2, "Upcoming Earnings": 3}
    col_index = column_indices[column]

    items = [(treeview.item(child)['values'], child) for child in treeview.get_children()]

    if column == "Upcoming Earnings":
        items.sort(key=lambda x: (x[0][col_index] == 'N/A', x[0][col_index]), reverse=reverse)
    else:
        items.sort(key=lambda x: x[0][col_index], reverse=reverse)

    treeview.delete(*treeview.get_children())
    for values, item in items:
        treeview.insert("", tk.END, iid=item, values=values)

    for col in column_indices:
        treeview.heading(col, text=col)

    arrow = "↓" if reverse else "↑"
    treeview.heading(column, text=f"{column} {arrow}", command=lambda: sort_tickers(treeview, column, not reverse))

def display_tickers():
    root = tk.Tk()
    root.title("Upcoming Earnings Tickers")

    frame = tk.Frame(root)
    frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    ticker_data = filter_tickers()
    columns = ("Ticker", "Company Name", "Sector", "Upcoming Earnings")
    tree = ttk.Treeview(frame, columns=columns, show='headings')

    column_widths = {
        "Ticker": 100, "Company Name": 200, "Sector": 150, "Upcoming Earnings": 150
    }

    for col in columns:
        tree.heading(col, text=col, command=lambda col=col: sort_tickers(tree, col, False))
        tree.column(col, width=column_widths[col])

    for item in ticker_data:
        tree.insert("", tk.END, values=item)

    tree.pack(expand=True, fill=tk.BOTH)
    root.mainloop()

if __name__ == "__main__":
    display_tickers()