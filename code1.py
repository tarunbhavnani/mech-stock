# -*- coding: utf-8 -*-
"""
Created on Sat Aug  1 19:15:40 2026

@author: tarun
"""
import pandas as pd
import yfinance as yf
import numpy as np
from config import *

TICKERS = ['TATACONSUM.NS','BAJFINANCE.NS','WIPRO.NS','ASIANPAINT.NS','HINDALCO.NS',
'CIPLA.NS','ETERNAL.NS','APOLLOHOSP.NS','DRREDDY.NS','SHRIRAMFIN.NS',
'BHARTIARTL.NS','HDFCLIFE.NS','TRENT.NS','EICHERMOT.NS','NESTLEIND.NS',
'INDIGO.NS','HDFCBANK.NS','RELIANCE.NS','SUNPHARMA.NS','BAJAJFINSV.NS',
'MAXHEALTH.NS','M&M.NS','MARUTI.NS','TITAN.NS','BAJAJ-AUTO.NS','ADANIPORTS.NS',
'SBILIFE.NS','SBIN.NS','ADANIENT.NS','POWERGRID.NS','JIOFIN.NS','HCLTECH.NS',
'HINDUNILVR.NS','JSWSTEEL.NS','TCS.NS','COALINDIA.NS','INFY.NS','ICICIBANK.NS',
'ITC.NS','AXISBANK.NS','ULTRACEMCO.NS','ONGC.NS','BEL.NS','NTPC.NS','KOTAKBANK.NS']





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
        
        
        df["day"] = range(1, len(df) + 1)

        data[ticker] = df

    return data





# def prepare_rebalance_data(data,
#                            rebalance_frequency=10,
#                            stop_loss_pct=0.95):
#     """
#     Prepare dataframe used by the backtest.

#     Keeps only rebalance dates and creates the
#     ratcheting trailing stop.

#     Returns
#     -------
#     dict
#     """

#     data = {}

#     for ticker in data:

#         df = data[ticker].copy()

#         df["day"] = range(1, len(df) + 1)

#         # keep only rebalance dates

#         jk = df[df["day"] % rebalance_frequency == 0].copy()
#         #jk=df.copy()

#         # buy signal

#         jk["flag"] = jk["Close"] > jk["SMA25"]

#         # raw stop

#         jk["limit"] = jk["Close"] * stop_loss_pct

#         # ratcheting stop

#         trail = []

#         for i in range(len(jk)):

#             if i == 0:
#                 trail.append(jk["limit"].iloc[0])

#             else:
#                 trail.append(
#                     max(
#                         trail[-1],
#                         jk["limit"].iloc[i]
#                     )
#                 )

#         jk["limit_updated"] = trail

#         data[ticker] = jk[
#             [
#                 "Close",
#                 "date",
#                 "Ticker",
#                 "SMA25",
#                 "Dist25",
#                 "day",
#                 "flag",
#                 "limit_updated",
#             ]
#         ]

#     return data


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
                            capital,
                            max_positions,
                            allocation_per_stock,
                            stoploss):
    """
    Build initial portfolio.

    Returns
    -------
    portfolio
    cash
    owned
    """

    portfolio = {}

    money = capital

    buy_list = buy_list[:max_positions]

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

        money -= cost

    owned = list(portfolio.keys())

    return portfolio, money, owned

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
                  money):
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

    owned = list(portfolio.keys())

    return portfolio, money, owned

def execute_buys(data,
                 portfolio,
                 buy_list,
                 day,
                 money,
                 max_positions,
                 allocation_per_stock, stoploss):
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

        money -= cost

    owned = list(portfolio.keys())

    return portfolio, money, owned



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

def run_backtest(data,first_day,capital,
                 max_positions,allocation_per_stock,
                 stoploss, dist_low, dist_high):

    max_day = max(df["day"].max() for df in data.values())
    
    owned=[]


    history = []

    for day in range(first_day, max_day + 1):
        
        print('.', end=" ", flush=True)
        
        if len(owned)==0:
            
            buy_list = get_buy_candidates(data, day, owned, dist_low, dist_high)
            
            portfolio, money, owned = build_initial_portfolio(data, buy_list, day, capital, max_positions, allocation_per_stock, stoploss)
        
        else:

            
            #get marhet value
            portfolio = mark_to_market(portfolio, data, day, stoploss)
            
            #get sell candidates
            sell_list = get_sell_list(portfolio, data, day)
            
            #sell
            portfolio, money, owned = execute_sells(portfolio, sell_list, data, day, money)
            
            #buy new
            if len(owned) < max_positions:
                
                #get buy list
                buy_list = get_buy_candidates(data, day, owned, dist_low, dist_high)
                
                #buy
                portfolio, money, owned = execute_buys(data, portfolio, buy_list, day, money, max_positions, allocation_per_stock, stoploss)
    
            
        #get marhet value
        portfolio = mark_to_market(portfolio, data, day, stoploss)
            
        #get portfolio value
        portfolio_value, equity = calculate_portfolio_value(portfolio, money)
            
        #get date
        sample = get_row(next(iter(data.values())),day)
            
        current=[i+'-'+str(int(portfolio[i]['price'])) for i in portfolio]

        history.append({
            "day": day,
            "date": sample["date"],
            "cash": money,
            "portfolio": portfolio_value,
            "equity": equity,
            "positions": len(portfolio),
            "current":current
            
        })

    history = pd.DataFrame(history)

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

# data = download_data(TICKERS)

# data = prepare_indicators(data)

# data = prepare_rebalance_data(data)

# buy_list = get_buy_candidates(
#     data,
#     first_day,
#     owned=[]
# )

# portfolio, money, owned = build_initial_portfolio(
#     data,
#     buy_list,
#     first_day
# )

# for day in range(first_day + 10,
#                  max_day + 1,
#                  10):

#     # Find sells

#     sell_list = get_sell_list(
#         portfolio,
#         data,
#         day
#     )

#     # Execute sells

#     portfolio, money, owned = execute_sells(
#         portfolio,
#         sell_list,
#         data,
#         day,
#         money
#     )

#     # Only look for buys if something was sold
#     # (same logic as your original code)

#     if sell_list:

#         buy_list = get_buy_candidates(
#             data,
#             day,
#             owned
#         )

#         portfolio, money, owned = execute_buys(
#             data,
#             portfolio,
#             buy_list,
#             day,
#             money
#         )
#         value= sum([portfolio[i]['price']*portfolio[i]['qty'] for i in portfolio])
        
#         print(day,"---", value+money)


