# -*- coding: utf-8 -*-
"""
Created on Tue Aug 11 17:20:17 2026

@author: tarun
"""


import pandas as pd
import yfinance as yf
import numpy as np
#from config import *
import copy


def check_nan_last_data_row(data):
    if sum([pd.isna(data[i]['Close'].iloc[-1]) for i in data])>0:
        for ticker in data:
            data[ticker] = data[ticker].iloc[:-1]
    else:
        pass
    return data


def download_data(tickers,
                  start_date,end_date=None,
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

    for n,ticker in enumerate(tickers):

        #print(f"Downloading {ticker}")
        print(n, end=', ', flush=True)

        try:

            df = yf.download(
                ticker,
                start=start_date,
                end=end_date,
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

            df.sort_values("date", inplace=True)

      
        except Exception as e:

            print(f"{e}")

        return df




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

    for ticker in data:

        df = data[ticker]

        # Moving averages

        df["SMA25"] = df["Close"].rolling(25).mean()#.ewm(span=25, adjust=False).mean()
        #df["SMA25"] = df["Close"].ewm(span=25, adjust=False).mean()
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
        df=anti_flag_counter(df)
        df=add_angle(df)
        

        data[ticker] = df
        
        data=check_nan_last_data_row(data)


    return data


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



# def add_angle(df, window=5):
#     df = df.copy()

#     pct_change = (
#         (df["Close"] / df["Close"].shift(window)) ** (1 / window) - 1
#     )

#     df["Angle"] = np.degrees(np.arctan(pct_change * 100))

#     return df


def get_final_data(all_data,nifty, TICKERS):
    data= {i:j for i,j in all_data.items() if i in TICKERS}    
    
    
    data = prepare_indicators(data)
    
    data=get_day(data)
    
    nifty = prepare_indicators({'nifty':nifty})
    
    nifty=get_day(nifty)
    
    
    return data, nifty['nifty']


