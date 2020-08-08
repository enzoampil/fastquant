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
from fastquant.indicators.custom import CustomIndicator


class CustomStrategy(BaseStrategy):
    """
    Simple moving average crossover strategy

    Parameters
    ----------
    upper_limit : float
        The upper value of the custom indicator above which, the asset is sold
    lower_limit : float
        The lower value of the custom indicator above which, the asset is sold

    """

    params = (
        ("upper_limit", 80),  # period for the fast moving average
        ("lower_limit", 20),
        ("custom_column", "custom"),
        ("type", "strength_index"), # Plan to have modes: strength_index (like RSI), crossover (like SMAC), binary (just boolean)
    )

    def __init__(self):
        # Initialize global variables
        super().__init__()
        # Strategy level variables
        self.upper_limit = self.params.upper_limit
        self.lower_limit = self.params.lower_limit
        self.custom_column = self.params.custom_column
        self.custom_indicator = CustomIndicator(
            self.data,
            custom_column=self.custom_column,
            upper_limit=self.params.upper_limit,
            lower_limit=self.params.lower_limit
        )

        print("===Strategy level arguments===")
        print("Upper limit :", self.upper_limit)
        print("Lower limit :", self.lower_limit)

    # Buy when the custom indicator is below the lower limit, and sell when it's above the upper limit
    def buy_signal(self):
        return self.custom_indicator[0] < self.lower_limit
        #return getattr(self.datas[0], self.custom_column) < self.lower_limit

    def sell_signal(self):
        return self.custom_indicator[0] > self.upper_limit
        #return getattr(self.datas[0], self.custom_column) > self.upper_limit