# -*- coding: utf-8 -*-
"""
Created on Sat Sep  5 15:44:05 2026

@author: tarun
"""
import pandas as pd

def show_data(data, data_hourly,concerned_data):
    rows=[]
    for ticker in data:
        if ticker in concerned_data:

            d = data[ticker].iloc[-1]
            d1=data_hourly[ticker].iloc[-1]
        
            
        
            rows.append({
        
                "Ticker": ticker,
                "Price":  d["Close"],
                "Change": d["Dist25_Change"],
                "Day High":   d["High"],
                "Day Low":  d["Low"],
                "Swing":  round(100*(d["High"]-d["Low"])/d["Low"],2),
                "Volume":d["Volume"],
                "Vol_sd":d["sd"],
                "SMA25": d["SMA25"],
                "flag_SMA25Day": d["flag_counter"]-d["anti_flag_counter"],
                "SMA100Hr": d1["SMA100"],
                "flag_SMA100Hr": d1["flag_counter"]-d1["anti_flag_counter"],
                "Angle":             d["Angle"],
                "Angle_flag":        d["Angle_flag"]
               
            })

    return pd.DataFrame(rows)



