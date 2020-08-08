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


class CustomIndicator(bt.Indicator):

    """
    Custom Indicator
    """

    lines = ("custom",)

    params = (
        ("custom_column", "custom"),
        ("upper_limit", 95),
        ("lower_limit", 5),
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

    def __init__(self):
        super().__init__()
        self.custom_column = self.params.custom_column
        self.upper_limit = self.params.upper_limit
        self.lower_limit = self.params.lower_limit

        # Plotting lines are based on the upper and lower limits
        CustomIndicator.plotinfo = dict(
            plotymargin=0.15, plothlines=[0], plotyticks=[self.upper_limit, self.lower_limit]
        )

    def _plotlabel(self):
        return

    def next(self):
        self.lines.custom[0] = getattr(self.datas[0], self.custom_column)[0]
