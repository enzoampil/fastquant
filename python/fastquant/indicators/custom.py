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

    params = (("custom_column", "custom"),)

    plotinfo = dict(
        plotymargin=0.15,
        plothlines=[0],
        plotyticks=[5, 95],
    )

    def __init__(self):
        super().__init__()
        self.custom_column = self.params.custom_column

    def _plotlabel(self):
        return

    def next(self):
        self.lines.custom[0] = getattr(self.datas[0], self.custom_column)[0]
