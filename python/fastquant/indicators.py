#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Import standard library
from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)
from pkg_resources import resource_filename
import datetime
import sys

# Import modules
import backtrader as bt


class Sentiment(bt.Indicator):

    """
    Sentiment Custom Indicator
    Implementation of sentiment custom indicator using nltk/textblob pre-built sentiment models

    Parameters
    ----------
    agg_sentiment : dict
        The scraped dictionary with key, value pair of date, sentiment score. This is handled automatically by get_bt_news in senti_scraper.

    """

    lines = ("sentiment",)
    params = (("agg_sentiment", None),)

    plotinfo = dict(
        plotymargin=0.15, plothlines=[0], plotyticks=[1.0, 0, -1.0]
    )

    plotlines = dict(
        sentiment=dict(
            alpha=0.85,
            width=1.0,
            _method="bar",
            _plotvalue=True,
            _plotvaluetag=False,
            _name=" ",
            _skipnan=True,
            _samecolor=False,
        )
    )

    def _plotlabel(self):
        return

    def next(self):
        date = self.datas[0].datetime.date(0)
        agg_sentiment = self.params.agg_sentiment
        if date in agg_sentiment:
            self.lines.sentiment[0] = agg_sentiment[date]
