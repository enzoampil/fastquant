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
import warnings
import logging

# Import modules
import backtrader as bt
import backtrader.feeds as btfeed
import backtrader.analyzers as btanalyzers
import pandas as pd
import numpy as np
from collections.abc import Iterable
import time
from fastquant.notification import trigger_bot
import croniter


from fastquant.config import (
    INIT_CASH,
    COMMISSION_PER_TRANSACTION,
    GLOBAL_PARAMS,
    BUY_PROP,
    SELL_PROP,
    SHORT_MAX,
)
from fastquant.utils.strategy_logging import StrategyLogger


class BaseStrategy(bt.Strategy):
    """
    Base Strategy template for all strategies to be added to fastquant

    Attributes
    ----------
    init_cash
    buy_proportion
    sell_proportion
    commission
    stop_loss_percent
    stop_trail_percent
    take_profit_percent
    execution_type
    allow_short_selling
    max_short_ratio
    add_cash_amount
    add_cash_frequency
    channel
    symbol

    Modified/Removed:
        init_cash   :initial_cash
        buy_prop    :buy_proportion
        sell_prop   :sell_proportion
        stop_loss   :stop_loss_percent
        stop_trail  :stop_trail_percent
        periodic_logging
        strategy_logging
        allow_short : allow_short_selling
        short_max   : max_short_ratio
        add_cash_freq : add_cash_frequency



    """

    """"
    init
    buy_signal
    sell_signal
    update_logging

    """

    # Set default parameters
    # After initialization, the `params` variable becomes accessible as an attribute of the strategy object
    # with the properties of a `named tuple`
    params = (
        ("init_cash", INIT_CASH),
        ("custom", 10),
        ("custom2", 20),
        ("buy_prop", BUY_PROP),
        ("sell_prop", SELL_PROP),
        ("commission", COMMISSION_PER_TRANSACTION),
        ("stop_loss", 0),  # Zero means no stop loss
        ("stop_trail", 0),  # Zero means no stop loss
        # Either open or close, to indicate if a purchase is executed based on the next open or close
        ("execution_type", "market"),
        ("periodic_logging", False),
        ("transaction_logging", True),
        ("strategy_logging", True),
        ("channel", ""),
        ("symbol", ""),
        ("allow_short", False),
        ("short_max", SHORT_MAX),
        ("add_cash_amount", 0),
        ("add_cash_freq", "M"),
    )

    def __init__(self):

        # print("sadsads", self.params.custom)
        print(type(self.params.custom2))

        self.initial_cash = self.params.init_cash
        self.buy_proportion = self.params.buy_prop
        self.sell_proportion = self.params.sell_prop
        self.execution_type = self.params.execution_type
        self.periodic_logging = self.params.periodic_logging
        self.transaction_logging = self.params.transaction_logging
        self.strategy_logging = self.params.strategy_logging
        self.commission = self.params.commission
        self.channel = self.params.channel
        self.stop_loss_percent = self.params.stop_loss
        self.stop_trail_percent = self.params.stop_trail
        self.allow_short_selling = self.params.allow_short
        self.max_short_ratio = self.params.short_max

        self.broker.set_coc(True)
        add_cash_frequency = self.params.add_cash_freq

        # Longer term, we plan to add `freq` like notation, similar to pandas datetime
        # https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html
        # M means add cash at the first day of each month
        if add_cash_frequency == "M":
            self.add_cash_frequency = "0 0 1 * *"
        # W means add cash once a week on monday
        elif add_cash_frequency == "W":
            self.add_cash_frequency = "0 0 * * 1"
        # Otherwise, it assumes the input is in cron notation (no change)
        else:
            self.add_cash_frequency = add_cash_frequency

        self.add_cash_amount = self.params.add_cash_amount
        # Attribute that tracks how much cash was added over time
        self.total_cash_added = 0

        # Create logging handler
        self.logging = StrategyLogger(self)
        self.logging.strategy_argments()

        self.order_history_df = None
        self.periodic_history_df = None

        self.dataclose = self.datas[0].close
        self.dataopen = self.datas[0].open

        self.order = None
        self.buyprice = None
        self.buycomm = None
        # Number of ticks in the input data
        self.len_data = len(list(self.datas[0]))
        # Sets the latest action as "buy", "sell", or "neutral"
        self.action = None

        # Warn if user forgets to set a value to commission
        if self.commission == 0:
            warnings.warn(
                "Comission value is set to 0. This might yield unrealistic results. Set using the `commission` paramter in `backtest()`",
                UserWarning,
            )

    def buy_signal(self):
        return False  # Safer to set default action to do nothing

    def sell_signal(self):
        return False  # Safer to set default action to do nothing

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:

            if order.isbuy():
                self.action = "buy"
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm

            else:  # Sell
                self.action = "sell"

            self.bar_executed = len(self)
            self.logging.order_executed(order, action=self.action.upper())

            # Update order history whenever an order is completed
            self.logging.update_order_history(order)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.logging.order_aborted(order)

        # Write down: no pending order
        self.order = None

    def notify_trade(self, trade):
        if trade.isclosed:
            self.logging.trade_closed(trade)
        else:
            return

    def notify_cashvalue(self, cash, value):
        # Update cash and value every period
        self.cash = cash
        self.value = value
        self.logging.cash_value()

    def stop(self):
        # Saving to self so it's accessible later during optimization
        self.final_value = self.broker.getvalue()
        # Note that PnL is the final portfolio value minus the initial cash balance minus the total cash added
        self.pnl = round(
            self.final_value - self.initial_cash - self.total_cash_added, 2
        )
        if self.strategy_logging:
            self.logging.log(
                "Final Portfolio Value: {}".format(self.final_value)
            )
            self.logging.log("Final PnL: {}".format(self.pnl))

        # Create dataframe from logging module
        self.order_history_df = pd.DataFrame(self.logging.order_history)
        self.periodic_history_df = pd.DataFrame(self.logging.periodic_history)
        self.trade_history_df = pd.DataFrame(self.logging.trade_history)

        last_date = str(self.datas[0].datetime.date(0))
        if self.channel:
            trigger_bot(
                self.symbol,
                self.action,
                last_date,
            )

    def start(self):
        # Used to signal setting the first iteration
        self.first_timepoint = True

    def periodic_cash_in(self):

        if self.first_timepoint:
            # Change state to indicate that the cash date iterator has been set
            self.first_timepoint = False

            # Initialize income date iterator, and set next
            start_date = self.datas[0].datetime.datetime(0)
            self.cron = croniter.croniter(self.add_cash_frequency, start_date)
            self.next_cash_datetime = self.cron.get_next(datetime.datetime)

            self.logging.initialize_periodic_cash_in(
                start_date, self.next_cash_datetime
            )

        # Add cash to broker if date is same or later to the next income date
        # This means if the dataset is only for weekdays, a date on a weekend will be executed on the next monday
        if self.datas[0].datetime.datetime(0) >= self.next_cash_datetime:
            self.broker.add_cash(self.add_cash_amount)
            self.next_cash_datetime = self.cron.get_next(datetime.datetime)
            self.total_cash_added += self.add_cash_amount

            self.logging.periodic_cash_in(
                self.add_cash_amount,
                self.total_cash_added,
                self.next_cash_datetime,
            )

    def next(self):
        if self.add_cash_amount > 0:
            self.periodic_cash_in()  # Trigger only when amount is specified

        self.logging.update_periodic_history()  # dt, position_value, position_size, cash,

        if self.order:
            return

        # Skip the last observation since purchases are based on next day closing prices (no value for the last observation)
        if len(self) + 1 >= self.len_data:
            return

        # Allow for backwards compatibilty; older strategies return only the signal, new strategies can return both signal and buy/sell proportion
        buy_signal_response = self.buy_signal()
        sell_signal_response = self.sell_signal()
        if type(buy_signal_response) == bool:
            buy_signal, buy_prop = buy_signal_response, None
        else:
            buy_signal, buy_prop = buy_signal_response

        if type(sell_signal_response) == bool:
            sell_signal, sell_prop = sell_signal_response, None
        else:
            sell_signal, sell_prop = sell_signal_response

        if buy_signal:
            self.create_buy_order(buy_prop)
            # self.action will be set order is completed

        elif sell_signal:
            self.create_sell_order(sell_prop)
            # self.action will be set order is completed

        else:
            self.action = "neutral"

    def create_buy_order(self, buy_proportion=None):
        """
        Returns
        -------
        order
        """

        # Buy based on the current closing price
        if self.execution_type == "market":
            market_price = self.dataclose[0]

        # Buy based on the next closing price
        elif self.execution_type == "close":
            market_price = self.dataclose[1]

        afforded_size = int(self.cash / (market_price * (1 + self.commission)))

        # Compute number of units to buy based on the proportion
        if buy_proportion is None:
            buy_proportion_size = int(afforded_size * self.buy_proportion)
        else:
            buy_proportion_size = int(afforded_size * buy_proportion)

        final_size = min(buy_proportion_size, afforded_size)

        # Log that buy signal is triggered
        self.logging.buy_signal(
            self.cash,
            market_price,
            buy_proportion_size,
            afforded_size,
            final_size,
        )

        # Buy only if final size is > 0
        if final_size > 0:

            # Buy on today's closing price
            if self.execution_type == "market":
                self.order = self.buy(
                    size=final_size, exectype=bt.Order.Market
                )
                self.logging.order_created(
                    order_type_str="buy",
                    text="Order type: %s Price: %.2f"
                    % (self.execution_type, market_price),
                )

            # Buy on tomorrow's closing price
            elif self.execution_type == "close":
                self.order = self.buy(size=final_size, exectype=bt.Order.Close)
                self.logging.order_created(
                    order_type_str="buy",
                    text="Order type: %s Price: %.2f"
                    % (self.execution_type, market_price),
                )

            # create stop loss order
            if self.stop_loss_percent:
                stop_price = market_price * (1.0 - self.stop_loss_percent)
                self.sell(
                    exectype=bt.Order.Stop,
                    price=stop_price,
                    size=size,
                )
                self.logging.order_created(
                    order_type_str="buy",
                    text="Order type: %s Price: %.2f"
                    % ("Stop Order", stop_price),
                )

            # create trailing stop order
            if self.stop_trail_percent:
                self.sell(
                    exectype=bt.Order.StopTrail,
                    trailpercent=self.stop_trail_percent,
                    size=final_size,
                )
                self.logging.order_created(
                    order_type_str="buy",
                    text="Order type: %s Trail Percent: %.2f"
                    % ("Trailing Stop", self.stop_trail_percent),
                )

    def create_short_sell_order(self, sell_proportion=None):
        # Sell short based on the closing price of the previous day
        if self.execution_type == "close":

            sell_proportion_size = int(
                self.sell_proportion
                * self.broker.getvalue()
                / self.dataclose[1]
            )
            # The max incremental short allowed is the short that would lead to a cumulative short position
            # equal to the maximum short position (initial cash times the maximum short ratio, which is 1.5 by default)
            max_position_size = max(
                int(
                    self.broker.getvalue()
                    * self.max_short_ratio
                    / self.dataclose[1]
                )
                + self.position.size,
                0,
            )
            if max_position_size > 0:
                if self.transaction_logging:
                    self.log("SELL CREATE, %.2f" % self.dataclose[1])
                self.order = self.sell(
                    size=min(sell_proportion_size, max_position_size)
                )

        # Buy based on the opening price of the next closing day (only works "open" data exists in the dataset)
        else:

            sell_proportion_size = int(
                self.sell_proportion
                * self.broker.getvalue()
                / self.dataopen[1]
            )
            # The max incremental short allowed is the short that would lead to a cumulative short position
            # equal to the maximum short position (initial cash times the maximum short ratio, which is 1.5 by default)
            max_position_size = max(
                int(
                    self.broker.getvalue()
                    * self.max_short_ratio
                    / self.dataopen[1]
                )
                + self.position.size,
                0,
            )
            if max_position_size > 0:
                if self.transaction_logging:
                    self.log("SELL CREATE, %.2f" % self.dataopen[1])
                self.order = self.sell(
                    size=min(sell_proportion_size, max_position_size)
                )

    def create_sell_order(self, sell_proportion=None):

        if self.allow_short_selling:
            self.create_short_sell_order(sell_proportion)

        # Only sell if you hold least one unit of the stock (and sell only that stock, so no short selling)
        elif self.position.size > 0:

            # Verify that you could actually sell based on the sell proportion and the units owned
            if sell_proportion is None:
                sell_proportion = self.sell_proportion

            sell_proportion_size = int(self.position.size * sell_proportion)

            # Log that sell signal was triggered
            self.logging.sell_signal(
                size=sell_proportion_size,
                price=(
                    self.dataclose[0]
                    if self.execution_type == "market"
                    else self.dataclose[1]
                ),
            )

            if sell_proportion_size > 0:

                # Sell on current closing price
                if self.execution_type == "market":
                    self.order = self.sell(
                        size=sell_proportion_size, exectype=bt.Order.Market
                    )
                    sell_price = self.dataclose[0]
                    self.logging.order_created(
                        order_type_str="sell",
                        text="Order type: %s Price: %.2f"
                        % (self.execution_type, sell_price),
                    )

                # Sell on next closing price
                elif self.execution_type == "close":
                    self.order = self.sell(
                        size=sell_proportion_size, exectype=bt.Order.Close
                    )
                    sell_price = self.dataclose[1]
                    self.logging.order_created(
                        order_type_str="sell",
                        text="Order type: %s Price: %.2f"
                        % (self.execution_type, sell_price),
                    )
