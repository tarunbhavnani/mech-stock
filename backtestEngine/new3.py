# -*- coding: utf-8 -*-
"""
Created on Tue Aug 11 19:18:45 2026

@author: tarun
"""

import os
os.chdir(r"C:\Users\tarun\Desktop\mech-buy\backtestEngine")

from new1 import *
from new2 import *
from config import *



#all_tickers=TICKERS.copy()

# =============================================================================
#get all data first

#all_data = download_data(all_tickers,start_date='2020-01-01', end_date= '2026-08-28')

#all_nifty = download_nifty(start_date='2020-01-01', end_date= '2026-08-28')
 
# =============================================================================

#load TICKERS

data,nifty= get_final_data(all_data,all_nifty, TICKERS)


#call pm class

pm=PortfolioManager(data,nifty, stoploss, first_day, money, max_positions,dist_low,dist_high)

#run backtest

history, all_bought, all_sold=pm.run_backtest()


stats = performance_metrics(history,initial_capital=1000000)

plot_equity_curve(history)


final3=get_transactions(all_bought, all_sold)
final3=final3.sort_values(by=['ticker','day'])
kl=final3.groupby(['day', 'action']).apply(lambda x: list(x['ticker'])).reset_index()
kl.columns=['day', 'action', 'ticker']

kl['pf']=0
pf=kl.ticker.iloc[0]

pf={}
temp=[]
for i in range(0,len(kl)):
    if kl.action.iloc[i]=='buy':
        temp=temp+kl.ticker.iloc[i]
    elif kl.action.iloc[i]=='sell':
        for c in kl.ticker.iloc[i]:
            temp.remove(c)
    
    
    pf[kl.day.iloc[i]]=temp


history['chg']=history.equity.diff()

mx=0
dd=[]
for i in history['equity']:
    if i>mx:
        mx=i
    if mx!=0:
        dd.append(round((100*(i-mx)/mx),2))
    else:
        dd.append(0)
        
history['dd']=dd


hj=final3.groupby(['ticker', 'qty'])
fd={}
for i in hj:
    try:
    
        buy=i[1][i[1]['action']=='buy']['price'].iloc[0]*i[1][i[1]['action']=='buy']['qty'].iloc[0]
        sell=i[1][i[1]['action']=='sell']['price'].iloc[0]*i[1][i[1]['action']=='sell']['qty'].iloc[0]
        fd[i[0]]=(sell-buy)/buy
    except:
        pass
# =============================================================================
# 96 saved version 
# ==================================================
# Initial Capital : 1,000,000
# Ending Equity   : 39,160,820
# CAGR            : 78.95%
# Max Drawdown    : -31.89%
# ==================================================
# =============================================================================
