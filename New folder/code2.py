# -*- coding: utf-8 -*-
"""
Created on Sat Aug  1 19:29:19 2026

@author: tarun
"""

import os
os.chdir(r"C:\Users\tarun\Desktop\mech-buy")

# =============================================================================
# issues:
    #1) the limit updated does not update properly if stock falls a lot. action: remove limit updated. and bring the sell price in portfolio for each stock. price updated everyday and sell is 10 pc down from maxiumum
    #2) if all are sold and nothing to buy then it never buys after the loop/
    #3) update buy list from above 2-5 25 dms to also cover in uptrend
    #4) if stock market falling buying can stop!
# =============================================================================


from code1 import *

data = download_data(TICKERS,start_date="2025-01-01")

data = prepare_indicators(data)

data1 = prepare_rebalance_data(data)

history = run_backtest(
    data1,
    first_day=70
)

stats = performance_metrics(
    history,
    initial_capital=1000000
)

plot_equity_curve(history)
