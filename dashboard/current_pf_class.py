# -*- coding: utf-8 -*-
"""
Created on Mon Aug  3 21:19:27 2026

@author: tarun
"""

import numpy as np


class PortfolioManager:

    def __init__(self, data, current_list, stoploss):
        self.data = data
        self.current_list = current_list
        self.stoploss = stoploss
        self.portfolio = {}

    # =========================================================================
    # Build current portfolio
    # =========================================================================
    def current_portfolio(self):
        """
        Build current portfolio in required format on today's date.
        """

        self.portfolio = {}

        for ticker in self.current_list:

            row = self.data[ticker].iloc[-1]

            if row is None:
                continue

            price = np.floor(row["Close"])

            highest_price = price

            sl = np.ceil(highest_price * (100 - self.stoploss) / 100)

            qty = int(self.current_list[ticker])

            cost = qty * price

            self.portfolio[ticker] = {
                "price": price,
                "highest_price": highest_price,
                "qty": qty,
                "value": cost,
                "sl": sl,
            }

        return self.portfolio

    # =========================================================================
    # Update current portfolio
    # =========================================================================
    def update_current_portfolio(self):
        """
        Update current portfolio with latest prices.
        """

        for ticker in self.portfolio:

            row = self.data[ticker].iloc[-1]

            if row is None:
                continue

            price = np.floor(row["Close"])

            self.portfolio[ticker]["price"] = price

            if price > self.portfolio[ticker]["highest_price"]:
                self.portfolio[ticker]["highest_price"] = price
                self.portfolio[ticker]["sl"] = np.ceil(
                    price * (100 - self.stoploss) / 100
                )

        return self.portfolio

    # =========================================================================
    # Buy candidates
    # =========================================================================
    def get_buy_candidates(self, dist_low, dist_high):
        """
        Find stocks eligible for buying.
        """

        buy_list = {}

        for ticker in self.data:

            row = self.data[ticker].iloc[-1]

            if row is None:
                continue

            if row["flag"]:

                if dist_low < row["Dist25"] < dist_high:
                    if (
                        row["flag_counter"] > 5
                        and row["Dist25_Change"] > 0
                    ):
                        buy_list[ticker] = row["Dist25"]

        buy_list = dict(
            sorted(
                buy_list.items(),
                key=lambda x: x[1]
            )
        )

        return list(buy_list.keys())

    # =========================================================================
    # Sell stock
    # =========================================================================
    def sell_stock(self, ticker):

        sold = self.portfolio.pop(ticker)

        return sold

    # =========================================================================
    # Buy stock
    # =========================================================================
    def buy_stock(self, ticker, price, qty):

        bought = {
            "price": price,
            "highest_price": price,
            "qty": qty,
            "value": price * qty,
            "sl": np.ceil(price * (100 - self.stoploss) / 100),
        }

        self.portfolio[ticker] = bought

        return self.portfolio