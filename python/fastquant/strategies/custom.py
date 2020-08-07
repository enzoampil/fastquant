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
        ("upper_limit", 80),  # period for the fast moving average
        ("lower_limit", 20),
    )

    def __init__(self):
        # Initialize global variables
        super().__init__()
        # Strategy level variables
        self.upper_limit = self.params.upper_limit
        self.lower_limit = self.params.lower_limit
        self.custom = self.lines.custom[0]

        print("===Strategy level arguments===")
        print("Upper limit :", self.upper_limit)
        print("Lower limit :", self.lower_limit)

    # Buy when the custom indicator is below the lower limit, and sell when it's above the upper limit
    def buy_signal(self):
        return self.custom < self.lower_limit

    def sell_signal(self):
        return self.custom > self.upper_limit