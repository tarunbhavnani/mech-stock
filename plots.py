# -*- coding: utf-8 -*-
"""
Created on Sat Aug  1 19:57:56 2026

@author: tarun
"""

# -*- coding: utf-8 -*-
"""
Plots
"""

import matplotlib.pyplot as plt


def plot_equity_curve(history):
    """
    Plot Portfolio Equity Curve
    """

    plt.figure(figsize=(14,6))

    plt.plot(
        history["date"],
        history["equity"],
        linewidth=2,
        label="Portfolio"
    )

    plt.title("Portfolio Equity Curve")

    plt.xlabel("Date")

    plt.ylabel("Portfolio Value")

    plt.grid(True)

    plt.legend()

    plt.tight_layout()

    plt.show()


def plot_drawdown(history):
    """
    Plot Drawdown
    """

    history = history.copy()

    history["Peak"] = history["equity"].cummax()

    history["Drawdown"] = (
        history["equity"] -
        history["Peak"]
    ) / history["Peak"]

    plt.figure(figsize=(14,4))

    plt.fill_between(
        history["date"],
        history["Drawdown"] * 100,
        0
    )

    plt.title("Drawdown")

    plt.ylabel("%")

    plt.grid(True)

    plt.tight_layout()

    plt.show()