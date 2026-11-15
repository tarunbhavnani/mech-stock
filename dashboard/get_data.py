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
from datetime import datetime, timedelta




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


def prepare_indicators(data, flag='SMA25'):
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
            df["flag"] = df["Close"] > df[flag]
            df["Change"] = (df["Close"] - df["Close"].shift(1)) / df["Close"].shift(1) * 100
            
            df=flag_counter(df)
            df=anti_flag_counter(df)
            df=add_angle(df)
            
            df=vol_analysis(df)
            
            df= get_supp_res_last(df)
            
            df['sd_flag']=sd_flag(df)
            
    
            fd[ticker.split('.')[0]] = df
        

    return fd


# def add_angle(df, window=3):
#     df = df.copy()

#     #pct_change = ((df["Close"] / df["Close"].shift(window)) ** (1 / window) - 1)
#     pct_change = ((df["SMA25"] / df["SMA25"].shift(window)) ** (1 / window) - 1)

#     df["Angle"] = np.degrees(np.arctan(pct_change * 100))
    
#     # df["Angle_flag"] = df['Angle'].rolling(5).mean()
#     # df["Angle_flag"]=[i>j for i,j in zip(df["Angle"],df["Angle_flag"] )]
#     df["Angle_flag"] = df['Close'].rolling(5).mean()
#     df["Angle_flag"]=[i>j for i,j in zip(df["Close"],df["Angle_flag"] )]
    

#     return df


def add_angle(df, lookback=10):

    df = df.copy()

    # SMA25 angle using two points
    slope = (
        df["SMA25"] - df["SMA25"].shift(lookback)
    ) / lookback

    # Normalize against current SMA25
    pct_slope = slope / df["SMA25"] * 100

    df["Angle"] = np.degrees(np.arctan(pct_slope))
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


def download_data_hourly(
    tickers,
    start_date=None,
    end_date=None,
    force_download=False,
):
    # -------------------------------------------------------
    # Last 60 days, 1-hour timeframe
    # -------------------------------------------------------

    if start_date is None:
        start_date = datetime.now() - timedelta(days=60)

    if end_date is None:
        end_date = datetime.now()

    print(f"Downloading {len(tickers)} stocks...")
    print(f"Period: {start_date.date()} to {end_date.date()}")
    print("Interval: 1 hour")

    # -------------------------------------------------------
    # Download ALL tickers together
    # -------------------------------------------------------

    raw = yf.download(
        tickers=tickers,
        start=start_date,
        end=end_date,
        interval="1h",
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

        print(
            f"\rProcessing {n + 1}/{len(tickers)}",
            end="",
            flush=True
        )

        try:

            # Multiple ticker download gives:
            # ticker -> OHLCV
            df = raw[ticker].copy()

            if df.empty:
                continue

            df = df[
                ["Close", "High", "Low", "Open", "Volume"]
            ]

            df = df[~df["Close"].isnull()]

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
            # Distance from moving averages
            # ------------------------------------------------

            df["Dist25"] = (
                (close - df["SMA25"])
                / df["SMA25"]
                * 100
            )

            df["Dist100"] = (
                (close - df["SMA100"])
                / df["SMA100"]
                * 100
            )

            df["Dist200"] = (
                (close - df["SMA200"])
                / df["SMA200"]
                * 100
            )

            data[ticker] = df

        except Exception as e:
            print(f"\n{ticker}: {e}")

    print("\nDone.")

    return data

def vol_analysis(data, window=150):
    df = data.tail(window).copy()

    # Calculate IQR
    q1 = df['Volume'].quantile(0.25)
    q3 = df['Volume'].quantile(0.75)
    iqr = q3 - q1

    # Remove outliers
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr

    volume_clean = df.loc[
        df['Volume'].between(lower, upper),
        'Volume'
    ]

    # Mean and standard deviation without outliers
    mean_volume = volume_clean.mean()
    std_volume = volume_clean.std()

    # Calculate z-score for ALL observations,
    # including the original outliers
    df['sd'] = ((df['Volume'] - mean_volume) / std_volume).round(2)

    # Add/update column in original dataframe
    data['sd'] = 0.0
    data.loc[df.index, 'sd'] = df['sd']

    return data

# def get_supp_res(df):

#     resis=[]
#     supp=[]
#     for i in range(len(df)):
#         try:
#             temp= df.iloc[0:i]
#             price= temp['Close'].iloc[-1]
#             #temp= data[ticker]
#             bin_size= round(price*.02)
            
#             temp['Mid']=round((temp['Open']+temp['Close'])/2 )
#             temp=temp[['Mid', 'Volume']]
            
#             temp['Mid_bin'] = (temp['Mid'] // bin_size) * bin_size
        
#             temp = (
#                 temp.groupby('Mid_bin', as_index=False)['Volume']
#                   .sum()
#                   .sort_values('Mid_bin', ascending=False)
#             )
#             temp.columns=['Mid', 'Volume']
#             temp=temp.groupby('Mid')['Volume'].sum().reset_index().sort_values('Volume', ascending=False)
#             temp=temp.iloc[:10]
#             try:
#                 resistance=min(temp[temp.Mid>price]['Mid'])
#             except:
#                 resistance="NIR"
#             resis.append(resistance)
            
#             try:
#                 support=max(temp[temp.Mid<price]['Mid'])
#             except:
#                 support="NIS"
#             supp.append(support)
#         except:
#             resis.append("NIR")
#             supp.append("NIS")
            
#     df['support']=supp
#     df['resistance']=resis
    
#     return df

# def get_supp_res(df):

#     df = df.copy()

#     close = df['Close'].to_numpy()
#     mid = ((df['Open'].to_numpy() + close) / 2).round()
#     volume = df['Volume'].to_numpy()

#     n = len(df)

#     support = np.full(n, np.nan)
#     resistance = np.full(n, np.nan)

#     last_bin_size = None
#     vp = None

#     for i in range(1, n):

#         price = close[i - 1]
#         bin_size = max(round(price * 0.02), 1)

#         # Recalculate only when bin size changes
#         if bin_size != last_bin_size:

#             bins = (mid[:i] // bin_size) * bin_size

#             vp = (
#                 pd.Series(volume[:i])
#                 .groupby(bins)
#                 .sum()
#             )

#             last_bin_size = bin_size

#         else:
#             # Add only the latest candle
#             current_bin = (mid[i - 1] // bin_size) * bin_size

#             if current_bin in vp.index:
#                 vp.loc[current_bin] += volume[i - 1]
#             else:
#                 vp.loc[current_bin] = volume[i - 1]

#         levels = vp.nlargest(10).index.to_numpy()

#         below = levels[levels < price]
#         above = levels[levels > price]

#         if len(below):
#             support[i] = below.max()

#         if len(above):
#             resistance[i] = above.min()

#     df['support'] = support
#     df['resistance'] = resistance
    

#     return df
def get_supp_res_last(df):

    df = df.copy()


    close = df['Close'].to_numpy()
    mid = ((df['Open'].to_numpy() + close) / 2).round()
    volume = df['Volume'].to_numpy()

    n = len(df)

    #support = np.full(n, np.nan)
    #resistance = np.full(n, np.nan)

    last_bin_size = None
    vp = None

    #for i in range(1, n):
    i=n-1

    price = close[i - 1]
    bin_size = max(round(price * 0.02), 1)

    # Recalculate only when bin size changes

    bins = (mid[:i] // bin_size) * bin_size

    vp = (
        pd.Series(volume[:i])
        .groupby(bins)
        .sum()
    )

    abc=[(i,j) for i,j in zip(vp, vp.index.to_numpy())]
    bl=[i for i in abc if i[1]<price]
    bl=sorted(bl, key=lambda x: x[0], reverse=True)[0:5]
    df.loc[:, 's1']=sorted(bl, key=lambda x: x[1], reverse=True)[0][1] if len(bl) > 0 else np.nan
    df.loc[:, 's2']=sorted(bl, key=lambda x: x[1], reverse=True)[1][1] if len(bl) > 1 else np.nan

    ab=[i for i in abc if i[1]>=price]
    ab=sorted(ab, key=lambda x: x[0], reverse=True)[0:5]
    df.loc[:, 'r1']=sorted(ab, key=lambda x: x[1], reverse=True)[-1][1] if len(ab) > 0 else np.nan
    df.loc[:, 'r2']=sorted(ab, key=lambda x: x[1], reverse=True)[-2][1] if len(ab) > 1 else np.nan
    

    return df

def sd_flag(df):
    temp= df.iloc[-25:]
    
    bull=len([(i,j) for i,j in zip(temp.Change, temp.sd) if i>2 and j>5 ])
    bear=len([(i,j) for i,j in zip(temp.Change, temp.sd) if i<-2 and j>5 ])
    move=len([(i,j) for i,j in zip(temp.Change, temp.sd) if -1<=i<=-2 and j>5 ])
    
    if bull>0 and bear==0:
        return "Bull-"+str(bull)

    elif bull==0 and bear>0:
        return "Bear-"+str(bear)
    
    elif bull>0 and bear>0:
        return "Bull&Bear -" +str(bull)+"-"+str(bear)

    elif move>0 and bull==0 and bear==0:
        return "Movement-"+str(move)
    
    else:
        return ""

def download_nifty_hourly(
    start_date=None,
    end_date=None,
    auto_adjust=True
):

    # -------------------------------------------------------
    # Last 60 days by default
    # -------------------------------------------------------

    if start_date is None:
        start_date = datetime.now() - timedelta(days=60)

    if end_date is None:
        end_date = datetime.now()

    try:

        print(
            f"Downloading NIFTY 1-hour data: "
            f"{start_date.date()} to {end_date.date()}"
        )

        df = yf.download(
            "^NSEI",
            start=start_date,
            end=end_date,
            interval="1h",
            auto_adjust=auto_adjust,
            progress=True
        )

        if df.empty:
            print("No NIFTY data downloaded.")
            return pd.DataFrame()

        # ---------------------------------------------------
        # Flatten MultiIndex if required
        # ---------------------------------------------------

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # ---------------------------------------------------
        # Select required columns
        # ---------------------------------------------------

        df = df[
            [
                "Close",
                "High",
                "Low",
                "Open",
                "Volume"
            ]
        ].copy()

        # Remove rows with missing Close
        df = df[~df["Close"].isnull()]

        # ---------------------------------------------------
        # Date
        # ---------------------------------------------------

        df["date"] = df.index
        df.reset_index(drop=True, inplace=True)

        df["Ticker"] = "nifty"

        # ---------------------------------------------------
        # Moving averages
        # ---------------------------------------------------

        close = df["Close"]

        df["SMA25"] = close.rolling(25).mean()
        df["SMA100"] = close.rolling(100).mean()
        df["SMA200"] = close.rolling(200).mean()

        # ---------------------------------------------------
        # Volume MA
        # ---------------------------------------------------

        df["VOL25"] = df["Volume"].rolling(25).mean()

        # ---------------------------------------------------
        # Distance from moving averages
        # ---------------------------------------------------

        df["Dist25"] = (
            (close - df["SMA25"])
            / df["SMA25"]
            * 100
        )

        df["Dist100"] = (
            (close - df["SMA100"])
            / df["SMA100"]
            * 100
        )

        df["Dist200"] = (
            (close - df["SMA200"])
            / df["SMA200"]
            * 100
        )

        # ---------------------------------------------------
        # Sort
        # ---------------------------------------------------

        df.sort_values("date", inplace=True)
        df.reset_index(drop=True, inplace=True)

        print(f"Downloaded {len(df)} hourly candles.")

        return df

    except Exception as e:

        print(f"NIFTY download error: {e}")

        return pd.DataFrame()
