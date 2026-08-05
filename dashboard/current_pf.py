# -*- coding: utf-8 -*-
"""
Created on Mon Aug  3 18:13:09 2026

@author: tarun
"""
import numpy as np

data = download_data(TICKERS,start_date)

data = prepare_indicators(data)


current_list={'ARIS.NS': '1000', 'BLACKBUCK.NS': '200', 'COHANCE.NS': '3300', 'DABUR.NS': '1000',
              'DELTACORP.NS': '10000', 'EFCIL.NS': '250', 'GOCOLORS.NS': '500', 'GULPOLY.NS': '2000',
              'IOC.NS': '3000', 'INDOFARM.NS': '2000', 'JIOFIN.NS': '7000', 'KPEL.NS': '500',
              'NETWORK18.NS': '29000', 'PARADEEP.NS': '1000', 'RELIANCE.NS': '400', 'SAGILITY.NS': '10000',
              'MOTHERSON.NS': '4725', 'SUVEN.NS': '1000', 'SWANCORP.NS': '2750', 'TIMETECHNO.NS': '5000',
              'VEDL.NS': '1250', 'VIKRAN.NS': '2500', 'ZTECH.NS': '300', 'ZAGGLE.NS': '250'}

def current_portfolio(data, current_list,  stoploss):
    """
    Build current portfolio in required format on todays date

    Returns
    -------
    portfolio
    
    """

    portfolio = {}

    for ticker in current_list:
        

        row = data[ticker].iloc[-1]

        if row is None:
            continue

        price = np.floor(row["Close"])
        
        highest_price=price
        
        sl=np.ceil(highest_price*(100-stoploss)/100)

        qty = int(current_list[ticker])

        cost = qty * price

        
        portfolio[ticker] = {

            "price": price,
            
            "highest_price": highest_price,

            "qty": qty,

            "value": cost,
            "sl":sl

        }
    return portfolio

current_portfolio= current_portfolio(data, current_list,  stoploss)

# =============================================================================
# 
# =============================================================================

def update_current_portfolio(data, portfolio, stoploss):
    
    """
    update current portfolio with latest prices

    Returns
    -------
    portfolio
    
    """

    for ticker in portfolio:
        
        row = data[ticker].iloc[-1]
        
        if row is None:
            continue
        
        price = np.floor(row["Close"])
        
        
                
        portfolio[ticker]['price'] = price
        
        if price>portfolio[ticker]['highest_price']:
            portfolio[ticker]['highest_price']=price
            portfolio[ticker]['sl']=sl=np.ceil(price*(100-stoploss)/100)
            
    return portfolio

current_portfolio= update_current_portfolio(data, current_portfolio, stoploss)


# =============================================================================
# 
# =============================================================================


def get_buy_candidates(data,dist_low,dist_high):

    """
    Find stocks eligible for buying.

    Returns
    -------
    list
    """

    buy_list = {}

    for ticker in data:

 

        row = data[ticker].iloc[-1]

        if row is None:
            continue

        if row["flag"]:

            if dist_low < row["Dist25"] < dist_high:
                if row['flag_counter']>5 and row["Dist25_Change"]>0:
                    #print(row['flag_counter'])

                    buy_list[ticker] = row["Dist25"]

    buy_list = dict(
        sorted(
            buy_list.items(),
            key=lambda x: x[1]
        )
    )

    return list(buy_list.keys())

buy_list=get_buy_candidates(data,dist_low,dist_high)





# =============================================================================
# sell stock
# =============================================================================


def sell_stock(portfolio, ticker):
    
    sold=portfolio.pop('ZAGGLE.NS')
    
    return portfolio, sold


# =============================================================================
# buy stock
# =============================================================================

def buy_stock(stoploss, portfolio, ticker, price, qty):
    
    bought={

        "price": price,
        
        "highest_price": price,

        "qty": qty,

        "value": price*qty,
        
        "sl":np.ceil(price*(100-stoploss)/100)

    }
    
    portfolio[ticker]=bought
    
    
    return portfolio





    





