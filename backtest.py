# -*- coding: utf-8 -*-
"""
Created on Sat Aug  1 19:54:56 2026

@author: tarun
"""
import pandas as pd
import yfinance as yf

def download_data(tickers,
                  start_date,
                  auto_adjust=True):
    """
    Download OHLCV data from Yahoo Finance.

    Parameters
    ----------
    tickers : list

    start_date : str

    auto_adjust : bool

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
                continue

            # Yahoo sometimes returns MultiIndex columns

            if hasattr(df.columns, "levels"):

                df.columns = df.columns.get_level_values(0)

            df = df[
                [
                    "Open",
                    "High",
                    "Low",
                    "Close",
                    "Volume"
                ]
            ].copy()

            df["date"] = pd.to_datetime(df.index)

            df["Ticker"] = ticker

            df.reset_index(drop=True,
                           inplace=True)

            df.sort_values(
                "date",
                inplace=True
            )

            data[ticker] = df

        except Exception as e:

            print(f"{ticker} : {e}")

    return data

def prepare_indicators(data):
    """
    Calculate indicators.

    Adds

        SMA25
        SMA100
        SMA200
        VOL25

        Dist25
        Dist100
        Dist200

    Returns
    -------
    dict
    """

    for ticker in data:

        df = data[ticker]

        df["SMA25"] = (
            df["Close"]
            .rolling(25)
            .mean()
        )

        df["SMA100"] = (
            df["Close"]
            .rolling(100)
            .mean()
        )

        df["SMA200"] = (
            df["Close"]
            .rolling(200)
            .mean()
        )

        df["VOL25"] = (
            df["Volume"]
            .rolling(25)
            .mean()
        )

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
                           stop_loss_pct):
    """
    Prepare data for the strategy.

    Adds

        flag
        limit_updated

    Returns
    -------
    dict
    """

    rebalance = {}

    for ticker in data:

        df = data[ticker].copy()

        # Buy signal

        df["flag"] = (
            df["Close"]
            >
            df["SMA25"]
        )

        # Initial stop

        df["limit"] = (
            df["Close"]
            *
            stop_loss_pct
        )

        # Trailing stop

        trail = []

        for i in range(len(df)):

            if i == 0:

                trail.append(
                    df["limit"].iloc[0]
                )

            else:

                trail.append(

                    max(

                        trail[-1],

                        df["limit"].iloc[i]

                    )

                )

        df["limit_updated"] = trail

        rebalance[ticker] = df

    return rebalance


def get_row(df,
            date):
    """
    Return row for a given date.

    Returns
    -------
    Series
    """

    row = df.loc[
        df["date"] == date
    ]

    if row.empty:

        return None

    return row.iloc[0]


def get_trading_dates(data,
                      first_trading_day):
    """
    Master calendar.

    Uses the first stock
    as the calendar.

    Returns
    -------
    list
    """

    first = next(iter(data))

    dates = (
        data[first]
        ["date"]
        .iloc[first_trading_day:]
        .tolist()
    )

    return dates


def get_buy_candidates(data,
                       date,
                       owned,
                       dist_low=2,
                       dist_high=5):
    """
    Find all stocks eligible for buying.
    """

    buy_list = {}

    for ticker in data:

        if ticker in owned:
            continue

        row = get_row(data[ticker], date)

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


def build_initial_portfolio(data,
                            buy_list,
                            first_date,
                            capital,
                            max_positions,
                            allocation_per_stock):
    """
    Build the initial portfolio.
    """

    portfolio = {}

    money = capital

    buy_list = buy_list[:max_positions]

    for ticker in buy_list:

        row = get_row(
            data[ticker],
            first_date
        )

        if row is None:
            continue

        price = row["Close"]

        qty = int(
            allocation_per_stock // price
        )

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
                  data,
                  date):
    """
    Find all stocks
    whose trailing stop has been hit.
    """

    sell = []

    for ticker in portfolio:

        row = get_row(
            data[ticker],
            date
        )

        if row is None:
            continue

        if row["Close"] < row["limit_updated"]:

            sell.append(ticker)

    return sell


def execute_sells(portfolio,
                  sell_list,
                  data,
                  date,
                  money):
    """
    Sell all positions.
    """

    for ticker in sell_list:

        row = get_row(
            data[ticker],
            date
        )

        if row is None:
            continue

        sell_price = row["Close"]

        qty = portfolio[ticker]["qty"]

        money += sell_price * qty

        portfolio.pop(ticker)

    owned = list(
        portfolio.keys()
    )

    return portfolio, money, owned


def execute_buys(data,
                 portfolio,
                 buy_list,
                 date,
                 money,
                 max_positions,
                 allocation_per_stock):
    """
    Buy new stocks.
    """

    owned = list(
        portfolio.keys()
    )

    available = (
        max_positions
        - len(owned)
    )

    if available <= 0:

        return (
            portfolio,
            money,
            owned
        )

    buy_list = buy_list[:available]

    for ticker in buy_list:

        row = get_row(
            data[ticker],
            date
        )

        if row is None:
            continue

        price = row["Close"]

        qty = int(
            allocation_per_stock
            // price
        )

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

    owned = list(
        portfolio.keys()
    )

    return (
        portfolio,
        money,
        owned
    )


def mark_to_market(portfolio,
                   data,
                   date):
    """
    Update all portfolio prices.
    """

    for ticker in portfolio:

        row = get_row(
            data[ticker],
            date
        )

        if row is None:
            continue

        portfolio[ticker]["price"] = row["Close"]

        portfolio[ticker]["value"] = (

            portfolio[ticker]["qty"]

            *

            row["Close"]

        )

    return portfolio


def calculate_portfolio_value(
        portfolio,
        cash):
    """
    Portfolio Value
    """

    portfolio_value = sum(

        p["value"]

        for p in portfolio.values()

    )

    total_equity = (

        portfolio_value

        +

        cash

    )

    return portfolio_value, total_equity


def performance_metrics(
        history,
        initial_capital):
    """
    Calculate performance metrics.
    """

    history = history.copy()

    history["Peak"] = (

        history["equity"]

        .cummax()

    )

    history["Drawdown"] = (

        history["equity"]

        -

        history["Peak"]

    ) / history["Peak"]

    max_drawdown = (

        history["Drawdown"]

        .min()

    )

    years = (

        history["date"].iloc[-1]

        -

        history["date"].iloc[0]

    ).days / 365.25

    ending_value = (

        history["equity"]

        .iloc[-1]

    )

    cagr = (

        (ending_value / initial_capital)

        **

        (1 / years)

    ) - 1

    print()

    print("=" * 60)

    print(f"Initial Capital : {initial_capital:,.0f}")

    print(f"Ending Equity   : {ending_value:,.0f}")

    print(f"CAGR            : {cagr:.2%}")

    print(f"Max Drawdown    : {max_drawdown:.2%}")

    print("=" * 60)

    return {

        "Ending Equity": ending_value,

        "CAGR": cagr,

        "Max Drawdown": max_drawdown

    }


def run_backtest(
        data,
        first_trading_day,
        initial_capital,
        max_positions,
        allocation_per_stock,
        dist_low,
        dist_high):
    """
    Complete Backtest
    """

    dates = get_trading_dates(
        data,
        first_trading_day
    )

    first_date = dates[0]

    buy_list = get_buy_candidates(
        data,
        first_date,
        [],
        dist_low,
        dist_high
    )

    portfolio, cash, owned = (

        build_initial_portfolio(

            data,

            buy_list,

            first_date,

            initial_capital,

            max_positions,

            allocation_per_stock

        )

    )

    history = []

    for date in dates:

        ################################################

        sell_list = get_sell_list(

            portfolio,

            data,

            date

        )

        ################################################

        portfolio, cash, owned = (

            execute_sells(

                portfolio,

                sell_list,

                data,

                date,

                cash

            )

        )

        ################################################

        if len(sell_list) > 0:

            buy_list = get_buy_candidates(

                data,

                date,

                owned,

                dist_low,

                dist_high

            )

            portfolio, cash, owned = (

                execute_buys(

                    data,

                    portfolio,

                    buy_list,

                    date,

                    cash,

                    max_positions,

                    allocation_per_stock

                )

            )

        ################################################

        portfolio = mark_to_market(

            portfolio,

            data,

            date

        )

        portfolio_value, equity = (

            calculate_portfolio_value(

                portfolio,

                cash

            )

        )

        history.append(

            {

                "date": date,

                "cash": cash,

                "portfolio": portfolio_value,

                "equity": equity,

                "positions": len(portfolio)

            }

        )

    history = pd.DataFrame(history)

    stats = performance_metrics(

        history,

        initial_capital

    )

    return history, stats,portfolio


