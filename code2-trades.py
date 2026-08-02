# -*- coding: utf-8 -*-
"""
Created on Sun Aug  2 20:11:21 2026

@author: tarun
"""

# -*- coding: utf-8 -*-
"""
Created on Sat Aug  1 19:29:19 2026

@author: tarun
"""

import os
os.chdir(r"C:\Users\tarun\Desktop\mech-buy")

# =============================================================================
# issues:
    #1) the limit updated does not update properly if stock falls a lot. action: remove limit updated.
    #and bring the sell price in portfolio for each stock. price updated everyday and sell is 10 pc down from maxiumum. done 
    #2) if all are sold and nothing to buy then it never buys after the loop/: done
    #3) update buy list from above 2-5 25 dms to also cover in uptrend:i think ots done
    #4) if stock market falling buying can stop!: not done
    #5) price for ranibow did not update and was 1525 for all of them, inflationg the value
# =============================================================================


from code1 import *

data = download_data(TICKERS,start_date)

data = prepare_indicators(data)

data=get_day(data)

#data1 = prepare_rebalance_data(data)



history,trades=run_backtest(data,first_day,money,max_positions,allocation_per_stock,stoploss, dist_low, dist_high)

#get date
history=get_date(history, data)



stats = performance_metrics(history,initial_capital=1000000)

plot_equity_curve(history)


# hj=pd.DataFrame(trades)
# hj.columns= ['action', "stock", "price", "qty"]

# hj['check']=[1 if i=='sell' else -1 for i in hj.action]

# hj['money']=[i*j*k for i,j,k in zip(hj.price, hj.qty, hj.check)]

# hj.money.sum()

# list(hj)

# kl=hj.groupby(['action', "stock"]).agg({'price':np.mean, 'qty':sum}).reset_index()
# kl=hj.groupby([ "stock"]).sum('money').reset_index()
# kl=hj.groupby([ "action"]).sum('money').reset_index()

