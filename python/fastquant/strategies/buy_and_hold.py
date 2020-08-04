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


class BuyAndHoldStrategy(BaseStrategy):
    """
    Buy and Hold Strategy
    """

    def _init_(self):
        # Initialize global variables
        super().__init__()
        # Strategy level variables
        self.buy_and_hold = None
        self.buy_and_hold_sell = None

    def buy_signal(self):
        if not self.position:
            self.buy_and_hold = True
        return self.buy_and_hold

    def sell_signal(self):
        if (len(self) + 2) >= self.len_data:
            self.buy_and_hold_sell = True
        else:
            self.buy_and_hold_sell = False
        return self.buy_and_hold_sell
