#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Import modules
import backtrader as bt
from fastquant.strategies.base import BaseStrategy
from fastquant.indicators import Sentiment


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
        print("===Strategy level arguments===")
        print("sentiment threshold :", self.senti)
        self.datasentiment = Sentiment(self.data)

    def buy_signal(self):
        return self.datasentiment[0] >= self.senti

    def sell_signal(self):
        return self.datasentiment[0] <= self.senti
