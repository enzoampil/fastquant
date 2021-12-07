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


class RSIStrategy(BaseStrategy):
    """
    Relative Strength Index (RSI) trading strategy

    Parameters
    ----------
    rsi_period : int
        Period used as basis in computing RSI
    rsi_upper : int
        The RSI upper limit, above which the assess is considered "overbought" and is sold
    rsi_lower : int
        The RSI lower limit, below which the assess is considered "oversold" and is bought
    """

    params = (("rsi_period", 14), ("rsi_upper", 70), ("rsi_lower", 30))

    def __init__(self):

        # Initialize global variables
        super().__init__()
        # Strategy level variables
        self.rsi_period = self.params.rsi_period
        self.rsi_upper = self.params.rsi_upper
        self.rsi_lower = self.params.rsi_lower

        if self.strategy_logging:
            print("===Strategy level arguments===")
            print("rsi_period :", self.rsi_period)
            print("rsi_upper :", self.rsi_upper)
            print("rsi_lower :", self.rsi_lower)
        self.rsi = bt.indicators.RelativeStrengthIndex(
            period=self.rsi_period,
            upperband=self.rsi_upper,
            lowerband=self.rsi_lower,
        )

    def buy_signal(self):
        return self.rsi[0] < self.rsi_lower

    def sell_signal(self):
        return self.rsi[0] > self.rsi_upper
