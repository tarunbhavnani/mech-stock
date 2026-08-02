# -*- coding: utf-8 -*-
"""
Created on Sat Aug  1 19:15:40 2026

@author: tarun
"""
import pandas as pd
import yfinance as yf

TICKERS = ['TATACONSUM.NS','BAJFINANCE.NS','WIPRO.NS','ASIANPAINT.NS','HINDALCO.NS',
'CIPLA.NS','ETERNAL.NS','APOLLOHOSP.NS','DRREDDY.NS','SHRIRAMFIN.NS',
'BHARTIARTL.NS','HDFCLIFE.NS','TRENT.NS','EICHERMOT.NS','NESTLEIND.NS',
'INDIGO.NS','HDFCBANK.NS','RELIANCE.NS','SUNPHARMA.NS','BAJAJFINSV.NS',
'MAXHEALTH.NS','M&M.NS','MARUTI.NS','TITAN.NS','BAJAJ-AUTO.NS','ADANIPORTS.NS',
'SBILIFE.NS','SBIN.NS','ADANIENT.NS','POWERGRID.NS','JIOFIN.NS','HCLTECH.NS',
'HINDUNILVR.NS','JSWSTEEL.NS','TCS.NS','COALINDIA.NS','INFY.NS','ICICIBANK.NS',
'ITC.NS','AXISBANK.NS','ULTRACEMCO.NS','ONGC.NS','BEL.NS','NTPC.NS','KOTAKBANK.NS']


def download_data(tickers,
                  start_date="2015-01-01",
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

        data[ticker] = df

    return data





def prepare_rebalance_data(data,
                           rebalance_frequency=10,
                           stop_loss_pct=0.95):
    """
    Prepare dataframe used by the backtest.

    Keeps only rebalance dates and creates the
    ratcheting trailing stop.

    Returns
    -------
    dict
    """

    data1 = {}

    for ticker in data:

        df = data[ticker].copy()

        df["day"] = range(1, len(df) + 1)

        # keep only rebalance dates

        jk = df[df["day"] % rebalance_frequency == 0].copy()
        #jk=df.copy()

        # buy signal

        jk["flag"] = jk["Close"] > jk["SMA25"]

        # raw stop

        jk["limit"] = jk["Close"] * stop_loss_pct

        # ratcheting stop

        trail = []

        for i in range(len(jk)):

            if i == 0:
                trail.append(jk["limit"].iloc[0])

            else:
                trail.append(
                    max(
                        trail[-1],
                        jk["limit"].iloc[i]
                    )
                )

        jk["limit_updated"] = trail

        data1[ticker] = jk[
            [
                "Close",
                "date",
                "Ticker",
                "SMA25",
                "Dist25",
                "day",
                "flag",
                "limit_updated",
            ]
        ]

    return data1


def get_row(df, day):

    row = df.loc[df["day"] == day]

    if row.empty:
        return None

    return row.iloc[0]


def get_buy_candidates(data1,
                       day,
                       owned,
                       dist_low=2,
                       dist_high=5):
    """
    Find stocks eligible for buying.

    Returns
    -------
    list
    """

    buy_list = {}

    for ticker in data1:

        if ticker in owned:
            continue

        row = get_row(data1[ticker], day)

        if row is None:
            continue

        if row["flag"]:

            if dist_low < row["Dist25"] < dist_high:

                buy_list[ticker] = row["Dist25"]

    buy_list = dict(
        sorted(
            buy_list.items(),
            key=lambda x: x[1]
        )
    )

    return list(buy_list.keys())


def build_initial_portfolio(data1,
                            buy_list,
                            first_day,
                            capital=1000000,
                            max_positions=5,
                            allocation_per_stock=200000):
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

        row = get_row(data1[ticker], first_day)

        if row is None:
            continue

        price = row["Close"]

        qty = int(allocation_per_stock // price)

        cost = qty * price

        if cost > money:
            continue

        portfolio[ticker] = {

            "price": price,

            "qty": qty,

            "value": cost

        }

        money -= cost

    owned = list(portfolio.keys())

    return portfolio, money, owned

def get_sell_list(portfolio,
                  data1,
                  day):
    """
    Find all stocks that should be sold.

    Returns
    -------
    list
    """

    sell = []

    for ticker in portfolio:

        row = get_row(data1[ticker], day)

        if row is None:
            continue

        if row["Close"] < row["limit_updated"]:

            sell.append(ticker)

    return sell

def execute_sells(portfolio,
                  sell_list,
                  data1,
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

        row = get_row(data1[ticker], day)

        if row is None:
            continue

        sell_price = row["Close"]

        qty = portfolio[ticker]["qty"]

        money += sell_price * qty

        portfolio.pop(ticker)

    owned = list(portfolio.keys())

    return portfolio, money, owned

def execute_buys(data1,
                 portfolio,
                 buy_list,
                 day,
                 money,
                 max_positions=5,
                 allocation_per_stock=200000):
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

        row = get_row(data1[ticker], day)

        if row is None:
            continue

        price = row["Close"]

        qty = int(allocation_per_stock // price)

        if qty <= 0:
            continue

        cost = qty * price

        if cost > money:
            continue

        portfolio[ticker] = {

            "price": price,

            "qty": qty,

            "value": cost

        }

        money -= cost

    owned = list(portfolio.keys())

    return portfolio, money, owned


def mark_to_market(portfolio,
                   data1,
                   day):
    """
    Update portfolio prices to current day.

    Returns
    -------
    portfolio
    """

    for ticker in portfolio:

        row = get_row(data1[ticker], day)

        if row is None:
            continue

        portfolio[ticker]["price"] = row["Close"]
        portfolio[ticker]["value"] = (
            row["Close"] *
            portfolio[ticker]["qty"]
        )

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

def run_backtest(data1,
                 first_day,
                 capital=1000000,
                 max_positions=5,
                 allocation_per_stock=200000):

    # max_day = min(
    #     df["day"].max()
    #     for df in data1.values()
    # )
    max_day = max(
    df["day"].max()
    for df in data1.values()
        )

    buy_list = get_buy_candidates(
        data1,
        first_day,
        owned=[]
    )

    portfolio, money, owned = build_initial_portfolio(
        data1,
        buy_list,
        first_day,
        capital=capital,
        max_positions=max_positions,
        allocation_per_stock=allocation_per_stock
    )

    history = []

    for day in range(first_day,
                     max_day + 1,
                     10):

        sell_list = get_sell_list(
            portfolio,
            data1,
            day
        )

        portfolio, money, owned = execute_sells(
            portfolio,
            sell_list,
            data1,
            day,
            money
        )

        if len(sell_list) > 0:

            buy_list = get_buy_candidates(
                data1,
                day,
                owned
            )

            portfolio, money, owned = execute_buys(
                data1,
                portfolio,
                buy_list,
                day,
                money,
                max_positions=max_positions,
                allocation_per_stock=allocation_per_stock
            )

        portfolio = mark_to_market(
            portfolio,
            data1,
            day
        )

        portfolio_value, equity = calculate_portfolio_value(
            portfolio,
            money
        )

        sample = get_row(
            next(iter(data1.values())),
            day
        )

        history.append({
            "day": day,
            "date": sample["date"],
            "cash": money,
            "portfolio": portfolio_value,
            "equity": equity,
            "positions": len(portfolio)
        })

    history = pd.DataFrame(history)

    return history


def performance_metrics(history,
                        initial_capital=1000000):

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

# data1 = prepare_rebalance_data(data)

# buy_list = get_buy_candidates(
#     data1,
#     first_day,
#     owned=[]
# )

# portfolio, money, owned = build_initial_portfolio(
#     data1,
#     buy_list,
#     first_day
# )

# for day in range(first_day + 10,
#                  max_day + 1,
#                  10):

#     # Find sells

#     sell_list = get_sell_list(
#         portfolio,
#         data1,
#         day
#     )

#     # Execute sells

#     portfolio, money, owned = execute_sells(
#         portfolio,
#         sell_list,
#         data1,
#         day,
#         money
#     )

#     # Only look for buys if something was sold
#     # (same logic as your original code)

#     if sell_list:

#         buy_list = get_buy_candidates(
#             data1,
#             day,
#             owned
#         )

#         portfolio, money, owned = execute_buys(
#             data1,
#             portfolio,
#             buy_list,
#             day,
#             money
#         )
#         value= sum([portfolio[i]['price']*portfolio[i]['qty'] for i in portfolio])
        
#         print(day,"---", value+money)


