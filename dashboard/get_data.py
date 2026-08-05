# -*- coding: utf-8 -*-
"""
Created on Mon Aug  3 21:23:05 2026

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


