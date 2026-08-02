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

#data1 = prepare_rebalance_data(data)

history = run_backtest(
    data,
    first_day=70
)

stats = performance_metrics(
    history,
    initial_capital=1000000
)

plot_equity_curve(history)


# =============================================================================
# temp
# =============================================================================

df=data['ADANIENT.NS']
#df['flag_counter'] 


def flag_counter(df):
    counter=0
    flag_counter=[]
    for i in df['flag']:
        if i:
            counter+=1
            flag_counter.append(counter)
        else:
            counter=0
            flag_counter.append(counter)
    df['flag_counter'] =flag_counter
    return df


buy_list=get_buy_candidates(data,
                       day=70,
                       owned=[],
                       dist_low=2,
                       dist_high=5)

portfolio, money, owned=build_initial_portfolio(data,
                            buy_list,
                            first_day,
                            capital=1000000,
                            max_positions=5,
                            allocation_per_stock=200000,
                            stoploss=5)


portfolio=mark_to_market(portfolio,
                   data,
                   day,stoploss)


sell_list=get_sell_list(portfolio,
                  data,
                  day)


portfolio, money, owned= execute_sells(portfolio,
                  sell_list,
                  data1,
                  day,
                  money)

buy_list=get_buy_candidates(data,
                       day=143,
                       owned=owned,
                       dist_low=2,
                       dist_high=5)



