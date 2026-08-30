# -*- coding: utf-8 -*-
"""
Created on Fri Aug 28 17:26:47 2026

@author: tarun
"""

# -*- coding: utf-8 -*-
"""
Created on Thu Aug 27 16:13:37 2026

@author: tarun
"""
import pandas as pd
import yfinance as yf
import numpy as np
import copy
import os
from datetime import datetime



def download_data(
    tickers,
    start_date,end_date=None,
    force_download=False,
):
    # -------------------------------------------------------
    # Download ALL tickers together
    # -------------------------------------------------------

    print(f"Downloading {len(tickers)} stocks...")

    raw = yf.download(
        tickers=tickers,
        start=start_date,
        end=end_date,
        progress=True,
        auto_adjust=True,
        group_by="ticker",
        threads=True,
    )

    data = {}

    # -------------------------------------------------------
    # Process each ticker
    # -------------------------------------------------------

    for n, ticker in enumerate(tickers):

        print(f"\rProcessing {n + 1}/{len(tickers)}", end="", flush=True)

        try:

            # Multiple ticker download gives:
            # ticker -> OHLCV
            df = raw[ticker].copy()

            if df.empty:
                continue

            df = df[["Close", "High", "Low", "Open", "Volume"]]
            
            df=df[~df.Close.isnull()]

            df["date"] = df.index
            df.reset_index(drop=True, inplace=True)

            df["Ticker"] = ticker

            # ------------------------------------------------
            # Moving averages
            # ------------------------------------------------

            close = df["Close"]

            df["SMA25"] = close.rolling(25).mean()
            df["SMA100"] = close.rolling(100).mean()
            df["SMA200"] = close.rolling(200).mean()

            # ------------------------------------------------
            # Volume MA
            # ------------------------------------------------

            df["VOL25"] = df["Volume"].rolling(25).mean()

            # ------------------------------------------------
            # Distance
            # ------------------------------------------------

            df["Dist25"] = (close - df["SMA25"]) / df["SMA25"] * 100
            df["Dist100"] = (close - df["SMA100"]) / df["SMA100"] * 100
            df["Dist200"] = (close - df["SMA200"]) / df["SMA200"] * 100

            data[ticker] = df

        except Exception as e:
            print(f"\n{ticker}: {e}")

    

 
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


def get_cum_flag(temp, col):
    lst=[i for i in temp[col]]
    lst=[1 if i==True else -1 for i in lst]
    lst[0:25]=[0]*25#since 25 sma flag
    temp['cum1']=lst
    temp['cum']=0
    for i in range(len(temp)):
        temp['cum'].iloc[i]=sum(temp['cum1'].loc[max(0,i-24):i])
    temp.pop('cum1')
    return temp
    
    
    

def anti_flag_counter(df):
    counter=0
    anti_flag_counter=[]
    for i in df['flag']:
        if i:
            counter=0
            anti_flag_counter.append(counter)
        else:
            counter+=1
            anti_flag_counter.append(counter)
    df['anti_flag_counter'] =anti_flag_counter
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
    fd={}
    for ticker in data:
        if len(data[ticker])>0:

            df = data[ticker]
            # buy signal
            df["flag"] = df["Close"] > df["SMA25"]
            df["Dist25_Change"] = df["Dist25"].diff()
            
            df=flag_counter(df)
            df=anti_flag_counter(df)
            df=add_angle(df)
            
    
            fd[ticker.split('.')[0]] = df
        

    return fd


def add_angle(df, window=3):
    df = df.copy()

    #pct_change = ((df["Close"] / df["Close"].shift(window)) ** (1 / window) - 1)
    pct_change = ((df["SMA25"] / df["SMA25"].shift(window)) ** (1 / window) - 1)

    df["Angle"] = np.degrees(np.arctan(pct_change * 100))
    
    # df["Angle_flag"] = df['Angle'].rolling(5).mean()
    # df["Angle_flag"]=[i>j for i,j in zip(df["Angle"],df["Angle_flag"] )]
    df["Angle_flag"] = df['Close'].rolling(5).mean()
    df["Angle_flag"]=[i>j for i,j in zip(df["Close"],df["Angle_flag"] )]
    

    return df

def download_nifty(
                  start_date,end_date=None,
                  auto_adjust=True):
   

   
        try:

            df = yf.download(
                "^NSEI",
                start=start_date, end= end_date,
                auto_adjust=True
            )

          

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

            df["Ticker"] = 'nifty'
            close = df["Close"]
            df["SMA25"] = close.rolling(25).mean()
            df["SMA100"] = close.rolling(100).mean()
            df["SMA200"] = close.rolling(200).mean()

            # ------------------------------------------------
            # Volume MA
            # ------------------------------------------------

            df["VOL25"] = df["Volume"].rolling(25).mean()

            # ------------------------------------------------
            # Distance
            # ------------------------------------------------

            df["Dist25"] = (close - df["SMA25"]) / df["SMA25"] * 100
            df["Dist100"] = (close - df["SMA100"]) / df["SMA100"] * 100
            df["Dist200"] = (close - df["SMA200"]) / df["SMA200"] * 100

            df.sort_values("date", inplace=True)

      
        except Exception as e:

            print(f"{e}")

        return df

def get_final_data(all_data,nifty, TICKERS):
    data= {i:j for i,j in all_data.items() if i in TICKERS}    
    
    
    data = prepare_indicators(data)
    
    data=get_day(data)
    
    nifty = prepare_indicators({'nifty':nifty})
    
    nifty=get_day(nifty)
    
    
    return data, nifty['nifty']




def sanitize_tickers(ls1,ls2):
    ls2=[i for i in ls2 if i.split('.')[0] not in [j.split('.')[0] for j in ls1]]
    ls3=ls1+ls2
    return ls3
    

    # ls3=[i for i in my_stocks if i.split('.')[0] not in [j.split('.')[0] for j in fno]]

    # nf=ls2+ls3+fno

    # nf_check=[i.split('.')[0] for i in nf]
    # len(nf_check)==len(list(set(nf_check)))

    #print(nf)