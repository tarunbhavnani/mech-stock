# -*- coding: utf-8 -*-
"""
Created on Tue Aug  4 20:04:08 2026

@author: tarun
"""

# dashboard.py

import json
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from charts import (
    stock_chart,
    allocation_chart,
    holdings_chart,
    stoploss_chart,
    drawdown_chart,
    volume_chart,
    distance_chart
)
from config import *
from get_data import download_data, prepare_indicators
from portfolio_manager import PortfolioManager

st.set_page_config(
    page_title="Mechanical Buy Dashboard",
    layout="wide"
)

st.title("📈 Mechanical Buy Dashboard")


#########################################################
# LOAD PORTFOLIO and TICKERS
#########################################################

with open("data/portfolio.json", "r") as f:
    portfolio = json.load(f)

pf_tickers= [i for i in portfolio]

TICKERS=[i for i in TICKERS if i.split('.')[0] not in [i.split('.')[0] for i in pf_tickers]]

TICKERS= list(set(TICKERS+pf_tickers))

#########################################################
# LOAD DATA
#########################################################

@st.cache_data(ttl=3000)
def load_market():

    tickers = list(set(TICKERS))

    data = download_data(
        tickers,
        start_date
    )

    data = prepare_indicators(data)

    return data


data = load_market()

# =============================================================================
# initialize pm
# =============================================================================
pm = PortfolioManager(
    data,
    portfolio,
    stoploss,
    pf_start_date
)

portfolio = pm.update_current_portfolio()

buy_list = pm.get_buy_candidates(
    dist_low,
    dist_high
)

sell_list = pm.get_sell_list()

#########################################################
# SUMMARY
#########################################################

total_value = sum(
    portfolio[t]["value"]
    for t in portfolio
)

n_holdings = len(portfolio)

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Portfolio Value",
    f"₹{total_value:,.0f}"
)

c2.metric(
    "Holdings",
    n_holdings
)

c3.metric(
    "Buy Candidates",
    len(buy_list)
)

c4.metric(
    "Sell Candidates",
    len(sell_list)
)

st.divider()


#########################################################
# REFRESH
#########################################################

if st.button("🔄 Refresh Data"):

    st.cache_data.clear()

    st.rerun()

#########################################################
# HOLDINGS TABLE
#########################################################

rows = []

for ticker in portfolio:

    p = portfolio[ticker]

    pnl = (
        (p["price"] - p["highest_price"])
        / p["highest_price"]
        * 100
    )

    dist_sl = (
        (p["price"] - p["sl"])
        / p["sl"]
        * 100
    )

    rows.append({

        "Ticker": ticker,

        "Qty": p["qty"],

        "Current": p["price"],

        "Highest": p["highest_price"],

        #"SL": p["sl"],

        "Value": p["value"],

        "Drawdown %": round(pnl,2),

        #"Dist to SL %": 100*(1-(p['sl']/p["price"]))
        '25SMA':data[ticker]['SMA25'].iloc[-1],
        "Flag": data[ticker]['flag_counter'].iloc[-1],
        "Anti Flag": data[ticker]['anti_flag_counter'].iloc[-1]
        

    })

holdings = pd.DataFrame(rows)

st.subheader("Current Portfolio")

st.dataframe(
    holdings,
    use_container_width=True,
    hide_index=True
)

#########################################################
# BUY / SELL
#########################################################

left, right = st.columns(2)

with left:

    st.subheader("Buy Candidates")

    if len(buy_list):

        df = pd.DataFrame([
            data[t].iloc[-1]
            for t in buy_list
        ])

        df = df[[
            "Ticker",
            "Close",
            "Dist25",
            "Dist25_Change",
            "flag_counter"
        ]]

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.success("No Buy Candidates")

with right:

    st.subheader("Sell Candidates")

    if len(sell_list):

        sell_rows = []

        for t in sell_list:

            p = portfolio[t]

            sell_rows.append({

                "Ticker": t,

                "Current": p["price"],

                "SL": p["sl"]

            })

        st.dataframe(
            pd.DataFrame(sell_rows),
            use_container_width=True,
            hide_index=True
        )

    else:

        st.success("No Sell Signals")

#########################################################
# STOCK CHART
#########################################################

# st.plotly_chart(
#     stock_chart(df, portfolio, ticker),
#     use_container_width=True
# )

# col1, col2 = st.columns(2)

# with col1:
#     st.plotly_chart(
#         volume_chart(df),
#         use_container_width=True
#     )

# with col2:
#     st.plotly_chart(
#         distance_chart(df),
#         use_container_width=True
#     )

# st.plotly_chart(
#     allocation_chart(portfolio),
#     use_container_width=True
# )

# col1, col2 = st.columns(2)

# with col1:
#     st.plotly_chart(
#         holdings_chart(portfolio),
#         use_container_width=True
#     )

# with col2:
#     st.plotly_chart(
#         drawdown_chart(portfolio),
#         use_container_width=True
#     )

#########################################################
# PORTFOLIO ALLOCATION
#########################################################

# st.divider()

# st.subheader("Portfolio Allocation")

# alloc = pd.DataFrame([

#     {

#         "Ticker": t,

#         "Value": portfolio[t]["value"]

#     }

#     for t in portfolio

# ])

# pie = go.Figure(

#     data=[

#         go.Pie(

#             labels=alloc["Ticker"],

#             values=alloc["Value"]

#         )

#     ]

# )

# st.plotly_chart(
#     pie,
#     use_container_width=True
# )

#########################################################
# BUY STOCK
#########################################################

st.divider()

st.subheader("Buy Stock")

with st.form("buy"):

    bticker = st.selectbox(
        "Ticker",
        sorted(data.keys()),
        key="buyticker"
    )

    # bprice = st.number_input(
    #     "Price",
    #     min_value=0.0
    # )

    bqty = st.number_input(
        "Qty",
        min_value=1,
        step=1
    )

    submit = st.form_submit_button(
        "Buy"
    )

    if submit:

        pm.buy_stock(
            bticker,
            #bprice,
            bqty
        )

        pm.save_portfolio()

        st.success("Portfolio Updated")

#########################################################
# SELL STOCK
#########################################################

st.subheader("Sell Stock")


with st.form("sell"):

    bticker = st.selectbox(

        "Holding",

        list(portfolio.keys())

    )

    # bprice = st.number_input(
    #     "Price",
    #     min_value=0.0
    # )

    bqty = st.number_input(
        "Qty",
        min_value=1,
        step=1
    )

    submit = st.form_submit_button(
        "Sell"
    )

    if submit:

        pm.sell_stock(
            bticker,
            
            bqty
        )

        pm.save_portfolio()

        st.success("Stock Sold")


#########################################################
# ALL TABLE
#########################################################

rows = []

for ticker in data:

    d = data[ticker].iloc[-1]

    

    rows.append({

        "Ticker": ticker,
        "Open":  d["Open"],
        "Close": d["Close"],
        "Low":   d["Low"],
        "High":  d["High"],
        "Volume":d["Volume"],
        "SMA25": d["SMA25"],
        "flag_counter":      d["flag_counter"],
        "anti_flag_counter": d["anti_flag_counter"],
        "Angle":             d["Angle"],
        "Angle_flag":             d["Angle_flag"]
       
    })

holdings = pd.DataFrame(rows)

st.subheader("Watchlist")

st.dataframe(
    holdings,
    use_container_width=True,
    hide_index=True
)
          