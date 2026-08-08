# -*- coding: utf-8 -*-
"""
Created on Mon Aug  3 21:36:52 2026

@author: tarun
"""

# -*- coding: utf-8 -*-
"""
Created on Mon Aug  3 21:19:27 2026

@author: tarun


#update highest price in such a way that it shows the highest price since purchase. if run eveyday it will get updated. if not run in some days it might miss the day highs reached
since we are just looking at the current day high

make a similar one for hour level so that can be used on fno for fno calls!



#update required: sell does not have quantity
buy updates the stock entry does not append the adds
"""

import numpy as np
import json

class PortfolioManager:

    def __init__(self, data, portfolio, stoploss, pf_start_date):
        self.data = data
        self.pf_start_date=pf_start_date
        self.stoploss = stoploss
        self.portfolio = portfolio
        self.hp = self.get_highest_prices()

   
    
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
                    if (
                        row["flag_counter"] > 5
                        and row["Dist25_Change"] > 0
                    ):
                        buy_list[ticker] = row["Dist25"]

        buy_list = dict(
            sorted(
                buy_list.items(),
                key=lambda x: x[1]
            )
        )

        return list(buy_list.keys())

    # =========================================================================
    # Sell stock
    # =========================================================================
    def sell_stock(self, ticker):

        sold = self.portfolio.pop(ticker)

        return sold

    # =========================================================================
    # Buy stock
    # =========================================================================
    def buy_stock(self, ticker, price, qty):

        bought = {
            "price": price,
            "highest_price": price,
            "qty": qty,
            "value": price * qty,
            "sl": np.ceil(price * (100 - self.stoploss) / 100),
        }

        self.portfolio[ticker] = bought

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
            row= self.portfolio[ticker]

            
            if row["price"] <= row['sl']:

                sell.append(ticker)

        return sell
    
    
    
    
    