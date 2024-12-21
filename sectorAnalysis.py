import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

from portfolioInfo import (
    SEMICONDUCTOR_COMPANIES, TECHNOLOGY_COMPANIES, 
    CONSUMER_DISCRETIONARY_COMPANIES, ENERGY_COMPANIES, HEALTHCARE_COMPANIES, 
    FINANCIAL_COMPANIES, CONSUMER_STAPLES_COMPANIES, 
    COMMUNICATION_COMPANIES, UTILITIES_COMPANIES, MATERIALS_COMPANIES,
    TRAVEL_COMPANIES
)

SECTORS = {
    'Semiconductor': SEMICONDUCTOR_COMPANIES,
    'Technology': TECHNOLOGY_COMPANIES,
    'Consumer Discretionary': CONSUMER_DISCRETIONARY_COMPANIES,
    'Energy': ENERGY_COMPANIES,
    'Healthcare': HEALTHCARE_COMPANIES,
    'Financial': FINANCIAL_COMPANIES,
    'Consumer Staples': CONSUMER_STAPLES_COMPANIES,
    'Communication Services': COMMUNICATION_COMPANIES,
    'Utilities': UTILITIES_COMPANIES,
    'Materials': MATERIALS_COMPANIES,
    'Travels': TRAVEL_COMPANIES
}

def calculate_sector_performance(tickers):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    data = yf.download(tickers, start=start_date, end=end_date)
    
    adj_close = data['Adj Close'].copy()
    volume = data['Volume'].copy()
    
    adj_close = adj_close.dropna(axis=1)
    volume = volume.dropna(axis=1)
    
    price_change = (adj_close.iloc[-1] - adj_close.iloc[0]) / adj_close.iloc[0] * 100
    avg_price_change = price_change.mean()
    
    volume_change = (volume.iloc[-1] - volume.iloc[0]) / volume.iloc[0] * 100
    avg_volume_change = volume_change.mean()
    
    stock_price_change = adj_close.sum(axis=1)
    stock_price_change_percentage = (stock_price_change.iloc[-1] - stock_price_change.iloc[0]) / stock_price_change.iloc[0] * 100
    
    return avg_price_change, avg_volume_change, stock_price_change_percentage

sector_performance = {}
sector_volume_change = {}
sector_sum_price_change = {}

for sector, tickers in SECTORS.items():
    price_performance, volume_performance, sum_price_performance = calculate_sector_performance(tickers)
    sector_performance[sector] = price_performance
    sector_volume_change[sector] = volume_performance
    sector_sum_price_change[sector] = sum_price_performance

performance_df = pd.DataFrame.from_dict(sector_performance, orient='index', columns=['Performance'])
volume_df = pd.DataFrame.from_dict(sector_volume_change, orient='index', columns=['Volume Change'])
sum_price_df = pd.DataFrame.from_dict(sector_sum_price_change, orient='index', columns=['Stock Price Change'])

def add_labels(ax):
    for p in ax.patches:
        height = p.get_height()
        if height > 0:
            ax.annotate(f'{height:.2f}%', 
                        (p.get_x() + p.get_width() / 2., height), 
                        ha='center', va='center', fontsize=10, color='black', xytext=(0, 5),
                        textcoords='offset points')
        else:
            ax.annotate(f'{height:.2f}%', 
                        (p.get_x() + p.get_width() / 2., height), 
                        ha='center', va='center', fontsize=10, color='black', xytext=(0, -10),
                        textcoords='offset points')

def plot_graphs(figNum, df, criteria, yLabel):
    plt.figure(figNum, figsize=(7.5, 4.5))
    ax = df.sort_values(by=criteria, ascending=False).plot(kind='bar', legend=False, ax=plt.gca())
    plt.title(f'Sector {criteria} Over the Last Month')
    plt.ylabel(yLabel)
    plt.xlabel('Sector')
    plt.xticks(rotation=45)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    add_labels(ax)

if __name__ == "__main__":
    plot_graphs(1, performance_df, 'Performance', 'Average Percentage Change')
    plot_graphs(2, volume_df, 'Volume Change', 'Average Volume Percentage Change')
    plot_graphs(3, sum_price_df, 'Stock Price Change', 'Stock Prices Percentage Change')
    plt.show()