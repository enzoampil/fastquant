#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Import standard library
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


class MACDStrategy(BaseStrategy):
    """
    Moving Average Convergence Divergence (MACD) strategy
    Simple implementation of backtrader MACD reference: https://www.backtrader.com/blog/posts/2016-07-30-macd-settings/macd-settings/

    Summary:
    Enter if the macd line crosses the signal line to the upside and a control Simple Moving Average has had a
    net negative direction in the last x periods (current SMA value below the value x periods ago).
    In the opposite situation, given a market position exists, a sell position is made.

    Parameters
    ----------
    fast_period : int
        The period used for the fast exponential moving average line (should be smaller than `slow_upper`)
    slow_period : int
        The period used for the slow exponential moving average line (should be larger than `fast_upper`)
    signal_period : int
        The period used for the signal line for MACD
    sma_period : int
        Period for the moving average (default: 30)
    dir_period: int
        Period for SMA direction calculation (default: 10)
    """

    params = (
        ("fast_period", 12),  # period for the fast moving average
        ("slow_period", 26),
        ("signal_period", 9),
        ("sma_period", 30),
        ("dir_period", 10),
    )

    def __init__(self):
        # Initialize global variables
        super().__init__()
        # Strategy level variables
        self.fast_period = self.params.fast_period
        self.slow_period = self.params.slow_period
        self.signal_period = self.params.signal_period
        self.sma_period = self.params.sma_period
        self.dir_period = self.params.dir_period

        if self.strategy_logging:
            print("===Strategy level arguments===")
            print("fast_period :", self.fast_period)
            print("slow_period :", self.slow_period)
            print("signal_period :", self.signal_period)
            print("sma_period :", self.sma_period)
            print("dir_period :", self.dir_period)
        macd_ind = bt.ind.MACD(
            period_me1=self.fast_period,
            period_me2=self.slow_period,
            period_signal=self.signal_period,
        )
        self.macd = macd_ind.macd
        self.signal = macd_ind.signal
        self.crossover = bt.ind.CrossOver(
            self.macd, self.signal
        )  # crossover buy signal

        # Control market trend
        self.sma = bt.indicators.SMA(period=self.sma_period)
        self.smadir = self.sma - self.sma(-self.dir_period)

    def buy_signal(self):
        # Buy if the macd line cross the signal line to the upside
        # and a control Simple Moving Average  has had a net negative
        # direction in the last x periods

        return self.crossover > 0 and self.smadir < 0.0

    def sell_signal(self):
        return self.crossover < 0 and self.smadir > 0.0
