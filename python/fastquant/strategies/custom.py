#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Import standard library
# Strategy module for custom indicators input to backtest
from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

# Import modules
import backtrader as bt

# Import from package
from fastquant.strategies.base import BaseStrategy


class CustomStrategy(CustomStrategy):
    """
    Simple moving average crossover strategy

    Parameters
    ----------
    upper : float
        The upper value of the custom indicator above which, the asset is sold
    lower : float
        The lower value of the custom indicator above which, the asset is sold

    """

    params = (
        ("upper", 80),  # period for the fast moving average
        ("lower", 20),
    )

    def __init__(self):
        # Initialize global variables
        super().__init__()
        # Strategy level variables
        self.fast_period = self.params.fast_period
        self.slow_period = self.params.slow_period

        print("===Strategy level arguments===")
        print("fast_period :", self.fast_period)
        print("slow_period :", self.slow_period)
        sma_fast = bt.ind.SMA(period=self.fast_period)  # fast moving average
        sma_slow = bt.ind.SMA(period=self.slow_period)  # slow moving average
        self.crossover = bt.ind.CrossOver(
            sma_fast, sma_slow
        )  # crossover signal

    def buy_signal(self):
        return self.crossover > 0

    def sell_signal(self):
        return self.crossover < 0