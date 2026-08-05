# -*- coding: utf-8 -*-
"""
Created on Mon Aug  3 21:19:45 2026

@author: tarun
flag is close > 25sma
flag counter is consecutive days above 25sma
"""

import os

os.chdir(r'C:\Users\tarun\Desktop\mech-buy\dashboard')

# =============================================================================
# get current data
# =============================================================================

from get_data import *

from portfolio_manager import *

from config import *

TICKERS=list(set(TICKERS))
#start_date="2026-01-01"

data = download_data(TICKERS,start_date)

data = prepare_indicators(data)


# =============================================================================
# get current portfolio
# =============================================================================

import json

# Read dictionary from JSON
with open("data\portfolio.json", "r") as f:
    portfolio = json.load(f)

# =============================================================================
# load PM class and update prices
# =============================================================================

pm = PortfolioManager(data, portfolio, stoploss,pf_start_date)

updated_portfolio=pm.update_current_portfolio()

pm.save_portfolio()


# =============================================================================
# get sell candidates
# =============================================================================

pm.update_current_portfolio()

sell_list= pm.get_sell_list()


# =============================================================================
# update if sold
# =============================================================================

#sell_ticker="ZAGGLE.NS"

sold = pm.sell_stock(sell_ticker)

pm.save_portfolio()

# =============================================================================
# get buy candidates
# =============================================================================

buy_list = pm.get_buy_candidates(dist_low, dist_high)


check=pd.DataFrame([data[i].iloc[-1] for i in data if i in buy_list])
check.sort_values(by='Dist25', inplace=True)

# =============================================================================
# update if bought
# =============================================================================

#buy_ticker="ABC.NS"

pm.buy_stock(buy_ticker, price=100, qty=10)

pm.save_portfolio()


# =============================================================================
# end
# =============================================================================


