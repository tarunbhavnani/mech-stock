# -*- coding: utf-8 -*-
"""
Created on Tue Aug 11 18:50:09 2026

@author: tarun
DAY N
 │
 ├── Portfolio empty?
 │      │
 │      └── YES
 │           │
 │           └── Find buy candidates
 │                 │
 │                 ├── Nifty anti_flag_counter <= 5
 │                 ├── flag = True
 │                 ├── Dist25 within range
 │                 ├── flag_counter > 5
 │                 └── Angle > 10
 │
 │           Sort by Dist25 DESC
 │           Buy up to MAX_POSITIONS
 │
 │
 └── Portfolio not empty
        │
        ├── Mark to market
        │
        ├── Update trailing SL
        │
        ├── Find sells
        │      │
        │      └── Close < SMA25 × 0.98
        │          AND anti_flag_counter > 5
        │          AND Angle < 0
        │
        ├── Sell at Close
        │
        ├── Positions < MAX_POSITIONS?
        │      │
        │      └── YES
        │           │
        │           └── Find new buy candidates
        │               Buy available slots
        │
        └── Mark to market again
"""


import pandas as pd
import yfinance as yf
import numpy as np
#from config import *
import copy
import random



import numpy as np
import json

class PortfolioManager:

    def __init__(self, data, nifty,stoploss, first_day, money, max_positions,dist_low,dist_high):
        self.data = data
        self.first_day=first_day
        self.stoploss = stoploss
        self.portfolio = {}
        self.owned=[]
        self.money=money
        self.max_positions=max_positions
        self.dist_low=dist_low
        self.dist_high=dist_high
        self.nifty=nifty

   






    def get_row(self, df, day):
    
        row = df.loc[df["day"] == day]
    
        if row.empty:
            return None
    
        return row.iloc[0]





    def build_initial_portfolio(self,day):
        """
        Build initial portfolio.
    
        Returns
        -------
        portfolio
        cash
        owned
        """
    
        
    
        #money = capital
        buy_list = self.get_buy_candidates(day)
        buy_list = buy_list[:self.max_positions]
        
        allocation_per_stock=np.floor(self.money/self.max_positions)
        
        
        bought=[]
    
        for ticker in buy_list:
    
            row = self.get_row(self.data[ticker], day)
    
            if row is None:
                continue
    
            price = np.floor(row["Close"])
            
            sl=np.ceil(price*(100-self.stoploss)/100)
    
            qty = int(allocation_per_stock // price)
    
            cost = qty * price
    
            if cost > self.money:
                continue
    
            self.portfolio[ticker] = {
    
                "price": price,
                "bp": price,
    
                "qty": qty,
    
                "value": cost,
                "buy_day":day,
                "sl":sl
    
            }
    
            self.money -= cost
            
            bought.append((ticker, price, qty))
    
        self.owned = list(self.portfolio.keys())
    
        return  bought
    
    def get_buy_candidates(self,day):
                           
        """
        Find stocks eligible for buying.
    
        Returns
        -------
        list
        """
        # try:
        #     nifty_flag,_=self.get_nifty_flag(day)
        # except:
        #     nifty_flag=0
        
        # if nifty_flag<4:
        #     return []
    
        buy_list = {}
    
        for ticker in self.data:
    
            if ticker in self.owned:
                continue
    
            row = self.get_row(self.data[ticker], day)
    
            if row is None:
                continue
    
            if row["flag"]:
    
                if self.dist_low < row["Dist25"] < self.dist_high:
               
                    #if row["Angle"]>30 :
                    
                    if row['flag_counter']>0 and row["Angle"]>20 :
               
                        buy_list[ticker] = row["Dist25"]
    
        buy_list = dict(
            sorted(
                buy_list.items(),
                key=lambda x: x[1],reverse=True
            )
        )
    
        return list(buy_list.keys())




    def get_sell_list(self,day):
        """
        Find all stocks that should be sold.
    
        Returns
        -------
        list
        """
    
        sell = []
    
        for ticker in self.portfolio:
    
            row = self.get_row(self.data[ticker], day)
    
            if row is None:
                continue
    
            #if row["Close"] < portfolio[ticker]['sl']:
            #if day-self.portfolio[ticker]['buy_day']>30:
            #if row["Close"] < row['SMA25']*.98 and row['anti_flag_counter']>9:
            #if row["Close"] < row['SMA25']*.98 and row['anti_flag_counter']>5 and row['Angle']<0:
            if row['anti_flag_counter']>10 and row['Angle']<20:
            #if ((row['anti_flag_counter'] > 10 and row['Angle'] < 20) or row['Close'] < self.portfolio[ticker]['sl']):
                
                sell.append(ticker)
            
            
    
            
            # if row['Close']>10 and self.portfolio[ticker]['sl']:
            #     sell.append(ticker)
            
            # if row['Close']*self.portfolio[ticker]['qty']<self.portfolio[ticker]['bp']*self.portfolio[ticker]['qty']*.9:
            #     sell.append(ticker)
            
            # if day-self.portfolio[ticker]['buy_day']>30:
            #     if row['Close']*self.portfolio[ticker]['qty']<self.portfolio[ticker]['bp']*self.portfolio[ticker]['qty']*1.05:
            #         sell.append(ticker)
                
            
    
        return list(set(sell))


    def execute_sells(self,
                      sell_list,
                      
                      day
                      ):
        """
        Execute all sells.
    
        Returns
        -------
        portfolio
        money
        owned
        """
        sold=[]
        for ticker in sell_list:
    
            row = self.get_row(self.data[ticker], day)
    
            if row is None:
                continue
    
            sell_price = row["Close"]
    
            qty = self.portfolio[ticker]["qty"]
    
            self.money += sell_price * qty
            
            sold.append((ticker, sell_price, qty))
    
            temp=self.portfolio.pop(ticker)
            #print("sell:", temp)
            
    
        self.owned = list(self.portfolio.keys())
    
    
        return sold


    def sell_all(self,day):
        """
        Execute all sells.
    
        Returns
        -------
        portfolio
        money
        owned
        """
        sold=[]
        
        for ticker in self.portfolio:
    
            row = self.get_row(self.data[ticker], day)
    
            if row is None:
                continue
    
            sell_price = row["Close"]
    
            qty = self.portfolio[ticker]["qty"]
    
            self.money += sell_price * qty
            
            sold.append((ticker, sell_price, qty))
    
            #temp=portfolio.pop(ticker)
            #print("sell:", temp)
            
        return  sold


    def execute_buys(self,buy_list,day):
        """
        Buy new stocks.
    
        Returns
        -------
        portfolio
        money
        owned
        """
    
        #owned = list(portfolio.keys())
    
        available = self.max_positions - len(self.owned)
        
        
    
        if available <= 0:
            return 
        
        allocation_per_stock=np.floor(self.money/available)
        
        buy_list = buy_list[:available]
        bought=[]
    
        for ticker in buy_list:
    
            row = self.get_row(self.data[ticker], day)
    
            if row is None:
                continue
    
            price = row["Close"]
            
            if self.money>allocation_per_stock:
    
                qty = int(allocation_per_stock // price)
            else:
                qty = int(self.money // price)
            
    
            if qty <= 0:
                continue
    
            cost = qty * price
    
            if cost > self.money:
                continue
            
            sl=np.ceil(price*(100-self.stoploss)/100)
    
            self.portfolio[ticker] = {
    
                "price": price,
                "bp": price,
    
                "qty": qty,
    
                "value": cost,
                
                "buy_day":day,
                
                "sl":sl
    
            }
            #print("Buy:",portfolio[ticker])
    
            self.money -= cost
            
            bought.append((ticker, price, qty))
    
        
    
        return bought


    def get_nifty_flag(self,day):
        row = self.get_row(self.nifty, day)
        #return row['Angle']
        return row['flag_counter'], row['anti_flag_counter']
    
        



    def mark_to_market(self,day):
        """
        Update portfolio prices to current day.
    
        Returns
        -------
        portfolio
        """
    
        for ticker in self.portfolio:
            
            row = self.get_row(self.data[ticker], day)
    
            if row is None:
                continue
    
            self.portfolio[ticker]["price"] = row["Close"]
            self.portfolio[ticker]["value"] = (
                row["Close"] *
                self.portfolio[ticker]["qty"]
            )
            
            new_sl=np.floor(row["High"]*(100-self.stoploss)/100)
            
            if new_sl>self.portfolio[ticker]["sl"]:
                self.portfolio[ticker]["sl"]=new_sl
    
        


    def calculate_portfolio_value(self):
        """
        Calculate portfolio value.
    
        Returns
        -------
        portfolio_value
        total_equity
        """
    
        portfolio_value = sum(
            position["value"]
            for position in self.portfolio.values()
        )
    
        total_equity = portfolio_value + self.money
    
        return portfolio_value, total_equity




    def run_backtest(self):
    
        max_day = max(df["day"].max() for df in self.data.values())
        
        
        all_bought={}
        all_sold={}
    
    
        history = []
    
        for day in range(self.first_day, max_day + 1):
            
            print(day, end=", ", flush=True)
            
            
            
            if len(self.owned)==0 :
                
                
                
                bought = self.build_initial_portfolio(day)
                all_bought[day]=bought
            
                
            
            else:
    
                
                #get marhet value
                self.mark_to_market(day)
                
                #get sell candidates
                sell_list = self.get_sell_list(day)
                
                #sell
                sold = self.execute_sells(sell_list, day)
                all_sold[day]=sold
                
                
                #buy new
                if len(self.owned) < self.max_positions :
                    
                    #get buy list
                    buy_list = self.get_buy_candidates(day)
                    
                    
                    #buy
                    bought = self.execute_buys( buy_list, day)
                    all_bought[day]=bought
        
                
                #get marhet value
                self.mark_to_market(day)
                    
            #get portfolio value
            portfolio_value, equity = self.calculate_portfolio_value()
                    
                #get date
                #sample = get_row(next(iter(data.values())),day)
                
            current=[i+'-'+str(int(self.portfolio[i]['price']))+'-'+str(int(self.portfolio[i]['sl'])) for i in self.portfolio]
    
            history.append({
                "day": day,
            #    "date": sample["date"],
                "cash": self.money,
                "portfolio": portfolio_value,
                "equity": equity,
                "positions": len(self.portfolio),
                "current":copy.deepcopy(current)
                
            })
    
        history = pd.DataFrame(history)
        
        history=self.get_date(history)
    
        return history, all_bought, all_sold


    def get_date(self,history):
    
        date_len=max([len(self.data[i]) for i in self.data])
        
        ticker=[i for i in self.data if len(self.data[i])==date_len][0]
        
        temp=self.data[ticker][['date', 'day']]
        
        history= history.merge(temp, on='day', how='left')
        
        return history




def performance_metrics(history,
                        initial_capital):

    history = history.copy()

    history["Peak"] = history["equity"].cummax()

    history["Drawdown"] = (
        history["equity"]
        - history["Peak"]
    ) / history["Peak"]

    max_drawdown = history["Drawdown"].min()

    years = (
        history["date"].iloc[-1]
        - history["date"].iloc[0]
    ).days / 365.25

    ending_value = history["equity"].iloc[-1]

    cagr = (
        (ending_value / initial_capital)
        ** (1 / years)
        - 1
    )

    print("=" * 50)
    print(f"Initial Capital : {initial_capital:,.0f}")
    print(f"Ending Equity   : {ending_value:,.0f}")
    print(f"CAGR            : {cagr:.2%}")
    print(f"Max Drawdown    : {max_drawdown:.2%}")
    print("=" * 50)

    return {
        "Ending Equity": ending_value,
        "CAGR": cagr,
        "Max Drawdown": max_drawdown
    }


import matplotlib.pyplot as plt

def plot_equity_curve(history):

    plt.figure(figsize=(12,6))

    plt.plot(
        history["date"],
        history["equity"],
        linewidth=2
    )

    plt.title("Portfolio Equity Curve")

    plt.xlabel("Date")

    plt.ylabel("Portfolio Value")

    plt.grid(True)

    plt.show()
    
    

# =============================================================================
# 
# =============================================================================

def get_transactions(all_bought, all_sold):
    final=[]
    for i in all_bought:
        for j in all_bought[i]:
            final.append((i,'buy', j[0],j[1],j[2]))
    
    
    for i in all_sold:
        for j in all_sold[i]:
            final.append((i,'sell', j[0],j[1],j[2]))
    
    
    final=pd.DataFrame(final)
    final.columns=['day','action', 'ticker', 'price', 'qty']
    return final