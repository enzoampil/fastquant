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
import backtrader.feeds as btfeed

# Import from package
from fastquant.indicators.sentiment import Sentiment
from fastquant.strategies.base import BaseStrategy


class SentimentStrategy(BaseStrategy):
    """
    SentimentStrategy
    Implementation of sentiment strategy using nltk/textblob pre-built sentiment models

    Parameters
    ----------
    senti : float
        The sentiment score threshold to indicate when to buy/sell

    TODO: Textblob implementation for Sentiment indicator

    """

    params = (("senti", 0.2),)

    def __init__(self):
        # Initialize global variables
        super().__init__()
        # Strategy level variables
        self.senti = self.params.senti

        if self.strategy_logging:
            print("===Strategy level arguments===")
            print("sentiment threshold :", self.senti)
        self.datasentiment = Sentiment(self.data)

    def buy_signal(self):
        return self.datasentiment[0] >= self.senti

    def sell_signal(self):
        return self.datasentiment[0] <= -self.senti


class SentimentDF(bt.feeds.PandasData):
    # Add a 'sentiment_score' line to the inherited ones from the base class
    lines = ("sentiment_score",)

    # automatically handle parameter with -1
    # add the parameter to the parameters inherited from the base class
    params = (("sentiment_score", -1),)
