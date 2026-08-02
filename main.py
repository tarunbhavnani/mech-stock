# -*- coding: utf-8 -*-
"""
Created on Sat Aug  1 19:58:06 2026

@author: tarun
import os
os.chdir(r"C:\Users\tarun\Desktop\mech-buy")
"""

# -*- coding: utf-8 -*-

from config import *

from backtest import (
    download_data,
    prepare_indicators,
    prepare_rebalance_data,
    run_backtest
)

from plots import (
    plot_equity_curve,
    plot_drawdown
)


def main():

    ##################################################
    # Download
    ##################################################

    data = download_data(
        TICKERS,
        START_DATE,
        AUTO_ADJUST
    )

    ##################################################
    # Indicators
    ##################################################

    data = prepare_indicators(data)

    ##################################################
    # Strategy Data
    ##################################################

    data = prepare_rebalance_data(
        data,
        STOP_LOSS_PCT
    )

    ##################################################
    # Backtest
    ##################################################

    history, stats,portfolio = run_backtest(
        data=data,
        first_trading_day=FIRST_TRADING_DAY,
        initial_capital=INITIAL_CAPITAL,
        max_positions=MAX_POSITIONS,
        allocation_per_stock=ALLOCATION_PER_STOCK,
        dist_low=DIST_LOW,
        dist_high=DIST_HIGH
    )

    ##################################################
    # Results
    ##################################################

    #print(stats)
    print(portfolio)

    ##################################################
    # Plots
    ##################################################

    plot_equity_curve(history)

    plot_drawdown(history)


if __name__ == "__main__":

    main()
