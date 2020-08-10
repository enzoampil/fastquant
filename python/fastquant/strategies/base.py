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
import backtrader.feeds as btfeed
import backtrader.analyzers as btanalyzers
import pandas as pd
import numpy as np
from collections.abc import Iterable
import time

# from fastquant.data import get_bt_news_sentiment
from fastquant.indicators import Sentiment

from fastquant.config import (
    INIT_CASH,
    COMMISSION_PER_TRANSACTION,
    DATA_FORMAT_MAPPING,
    GLOBAL_PARAMS,
    BUY_PROP,
    SELL_PROP,
)


class BaseStrategy(bt.Strategy):
    """
    Base Strategy template for all strategies to be added to fastquant
    """

    # Strategy level arguments
    # After initialization, the `params` variable becomes accessible as an attribute of the strategy object
    # with the properties of a `named tuple`
    params = (
        ("init_cash", INIT_CASH),
        ("buy_prop", BUY_PROP),
        ("sell_prop", SELL_PROP),
        ("commission", COMMISSION_PER_TRANSACTION),
        (
            "execution_type",
            "close",
        ),  # Either open or close, to indicate if a purchase is executed based on the next open or close
        ("periodic_logging", False),
        ("transaction_logging", True),
    )

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print("%s, %s" % (dt.isoformat(), txt))

    def __init__(self):
        # Global variables
        self.init_cash = self.params.init_cash
        self.buy_prop = self.params.buy_prop
        self.sell_prop = self.params.sell_prop
        self.execution_type = self.params.execution_type
        self.periodic_logging = self.params.periodic_logging
        self.transaction_logging = self.params.transaction_logging
        self.commission = self.params.commission
        print("===Global level arguments===")
        print("init_cash : {}".format(self.init_cash))
        print("buy_prop : {}".format(self.buy_prop))
        print("sell_prop : {}".format(self.sell_prop))
        print("commission : {}".format(self.commission))

        self.dataclose = self.datas[0].close
        self.dataopen = self.datas[0].open

        self.order = None
        self.buyprice = None
        self.buycomm = None
        # Number of ticks in the input data
        self.len_data = len(list(self.datas[0]))

    def buy_signal(self):
        return True

    def sell_signal(self):
        return True

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                if self.transaction_logging:
                    self.log(
                        "BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f"
                        % (
                            order.executed.price,
                            order.executed.value,
                            order.executed.comm,
                        )
                    )

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                if self.transaction_logging:
                    self.log(
                        "SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f"
                        % (
                            order.executed.price,
                            order.executed.value,
                            order.executed.comm,
                        )
                    )

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            if self.transaction_logging:
                if not self.periodic_logging:
                    self.log("Cash %s Value %s" % (self.cash, self.value))
                self.log("Order Canceled/Margin/Rejected")
                self.log("Canceled: {}".format(order.status == order.Canceled))
                self.log("Margin: {}".format(order.status == order.Margin))
                self.log("Rejected: {}".format(order.status == order.Rejected))

        # Write down: no pending order
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        if self.transaction_logging:
            self.log(
                "OPERATION PROFIT, GROSS %.2f, NET %.2f"
                % (trade.pnl, trade.pnlcomm)
            )

    def notify_cashvalue(self, cash, value):
        # Update cash and value every period
        if self.periodic_logging:
            self.log("Cash %s Value %s" % (cash, value))
        self.cash = cash
        self.value = value

    def stop(self):
        # Saving to self so it's accessible later during optimization
        self.final_value = self.broker.getvalue()
        self.pnl = round(self.final_value - self.init_cash, 2)
        print("Final Portfolio Value: {}".format(self.final_value))
        print("Final PnL: {}".format(self.pnl))

    def next(self):
        if self.periodic_logging:
            self.log("Close, %.2f" % self.dataclose[0])
        if self.order:
            return

        # Skip the last observation since purchases are based on next day closing prices (no value for the last observation)
        if len(self) + 1 >= self.len_data:
            return

        if self.periodic_logging:
            self.log("CURRENT POSITION SIZE: {}".format(self.position.size))
        # Only buy if there is enough cash for at least one stock
        if self.cash >= self.dataclose[0]:
            if self.buy_signal():

                if self.transaction_logging:
                    self.log("BUY CREATE, %.2f" % self.dataclose[0])
                # Take a 10% long position every time it's a buy signal (or whatever is afforded by the current cash position)
                # "size" refers to the number of stocks to purchase
                # Afforded size is based on closing price for the current trading day
                # Margin is required for buy commission
                # Add allowance to commission per transaction (avoid margin)
                afforded_size = int(
                    self.cash
                    / (self.dataclose[0] * (1 + self.commission + 0.001))
                )
                buy_prop_size = int(afforded_size * self.buy_prop)
                # Buy based on the closing price of the next closing day
                if self.execution_type == "close":
                    final_size = min(buy_prop_size, afforded_size)
                    if self.transaction_logging:
                        self.log("Cash: {}".format(self.cash))
                        self.log("Price: {}".format(self.dataclose[0]))
                        self.log("Buy prop size: {}".format(buy_prop_size))
                        self.log("Afforded size: {}".format(afforded_size))
                        self.log("Final size: {}".format(final_size))
                    # Explicitly setting exectype=bt.Order.Close will make the next day's closing the reference price
                    self.order = self.buy(size=final_size)
                # Buy based on the opening price of the next closing day (only works "open" data exists in the dataset)
                else:
                    # Margin is required for buy commission
                    afforded_size = int(
                        self.cash
                        / (self.dataopen[1] * (1 + self.commission + 0.001))
                    )
                    final_size = min(buy_prop_size, afforded_size)
                    if self.transaction_logging:
                        self.log("Buy prop size: {}".format(buy_prop_size))
                        self.log("Afforded size: {}".format(afforded_size))
                        self.log("Final size: {}".format(final_size))
                    self.order = self.buy(size=final_size)

        # Only sell if you hold least one unit of the stock (and sell only that stock, so no short selling)
        stock_value = self.value - self.cash
        if stock_value > 0:
            if self.sell_signal():
                if self.transaction_logging:
                    self.log("SELL CREATE, %.2f" % self.dataclose[1])
                # Sell a 5% sell position (or whatever is afforded by the current stock holding)
                # "size" refers to the number of stocks to purchase
                if self.execution_type == "close":
                    if SELL_PROP == 1:
                        self.order = self.sell(
                            size=self.position.size, exectype=bt.Order.Close
                        )
                    else:
                        # Sell based on the closing price of the next closing day
                        self.order = self.sell(
                            size=int(
                                (stock_value / (self.dataclose[1]))
                                * self.sell_prop
                            ),
                            exectype=bt.Order.Close,
                        )
                else:
                    # Sell based on the opening price of the next closing day (only works "open" data exists in the dataset)
                    self.order = self.sell(
                        size=int(
                            (self.init_cash / self.dataopen[1])
                            * self.sell_prop
                        )
                    )
