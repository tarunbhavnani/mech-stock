# -*- coding: utf-8 -*-
"""
Created on Tue Aug  4 20:07:02 2026

@author: tarun
"""

# utils.py

import json
import pandas as pd
import streamlit as st

from config import *
from get_data import download_data, prepare_indicators
from portfolio_manager import PortfolioManager


# ==========================================================
# Load Market Data
# ==========================================================

@st.cache_data(ttl=300)
def load_market_data():
    """
    Download market data and calculate indicators.
    Cached for 5 minutes.
    """

    tickers = list(set(TICKERS))

    data = download_data(
        tickers=tickers,
        start_date=start_date
    )

    data = prepare_indicators(data)

    return data


# ==========================================================
# Load Portfolio
# ==========================================================

def load_portfolio():

    with open("data/portfolio.json", "r") as f:
        portfolio = json.load(f)

    return portfolio


# ==========================================================
# Save Portfolio
# ==========================================================

def save_portfolio(portfolio):

    with open("data/portfolio.json", "w") as f:

        json.dump(
            portfolio,
            f,
            indent=4
        )


# ==========================================================
# Create Portfolio Manager
# ==========================================================

def get_portfolio_manager():

    data = load_market_data()

    portfolio = load_portfolio()

    pm = PortfolioManager(
        data=data,
        portfolio=portfolio,
        stoploss=stoploss,
        pf_start_date=pf_start_date
    )

    portfolio = pm.update_current_portfolio()

    return pm, data, portfolio


# ==========================================================
# Portfolio Table
# ==========================================================

def portfolio_dataframe(portfolio):

    rows = []

    for ticker, p in portfolio.items():

        drawdown = (
            (p["price"] - p["highest_price"])
            / p["highest_price"]
            * 100
        )

        stoploss_distance = (
            (p["price"] - p["sl"])
            / p["sl"]
            * 100
        )

        rows.append({

            "Ticker": ticker,

            "Qty": p["qty"],

            "Current": round(p["price"], 2),

            "Highest": round(p["highest_price"], 2),

            "Stoploss": round(p["sl"], 2),

            "Value": round(p["value"], 2),

            "Drawdown %": round(drawdown, 2),

            "Distance to SL %": round(stoploss_distance, 2)

        })

    df = pd.DataFrame(rows)

    if not df.empty:

        df.sort_values(
            by="Value",
            ascending=False,
            inplace=True
        )

    return df


# ==========================================================
# Buy Candidates Table
# ==========================================================

def buy_dataframe(data, buy_list):

    if len(buy_list) == 0:

        return pd.DataFrame()

    rows = []

    for ticker in buy_list:

        row = data[ticker].iloc[-1]

        rows.append({

            "Ticker": ticker,

            "Close": round(row["Close"], 2),

            "Dist25": round(row["Dist25"], 2),

            "Dist25 Change": round(row["Dist25_Change"], 2),

            "Flag Counter": int(row["flag_counter"])

        })

    return pd.DataFrame(rows)


# ==========================================================
# Sell Candidates Table
# ==========================================================

def sell_dataframe(portfolio, sell_list):

    rows = []

    for ticker in sell_list:

        p = portfolio[ticker]

        rows.append({

            "Ticker": ticker,

            "Current": round(p["price"], 2),

            "Stoploss": round(p["sl"], 2),

            "Distance %": round(
                (p["price"] - p["sl"])
                / p["sl"]
                * 100,
                2
            )

        })

    return pd.DataFrame(rows)


# ==========================================================
# Portfolio Summary
# ==========================================================

def portfolio_summary(portfolio):

    total_value = sum(

        p["value"]

        for p in portfolio.values()

    )

    holdings = len(portfolio)

    avg_drawdown = 0

    if holdings:

        avg_drawdown = sum(

            (p["price"] - p["highest_price"])
            / p["highest_price"]
            * 100

            for p in portfolio.values()

        ) / holdings

    return {

        "portfolio_value": total_value,

        "holdings": holdings,

        "average_drawdown": round(avg_drawdown, 2)

    }


# ==========================================================
# Stock Metrics
# ==========================================================

def stock_metrics(df):

    row = df.iloc[-1]

    return {

        "Close": round(row["Close"], 2),

        "High": round(row["High"], 2),

        "Low": round(row["Low"], 2),

        "Volume": int(row["Volume"]),

        "Dist25": round(row["Dist25"], 2),

        "Dist100": round(row["Dist100"], 2),

        "Dist200": round(row["Dist200"], 2),

        "Flag": bool(row["flag"]),

        "Flag Counter": int(row["flag_counter"])

    }


# ==========================================================
# Refresh
# ==========================================================

def refresh():

    st.cache_data.clear()

    st.rerun()