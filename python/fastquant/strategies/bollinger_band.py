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


class BBandsStrategy(BaseStrategy):
    """
    Bollinger Bands strategy
    Simple implementation of backtrader BBands strategy reference: https://community.backtrader.com/topic/122/bband-strategy/2

    Parameters
    ----------
    period : int
        Period used as basis in calculating the moving average and standard deviation
    devfactor : int
        The number of standard deviations from the moving average to derive the upper and lower bands

    TODO: Study this strategy closer based on the above reference. Current implementation is naive.
    """

    params = (
        ("period", 20),  # period for the fast moving average
        ("devfactor", 2.0),
    )

    def __init__(self):
        # Initialize global variables
        super().__init__()
        # Strategy level variables
        self.period = self.params.period
        self.devfactor = self.params.devfactor

        if self.strategy_logging:
            print("===Strategy level arguments===")
            print("period :", self.period)
            print("devfactor :", self.devfactor)
        bbands = bt.ind.BBands(period=self.period, devfactor=self.devfactor)
        self.mid = bbands.mid
        self.top = bbands.top
        self.bot = bbands.bot

    def buy_signal(self):
        return self.dataclose[0] < self.bot

    def sell_signal(self):
        return self.dataclose[0] > self.top
