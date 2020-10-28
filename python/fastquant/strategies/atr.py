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

class ATRStrategy(BaseStrategy):
    """
    Defined by J. Welles Wilder, Jr. in 1978 in his book “New Concepts in Technical Trading Systems”.
    The idea is to take the close into account to calculate the range if it yields a larger range than the daily range (High - Low)

    Parameters
    ----------
    atr_period : int
        Period used as basis in computing ATR
    atr_factor : float
        Value used as a multiplier against the ATR.
    """

    params = (("atr_period", 14), ("atr_factor", 1.0))

    def __init__(self):

        # Initialize global variables
        super().__init__()
        # Strategy level variables
        self.atr_period = self.params.atr_period
        self.atr_factor = self.params.atr_factor
        print("===Strategy level arguments===")
        print("atr_period :", self.atr_period)
        print("atr_factor :", self.atr_factor)

        self.atr = bt.indicators.AverageTrueRange(period=self.atr_period)
        self.atr_factored = bt.indicators.AverageTrueRange(period=self.atr_period) * self.atr_factor

        self.dataclose = self.datas[0].close
        self.dataopen = self.datas[0].open
        self.lastdataclose = self.datas[1].close
        self.lastdataopen = self.datas[1].open

        self.atr_trailing_stop = 0

        if self.dataclose > self.atr[1] & self.lastdataclose > self.atr[1] :
            self.atr_trailing_stop = max(self.atr[1], self.dataclose - self.atr_factored)
        elif self.dataclose < self.atr[1] & self.lastdataclose < self.atr[1]:
            self.atr_trailing_stop = min(self.atr[1], self.dataclose + self.atr_factored)
        elif self.dataclose > self.atr[1]:
            self.atr_trailing_stop = self.dataclose - self.atr_factored
        else:
            self.atr_trailing_stop = self.dataclose + self.atr_factored

    def buy_signal(self):
        return self.dataclose > self.atr_trailing_stop[0]

    def sell_signal(self):
        return self.dataopen < self.atr_trailing_stop[0]