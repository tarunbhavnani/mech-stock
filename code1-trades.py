# -*- coding: utf-8 -*-
"""
Created on Sun Aug  2 19:47:59 2026

@author: tarun
"""

# -*- coding: utf-8 -*-
"""
Created on Sat Aug  1 19:15:40 2026

@author: tarun
"""
import pandas as pd
import yfinance as yf
import numpy as np
from config import *
import copy





def download_data(tickers,
                  start_date,
                  auto_adjust=True):
    """
    Download historical OHLCV data for all tickers.

    Returns
    -------
    dict
        {
            ticker : dataframe
        }
    """

    data = {}

    for ticker in tickers:

        print(f"Downloading {ticker}")

        try:

            df = yf.download(
                ticker,
                start=start_date,
                progress=False,
                auto_adjust=auto_adjust
            )

            if df.empty:
                print(f"{ticker} : No Data")
                continue

            # Flatten MultiIndex if required
            if hasattr(df.columns, "levels"):
                df.columns = df.columns.get_level_values(0)

            df = df[
                [
                    "Close",
                    "High",
                    "Low",
                    "Open",
                    "Volume"
                ]
            ].copy()

            df["date"] = df.index
            df.reset_index(drop=True, inplace=True)

            df["Ticker"] = ticker

            df.sort_values("date", inplace=True)

            data[ticker] = df

        except Exception as e:

            print(f"{ticker} : {e}")

    return data

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

def get_day(data):
    max_len=max([len(data[i]) for i in data])
    temp_stock= [i for i in data if len(data[i])==max_len][0]
    temp_data= copy.deepcopy(data[temp_stock])
    temp_data["day"]= range(1, len(temp_data) + 1)
    temp_data=temp_data[['date', 'day']]
    
    for i in data:
        data[i]= data[i].merge(temp_data, on='date', how='left')
    
    return data

def prepare_indicators(data):
    """
    Adds all indicators to every dataframe.

    Parameters
    ----------
    data : dict

    Returns
    -------
    dict
    """

    for ticker in data:

        df = data[ticker]

        # Moving averages

        df["SMA25"] = df["Close"].rolling(25).mean()
        df["SMA100"] = df["Close"].rolling(100).mean()
        df["SMA200"] = df["Close"].rolling(200).mean()

        # Volume average

        df["VOL25"] = df["Volume"].rolling(25).mean()

        # Distance from moving averages

        df["Dist25"] = (
            (df["Close"] - df["SMA25"])
            / df["SMA25"]
            * 100
        )

        df["Dist100"] = (
            (df["Close"] - df["SMA100"])
            / df["SMA100"]
            * 100
        )

        df["Dist200"] = (
            (df["Close"] - df["SMA200"])
            / df["SMA200"]
            * 100
        )
        
        #rising or falling
        df["Dist25_Change"] = df["Dist25"].diff()
        
        
        # buy signal

        df["flag"] = df["Close"] > df["SMA25"]
        
        df=flag_counter(df)
        

        data[ticker] = df

    return data




def get_row(df, day):

    row = df.loc[df["day"] == day]

    if row.empty:
        return None

    return row.iloc[0]


def get_buy_candidates(data,
                       day,
                       owned,
                       dist_low,
                       dist_high):
    """
    Find stocks eligible for buying.

    Returns
    -------
    list
    """

    buy_list = {}

    for ticker in data:

        if ticker in owned:
            continue

        row = get_row(data[ticker], day)

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


def build_initial_portfolio(data,
                            buy_list,
                            first_day,
                            money,
                            max_positions,
                            allocation_per_stock,
                            stoploss,trades):
    """
    Build initial portfolio.

    Returns
    -------
    portfolio
    cash
    owned
    """

    portfolio = {}

    #money = capital

    buy_list = buy_list[:max_positions]
    
    allocation_per_stock=np.floor(money/max_positions)

    for ticker in buy_list:

        row = get_row(data[ticker], first_day)

        if row is None:
            continue

        price = np.floor(row["Close"])
        
        sl=np.ceil(price*(100-stoploss)/100)

        qty = int(allocation_per_stock // price)

        cost = qty * price

        if cost > money:
            continue

        portfolio[ticker] = {

            "price": price,

            "qty": qty,

            "value": cost,
            "sl":sl

        }
        trades.append(('buy',ticker, price, qty ))

        money -= cost

    owned = list(portfolio.keys())

    return portfolio, money, owned, trades

def get_sell_list(portfolio,
                  data,
                  day):
    """
    Find all stocks that should be sold.

    Returns
    -------
    list
    """

    sell = []

    for ticker in portfolio:

        row = get_row(data[ticker], day)

        if row is None:
            continue

        if row["Close"] < portfolio[ticker]['sl']:

            sell.append(ticker)

    return sell



def execute_sells(portfolio,
                  sell_list,
                  data,
                  day,
                  money, trades):
    """
    Execute all sells.

    Returns
    -------
    portfolio
    money
    owned
    """

    for ticker in sell_list:

        row = get_row(data[ticker], day)

        if row is None:
            continue

        sell_price = row["Close"]

        qty = portfolio[ticker]["qty"]

        money += sell_price * qty

        portfolio.pop(ticker)
        
        trades.append(('sell',ticker, sell_price, qty ))

    owned = list(portfolio.keys())

    return portfolio, money, owned, trades

def execute_buys(data,
                 portfolio,
                 buy_list,
                 day,
                 money,
                 max_positions,
                 allocation_per_stock, stoploss, trades):
    """
    Buy new stocks.

    Returns
    -------
    portfolio
    money
    owned
    """

    owned = list(portfolio.keys())

    available = max_positions - len(owned)
    
    allocation_per_stock=np.floor(money/available)

    if available <= 0:
        return portfolio, money, owned

    buy_list = buy_list[:available]

    for ticker in buy_list:

        row = get_row(data[ticker], day)

        if row is None:
            continue

        price = row["Close"]
        
        if money>allocation_per_stock:

            qty = int(allocation_per_stock // price)
        else:
            qty = int(money // price)
        

        if qty <= 0:
            continue

        cost = qty * price

        if cost > money:
            continue
        
        sl=np.ceil(price*(100-stoploss)/100)

        portfolio[ticker] = {

            "price": price,

            "qty": qty,

            "value": cost,
            
            "sl":sl

        }
        trades.append(('buy',ticker, price, qty ))

        money -= cost

    owned = list(portfolio.keys())

    return portfolio, money, owned, trades



def mark_to_market(portfolio,
                   data,
                   day,stoploss):
    """
    Update portfolio prices to current day.

    Returns
    -------
    portfolio
    """

    for ticker in portfolio:

        row = get_row(data[ticker], day)

        if row is None:
            continue

        portfolio[ticker]["price"] = row["Close"]
        portfolio[ticker]["value"] = (
            row["Close"] *
            portfolio[ticker]["qty"]
        )
        
        new_sl=np.ceil(row["Close"]*(100-stoploss)/100)
        
        if new_sl>portfolio[ticker]["sl"]:
            portfolio[ticker]["sl"]=new_sl

    return portfolio


def calculate_portfolio_value(portfolio,
                              money):
    """
    Calculate portfolio value.

    Returns
    -------
    portfolio_value
    total_equity
    """

    portfolio_value = sum(
        position["value"]
        for position in portfolio.values()
    )

    total_equity = portfolio_value + money

    return portfolio_value, total_equity

def run_backtest(data,first_day,money,
                 max_positions,allocation_per_stock,
                 stoploss, dist_low, dist_high):
    
    trades=[]
    

    max_day = max(df["day"].max() for df in data.values())
    
    owned=[]


    history = []

    for day in range(first_day, max_day + 1):
        
        print(day, end=", ", flush=True)
        
        if len(owned)==0:
            
            buy_list = get_buy_candidates(data, day, owned, dist_low, dist_high)
            
            portfolio, money, owned,trades = build_initial_portfolio(data, buy_list, day, money, max_positions, allocation_per_stock, stoploss,trades)
        
        else:

            
            #get marhet value
            portfolio = mark_to_market(portfolio, data, day, stoploss)
            
            #get sell candidates
            sell_list = get_sell_list(portfolio, data, day)
            
            #sell
            portfolio, money, owned ,trades= execute_sells(portfolio, sell_list, data, day, money,trades)
            
            #buy new
            if len(owned) < max_positions:
                
                #get buy list
                buy_list = get_buy_candidates(data, day, owned, dist_low, dist_high)
                
                #buy
                portfolio, money, owned,trades = execute_buys(data, portfolio, buy_list, day, money, max_positions, allocation_per_stock, stoploss,trades)
    
            
            #get marhet value
            portfolio = mark_to_market(portfolio, data, day, stoploss)
                
        #get portfolio value
        portfolio_value, equity = calculate_portfolio_value(portfolio, money)
                
            #get date
            #sample = get_row(next(iter(data.values())),day)
            
        current=[i+'-'+str(int(portfolio[i]['price']))+'-'+str(int(portfolio[i]['sl'])) for i in portfolio]

        history.append({
            "day": day,
        #    "date": sample["date"],
            "cash": money,
            "portfolio": portfolio_value,
            "equity": equity,
            "positions": len(portfolio),
            "current":copy.deepcopy(current)
            
        })

    history = pd.DataFrame(history)

    return history,trades

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
    
    
def get_date(history, data):

    date_len=max([len(data[i]) for i in data])
    
    ticker=[i for i in data if len(data[i])==date_len][0]
    
    temp=data[ticker][['date', 'day']]
    
    history= history.merge(temp, on='day', how='left')
    
    return history
# =============================================================================
# 
# =============================================================================

