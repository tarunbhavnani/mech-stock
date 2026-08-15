# -*- coding: utf-8 -*-
"""
Created on Mon Aug 10 20:14:41 2026

@author: tarun


#1 angle in good candidates is not useful but super useful in sell candidates. best being row["Close"] < row['SMA25']*.98 and row['anti_flag_counter']>5 and row['Angle']<0

#2 Good candidates : below works wonders~95 cagr but only if stocks perform good in future.
for medium like nifty cagr is 18. for bad candidates it can give a crazy bad cagr. falling stocks in last 2 years gave 50 pc drawdown in 2025 till 2026 aug
    
    
    if dist_low < row["Dist25"] < dist_high:
        #if row["Dist25"] < 10:
            
            if row['flag_counter']>2 and row["Dist25_Change"]>0:
                
3# if update above row['flag_counter']>9 . This works good to reduce drawdown alot if market or stocks turn bad as buying become less
it also reduces the good stocks cagr from 95 to 65