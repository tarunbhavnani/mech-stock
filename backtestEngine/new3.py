# -*- coding: utf-8 -*-
"""
Created on Tue Aug 11 19:18:45 2026

@author: tarun
"""

all_tickers=TICKERS.copy()
all_data = download_data(all_tickers,start_date='2020-01-01', end_date= '2026-08-05')

all_nifty = download_nifty(start_date='2020-01-01', end_date= '2026-08-05')




data,nifty= get_final_data(all_data,all_nifty, TICKERS)


pm=PortfolioManager(data,nifty, stoploss, first_day, money, max_positions,dist_low,dist_high)


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
