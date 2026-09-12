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
from utils import show_data

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

#TICKERS=[i for i in TICKERS if i.split('.')[0] not in [i.split('.')[0] for i in pf_tickers]]

TICKERS= list(set(TICKERS))

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

rec= pm.buy_rec()

inc_exp= pm.increase_exposure_candidates()
dec_exp= pm.decrease_exposure_candidates()

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


holdings = show_data(data,portfolio)
holdings['holdings']= [portfolio[i]['qty'] for i in holdings.Ticker]
holdings['value']= [portfolio[i]['value'] for i in holdings.Ticker]


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
            "flag_counter",
            "Angle"
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
        
        
# =============================================================================
# buy rec
# =============================================================================
st.subheader("Delnaaz's Recommendation")

if len(rec)>0:
    st.dataframe(
        rec,
        use_container_width=True,
        hide_index=True
    )
else:
    st.success("No Open slots to buy")

# =============================================================================
# Increae exposure rec
# =============================================================================
left, right = st.columns(2)

with left:

    st.subheader("Increase exposure candidates")

    if len(inc_exp)>0:
        
        inc_rec=show_data(data,inc_exp)
        

        
        
        st.dataframe(
            inc_rec,
            use_container_width=True,
            hide_index=True
        )

    else:
        st.success("Nothing good to increase exposure")

with right:

    st.subheader("Decrease exposure candidates")

    if len(dec_exp)>0:
        
        dec_exp=show_data(data,dec_exp)
        

        
        
        st.dataframe(
            dec_exp,
            use_container_width=True,
            hide_index=True
        )

    else:
        st.success("Nothing bad to decrease exposure")
        st.dataframe(
            pd.DataFrame(sell_rows),
            use_container_width=True,
            hide_index=True
        )

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
left, right = st.columns(2)

with left:

    
    
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
with right:
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



holdings = show_data(data,data)

st.subheader("Watchlist")

st.dataframe(
    holdings,
    use_container_width=True,
    hide_index=True
)
          