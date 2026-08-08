# -*- coding: utf-8 -*-
"""
Created on Tue Aug  4 20:05:11 2026

@author: tarun
"""

# charts.py

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd


# ==========================================================
# Candlestick Chart
# ==========================================================

def stock_chart(df, portfolio=None, ticker=None):
    """
    Interactive candlestick chart with moving averages.

    Parameters
    ----------
    df : DataFrame
    portfolio : dict
    ticker : str

    Returns
    -------
    plotly Figure
    """

    fig = go.Figure()

    # Candles
    fig.add_trace(
        go.Candlestick(
            x=df["date"],
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="Price"
        )
    )

    # Moving averages
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["SMA25"],
            mode="lines",
            name="SMA25",
            line=dict(width=2)
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["SMA100"],
            mode="lines",
            name="SMA100",
            line=dict(width=2)
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["SMA200"],
            mode="lines",
            name="SMA200",
            line=dict(width=2)
        )
    )

    # Portfolio levels
    if portfolio is not None and ticker in portfolio:

        p = portfolio[ticker]

        fig.add_hline(
            y=p["highest_price"],
            line_dash="dot",
            annotation_text="Highest Price"
        )

        fig.add_hline(
            y=p["sl"],
            line_dash="dash",
            annotation_text="Stop Loss"
        )

        buy_price = p.get("buy_price", p.get("price"))

        fig.add_hline(
            y=buy_price,
            line_dash="solid",
            annotation_text="Buy Price"
        )

    fig.update_layout(
        template="plotly_dark",
        height=650,
        xaxis_rangeslider_visible=False,
        legend_orientation="h",
        margin=dict(
            l=20,
            r=20,
            t=40,
            b=20
        )
    )

    return fig


# ==========================================================
# Portfolio Allocation
# ==========================================================

def allocation_chart(portfolio):

    df = pd.DataFrame([
        {
            "Ticker": t,
            "Value": portfolio[t]["value"]
        }
        for t in portfolio
    ])

    fig = px.pie(
        df,
        names="Ticker",
        values="Value",
        hole=0.45
    )

    fig.update_layout(
        template="plotly_dark",
        height=500
    )

    return fig


# ==========================================================
# Top Holdings
# ==========================================================

def holdings_chart(portfolio):

    df = pd.DataFrame([
        {
            "Ticker": t,
            "Value": portfolio[t]["value"]
        }
        for t in portfolio
    ])

    df.sort_values(
        "Value",
        ascending=True,
        inplace=True
    )

    fig = px.bar(
        df,
        x="Value",
        y="Ticker",
        orientation="h",
        title="Portfolio Allocation"
    )

    fig.update_layout(
        template="plotly_dark",
        height=500
    )

    return fig


# ==========================================================
# Distance From Stoploss
# ==========================================================

def stoploss_chart(portfolio):

    rows = []

    for t in portfolio:

        p = portfolio[t]

        dist = (
            (p["price"] - p["sl"])
            / p["sl"]
            * 100
        )

        rows.append({
            "Ticker": t,
            "Distance": round(dist, 2)
        })

    df = pd.DataFrame(rows)

    df.sort_values(
        "Distance",
        inplace=True
    )

    fig = px.bar(
        df,
        x="Ticker",
        y="Distance",
        title="Distance From Stoploss (%)"
    )

    fig.update_layout(
        template="plotly_dark",
        height=450
    )

    return fig


# ==========================================================
# Portfolio Drawdown
# ==========================================================

def drawdown_chart(portfolio):

    rows = []

    for t in portfolio:

        p = portfolio[t]

        dd = (
            (p["price"] - p["highest_price"])
            / p["highest_price"]
            * 100
        )

        rows.append({

            "Ticker": t,
            "Drawdown": round(dd, 2)

        })

    df = pd.DataFrame(rows)

    df.sort_values(
        "Drawdown",
        inplace=True
    )

    fig = px.bar(
        df,
        x="Ticker",
        y="Drawdown",
        title="Drawdown From Highest Price (%)"
    )

    fig.update_layout(
        template="plotly_dark",
        height=450
    )

    return fig


# ==========================================================
# Volume Chart
# ==========================================================

def volume_chart(df):

    fig = go.Figure()

    fig.add_trace(

        go.Bar(

            x=df["date"],
            y=df["Volume"],
            name="Volume"

        )

    )

    fig.add_trace(

        go.Scatter(

            x=df["date"],
            y=df["VOL25"],
            mode="lines",
            name="VOL25"

        )

    )

    fig.update_layout(

        template="plotly_dark",
        height=300,
        legend_orientation="h"

    )

    return fig


# ==========================================================
# Dist25 Trend
# ==========================================================

def distance_chart(df):

    fig = go.Figure()

    fig.add_trace(

        go.Scatter(

            x=df["date"],
            y=df["Dist25"],
            mode="lines",
            name="Dist25"

        )

    )

    fig.add_hline(y=0)

    fig.update_layout(

        template="plotly_dark",
        height=300

    )

    return fig