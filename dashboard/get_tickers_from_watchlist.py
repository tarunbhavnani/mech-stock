# -*- coding: utf-8 -*-
"""
Created on Wed Aug 19 15:08:43 2026

@author: Tarun
"""

cw= pd.read_csv(r"C:\Users\Tarun\OneDrive\Desktop\git\mech-stock\dashboard\data\core-watchlist.csv")
import requests
import yfinance as yf

def get_ticker_from_isin(isin_code):
    url = "https://query2.finance.yahoo.com/v1/finance/search"
    params = {'q': isin_code, 'quotesCount': 1, 'newsCount': 0}
    headers = {'User-Agent': 'Mozilla/5.0'}  # Required to prevent 403 blocks
    
    response = requests.get(url, params=params, headers=headers)
    data = response.json()
    
    quotes = data.get('quotes', [])
    if quotes:
        return quotes[0]['symbol']  # Returns the correct Yahoo ticker (e.g., 'AAPL' or 'INFY.NS')
    else:
        raise ValueError(f"No ticker found for ISIN: {isin_code}")

# Example usage with Apple's ISIN (US0378331005)
isin = "INE00TV01023"
ticker_symbol = get_ticker_from_isin(isin)
print(f"Resolved Ticker: {ticker_symbol}")

cw['ISIN Code']

TICKERS=[]
for isin in cw['ISIN Code']:
    try:
        ticker_symbol = get_ticker_from_isin(isin)
        TICKERS.append(ticker_symbol)
    except:
        print(isin)


print(TICKERS)
