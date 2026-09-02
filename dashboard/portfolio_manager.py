# -*- coding: utf-8 -*-
"""
Created on Mon Aug  3 21:36:52 2026

@author: tarun
"""

# -*- coding: utf-8 -*-
"""
Created on Mon Aug  3 21:19:27 2026

@author: tarun


make a similar one for hour level so that can be used on fno for fno calls!

add function to check portfolio drawdown, sell all at 5 pc? 

"""

import numpy as np
import json
import pandas as pd

class PortfolioManager:

    def __init__(self, data, portfolio, stoploss, pf_start_date):
        self.data = data
        self.pf_start_date=pf_start_date
        self.stoploss = stoploss
        self.portfolio = portfolio
        self.hp = self.get_highest_prices()
        self.max_pos=10

   
    
    def get_highest_prices(self):
        
        hp={}
        tickers= [i for i in self.data]
        for tick in tickers:
            temp=self.data[tick][self.data[tick]['date']>self.pf_start_date]
            hp[tick]=max(round(temp['High']))
            
        
        return hp
       
    
    # # =========================================================================
    # # Update current portfolio
    # # =========================================================================
    # def update_current_portfolio(self):
    #     """
    #     Update current portfolio with latest prices.
    #     """

    #     for ticker in self.portfolio:

    #         row = self.data[ticker].iloc[-1]

    #         if row is None:
    #             continue

    #         highest_price = np.floor(row["High"])
            
    #         price = np.floor(row["Close"])
    #         value= price*self.portfolio[ticker]["qty"]
            

    #         self.portfolio[ticker]["price"] = price
    #         self.portfolio[ticker]["value"] = value

    #         if highest_price > self.portfolio[ticker]["highest_price"]:
    #             self.portfolio[ticker]["highest_price"] = price
            
    #         self.portfolio[ticker]["sl"] = np.ceil(self.portfolio[ticker]["highest_price"] * (100 - self.stoploss) / 100)

    #     return self.portfolio
    # =========================================================================
    # Update current portfolio
    # =========================================================================
    def update_current_portfolio(self):
        """
        Update current portfolio with latest prices.
        """

        for ticker in self.portfolio:

            row = self.data[ticker].iloc[-1]

            if row is None:
                continue

            highest_prices=self.hp
            self.portfolio[ticker]["highest_price"] = highest_prices[ticker]
             
            
            price = np.floor(row["Close"])
            value= price*self.portfolio[ticker]["qty"]
            

            self.portfolio[ticker]["price"] = price
            self.portfolio[ticker]["value"] = value

            
            self.portfolio[ticker]["sl"] = np.ceil(self.portfolio[ticker]["highest_price"] * (100 - self.stoploss) / 100)
            
            
            
            self.save_portfolio()

        return self.portfolio

    # =========================================================================
    # Buy candidates
    # =========================================================================
    def get_buy_candidates(self, dist_low, dist_high):
        """
        Find stocks eligible for buying.
        """

        buy_list = {}

        for ticker in self.data:

            row = self.data[ticker].iloc[-1]

            if row is None:
                continue

            if row["flag"]:

                if dist_low < row["Dist25"] < dist_high:
                    #if row['flag_counter']>0 and row["Angle"]>20 :
                    #if row['flag_counter']>2 and row["Angle"]>0 and row["Angle_flag"]:
                    if row['flag_counter']>5 and row["Angle"]>20 and row["Angle_flag"]:
                    #if row['flag_counter']>2 and row["Angle"]>10:
                    # if (
                    #     row["flag_counter"] > 2
                    #     and row["Dist25_Change"] > 0
                    # ):
                        buy_list[ticker] = row["Dist25"]

        buy_list = dict(
            sorted(
                buy_list.items(),
                key=lambda x: x[1],reverse=True
            )
        )

        return list(buy_list.keys())

    # =========================================================================
    # Sell stock
    # =========================================================================
    def sell_stock(self, ticker, qty):
        
        temp= self.portfolio[ticker]
        temp['qty']=temp['qty']-qty
        #temp['value']= temp['price']*temp['qty']
        
        self.portfolio[ticker]=temp
        self.portfolio={i:j for i,j in self.portfolio.items() if j['qty']>0}
        self.update_current_portfolio()
        #sold = self.portfolio.pop(ticker)

        #return sold

    # =========================================================================
    # Buy stock
    # =========================================================================
    def buy_stock(self, ticker, qty):
        
        if ticker in self.portfolio:
            bought= self.portfolio[ticker]
            bought['qty']=bought['qty']+qty
            #bought['value']= bought['value']+ price*qty
            
            
        else:    
            bought = {
                "price": 0,
                "highest_price": 0,
                "qty": qty,
                "value": 0,
                "sl": 0,
            }

        self.portfolio[ticker] = bought
        self.update_current_portfolio()

        return self.portfolio
    # =============================================================================
    #     save updated portfolio
    # =============================================================================
    
    def save_portfolio(self):
        
        with open("data\portfolio.json", "w") as f:
            json.dump(self.portfolio, f, indent=4, default=lambda x: x.item() if isinstance(x, np.generic) else x)
            
 
    # =============================================================================
    # get sell list    
    # =============================================================================
    def get_sell_list(self):
        """
        Find all stocks that should be sold.

        Returns
        -------
        list
        """

        sell = []

        for ticker in self.portfolio:
            
            row = self.data[ticker].iloc[-1]

            #if row["Close"] < row['SMA25']*.98 and row['anti_flag_counter']>5 and row['Angle']<0:
            #if row['anti_flag_counter']>10 and row['Angle']<20:
            #if (row['anti_flag_counter']>10 and row['Angle']<20) or self.portfolio[ticker]['price']<self.portfolio[ticker]['sl']:
            if row['anti_flag_counter']>7 and row['Angle']<20 and row['Angle_flag']==False:
            #if row["price"] <= row['sl']:

                sell.append(ticker)

        return sell
    
    def buy_rec(self):

        sell_list = self.get_sell_list()
        
        sell_rec={i:pm.portfolio[i]['qty'] for i in sell_list}
        sell_rec=pd.DataFrame(sell_rec.items())
        if len(sell_rec)>0:
            sell_rec.columns=['Stock', 'Qty']
            sell_rec['Action']='Sell'
        else:
            sell_rec=pd.DataFrame(columns=['Stock', 'Qty','Action'])
        
        sell_value= sum([self.portfolio[i]['value'] for i in sell_list])
        
        
        
        allocation_per_stock=sum([self.portfolio[i]['value'] for i in self.portfolio])/self.max_pos
        
        money=sell_value
        
        buy_rec= {}
        buy_list = self.get_buy_candidates(2,5)
            
            
        for buy in buy_list:
            #break
            price= self.data[buy]['Close'].iloc[-1]
            
            if money > allocation_per_stock:
        
                qty = int(allocation_per_stock // price)
                
                money-=price*qty
                
                buy_rec[buy]=qty
            
            else:
                
                qty = int(money // price)
                
                buy_rec[buy]=qty
                
        buy_rec=pd.DataFrame(buy_rec.items())
        if len(buy_rec)>0 and len(self.portfolio)<self.max_pos:
            buy_rec.columns=['Stock', 'Qty']
            buy_rec['Action']='Buy'
        else:
            buy_rec=pd.DataFrame(columns=['Stock', 'Qty','Action'])
            
        
        rec=pd.concat([sell_rec,buy_rec])
        
        return rec
        
            
            
        
    