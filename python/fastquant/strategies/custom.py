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
    implements a chosen dataframe column as a custom indicator (column name set as "custom" by default).
    
    The strategy is structured similar to RSIStrategy where you can set an upper_limit, above which the asset is sold (considered "overbought"), and a lower_limit, below which the asset is sold (considered "underbought). upper_limit is set to 95 by default, while lower_limit is set to 5 by default.

    Parameters
    ----------
    upper_limit : float
        The upper value of the custom indicator above which, the asset is sold
    lower_limit : float
        The lower value of the custom indicator above which, the asset is sold
    custom_column : str
        The name of the column in the dataframe that corresponds to the custom indicator

    """

    params = (
        ("upper_limit", 95),
        ("lower_limit", 5),
        ("custom_column", "custom"),
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
        )
        # Plotting lines are based on the upper and lower limits
        self.custom_indicator.plotinfo.plotyticks = [self.lower_limit, self.upper_limit]

        print("===Strategy level arguments===")
        print("Upper limit: ", self.upper_limit)
        print("Lower limit: ", self.lower_limit)

    # Buy when the custom indicator is below the lower limit, and sell when it's above the upper limit
    def buy_signal(self):
        return self.custom_indicator[0] < self.lower_limit

    def sell_signal(self):
        return self.custom_indicator[0] > self.upper_limit
