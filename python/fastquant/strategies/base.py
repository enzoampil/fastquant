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
    init_cash : float
        inital cash
    buy_prop : float
        buy proportion, percentage of available units to buy, setting to 1.0 buys all afforded units
    sell_prop : float
        sell proportion, percentage of owned units to sell
    commission: float
        Percentage of comission
    stop_loss : float
        stop loss percent
    stop_trail : float
        stop trail percent
    execution_type : str {`market`,`close`} (default=`market`)
        If set to `market`, excecutes the action (buy or sell) at current bar (or day),
        If set to `close`, executees the action on the next available bar
    allow_short : bool (default=False)
        allow short selling
    short_max : float
        The max incremental short allowed is the short that would lead to a cumulative short position
        equal to the maximum short position (initial cash times the maximum short ratio, which is 1.5 by default)
    add_cash_amount : int (default=0)
        Added cash amount for periodic cash-ins. (can be used in cost averaging)
    add_cash_frequency : str {`W` or `M`} (default=`W`)
        Frequency of when to add cash (weekly or monthly)
    channel: str (default=`""`)
        Notification channel
    symbol: str
        Symbol of the asset traded

    Renamed in code:
        init_cash   :initial_cash
        buy_prop    :buy_proportion
        sell_prop   :sell_proportion
        stop_loss   :stop_loss_percent
        stop_trail  :stop_trail_percent
        periodic_logging
        strategy_logging
        allow_short : allow_short_selling
        short_max   : max_short_ratio
        add_cash_freq :
            add_cash_frequency

    """

    # Set default parameters
    # After initialization, the `params` variable becomes accessible as an attribute of the strategy object
    # with the properties of a `named tuple`
    params = (
        ("init_cash", INIT_CASH),
        ("buy_prop", BUY_PROP),
        ("sell_prop", SELL_PROP),
        ("fractional", False), 
        ("commission", COMMISSION_PER_TRANSACTION),
        ("stop_loss", 0),  # Zero means no stop loss
        ("stop_trail", 0),  # Zero means no stop loss
<<<<<<< HEAD
        # Either open or close, to indicate if a purchase is executed based on the next open or close
        ("execution_type", "market"),
=======
        ("take_profit", 0), # Zero means no take profit
        (
            "execution_type",
            "close",
        ),  # Either open or close, to indicate if a purchase is executed based on the next open or close
>>>>>>> master
        ("periodic_logging", False),
        ("transaction_logging", True),
        ("strategy_logging", True),
        ("channel", ""),
        ("symbol", ""),
        ("allow_short", False),
        ("short_max", SHORT_MAX),
        ("add_cash_amount", 0),
        ("add_cash_freq", "M"),
        ("invest_div", True),
    )

    def __init__(self):

        self.initial_cash = self.params.init_cash
        self.buy_proportion = self.params.buy_prop
        self.sell_proportion = self.params.sell_prop
        self.execution_type = self.params.execution_type
        self.periodic_logging = self.params.periodic_logging
        self.transaction_logging = self.params.transaction_logging
        self.strategy_logging = self.params.strategy_logging
        self.fractional = self.params.fractional
        self.commission = self.params.commission
        self.channel = self.params.channel
<<<<<<< HEAD
        self.stop_loss_percent = self.params.stop_loss
        self.stop_trail_percent = self.params.stop_trail
        self.allow_short_selling = self.params.allow_short
        self.max_short_ratio = self.params.short_max

=======
        self.stop_loss = self.params.stop_loss
        self.stop_trail = self.params.stop_trail
        self.take_profit = self.params.take_profit
        self.allow_short = self.params.allow_short
        self.short_max = self.params.short_max
        self.invest_div = self.params.invest_div
>>>>>>> master
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

<<<<<<< HEAD
        # Create logging handler
        self.logging = StrategyLogger(self)
        self.logging.strategy_argments()

=======
        if self.strategy_logging:
            self.log("===Global level arguments===")
            self.log("init_cash : {}".format(self.init_cash))
            self.log("buy_prop : {}".format(self.buy_prop))
            self.log("sell_prop : {}".format(self.sell_prop))
            self.log("commission : {}".format(self.commission))
            self.log("stop_loss : {}".format(self.stop_loss))
            self.log("stop_trail : {}".format(self.stop_trail))
            self.log("take_profit : {}".format(self.take_profit))

        self.order_history = {
            "dt": [],
            "type": [],
            "price": [],
            "size": [],
            "value": [],
            "commission": [],
            "pnl": [],
        }
        self.periodic_history = {
            "dt": [],
            "portfolio_value": [],
            "cash": [],
        }
>>>>>>> master
        self.order_history_df = None
        self.periodic_history_df = None

        self.dataclose = self.datas[0].close
        self.dataopen = self.datas[0].open

        # Assign self.datadiv if dividend attribute is found
        self.datadiv = None
        if hasattr(self.datas[0],'dividend'):
            self.datadiv = self.datas[0].dividend  

        self.order = None
        self.buyprice = None
        self.buycomm = None
        # Number of ticks in the input data
        self.len_data = len(list(self.datas[0]))
        # Sets the latest action as "buy", "sell", or "neutral"
        self.action = None
        # Initialize price bought
        self.price_bought = 0

        # Initialize stoploss order
        self.stoploss_order = None

        # Initialize stoploss trail order
        self.stoploss_trail_order = None

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

    def take_profit_signal(self):
        return True

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
            self.logging.update_order_history(order, self.execution_type)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.logging.order_aborted(order)

        # Write down: no pending order
        self.order = None

    def notify_trade(self, trade):
        if trade.isclosed:
            self.logging.trade_closed(trade)
        else:
            return
<<<<<<< HEAD
=======
        if self.transaction_logging:
            self.log(
                "OPERATION PROFIT, GROSS: %.2f, NET: %.2f"
                % (trade.pnl, trade.pnlcomm)
            )
>>>>>>> master

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
<<<<<<< HEAD
            self.final_value - self.initial_cash - self.total_cash_added, 2
=======
            self.final_value - self.init_cash - self.total_cash_added, 2
>>>>>>> master
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

<<<<<<< HEAD
    def periodic_cash_in(self):

        if self.first_timepoint:
            # Change state to indicate that the cash date iterator has been set
            self.first_timepoint = False
=======
    def next(self):

        # add dividend to cash
        if self.invest_div and self.datadiv != None:
            self.broker.add_cash(self.datadiv)

        if self.add_cash_amount:
            if self.first_timepoint:
                # Initialize income date iterator, and set next
                start_date = self.datas[0].datetime.datetime(0)
                self.cron = croniter.croniter(self.add_cash_freq, start_date)
                self.next_cash_datetime = self.cron.get_next(datetime.datetime)

                if self.transaction_logging:
                    self.log(
                        "Start date: {}".format(
                            start_date.strftime("%Y-%m-%d")
                        )
                    )
                    self.log(
                        "Next cash date: {}".format(
                            self.next_cash_datetime.strftime("%Y-%m-%d")
                        )
                    )
>>>>>>> master

            # Initialize income date iterator, and set next
            start_date = self.datas[0].datetime.datetime(0)
            self.cron = croniter.croniter(self.add_cash_frequency, start_date)
            self.next_cash_datetime = self.cron.get_next(datetime.datetime)

            self.logging.initialize_periodic_cash_in(
                start_date, self.next_cash_datetime
            )

<<<<<<< HEAD
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
=======
                if self.transaction_logging:
                    self.log("Cash added: {}".format(self.add_cash_amount))
                    self.log(
                        "Total cash added: {}".format(self.total_cash_added)
                    )
                    self.log(
                        "Next cash date: {}".format(
                            self.next_cash_datetime.strftime("%Y-%m-%d")
                        )
                    )
>>>>>>> master

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

<<<<<<< HEAD
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
=======
        # Only buy if there is enough cash for at least one stock
        if self.buy_signal():
            # Alternative for fractional condition based in min amount of significant value: 
            #(self.fractional and self.cash >= self.dataclose[0] / 10000)
            if (self.fractional and self.cash >= 10) or (not self.fractional and self.cash >= self.dataclose[0]):
                
                if self.transaction_logging:
                    self.log("BUY CREATE, %.2f" % self.dataclose[0])
                # Take a 10% long position every time it's a buy signal (or whatever is afforded by the current cash position)
                # "size" refers to the number of stocks to purchase
                # Afforded size is based on closing price for the current trading day
                # Margin is required for buy commission
                # Add allowance to commission per transaction (avoid margin)
                afforded_size = self.cash / (self.dataclose[0] * (1 + self.commission + 0.001))
                buy_prop_size = afforded_size * self.buy_prop

                # Used for take profit method
                self.price_bought = self.data.close[0]

                # Buy based on the closing price of the previous closing day
                if self.execution_type == "close":
                    final_size = min(buy_prop_size, afforded_size)
                    if not self.fractional:
                        final_size = int(final_size)
                    if self.transaction_logging:
                        self.log("Cash: {}".format(self.cash))
                        self.log("Price: {}".format(self.dataclose[0]))
                        self.log("Buy prop size: {}".format(buy_prop_size))
                        self.log("Afforded size: {}".format(afforded_size))
                        self.log("Final size: {}".format(final_size))
                    # Explicitly setting exectype=bt.Order.Close will make the next day's closing the reference price
                    self.order = self.buy(size=final_size)

                    # Implement stop loss at the purchase level (only this specific trade is closed)
                    if self.stop_loss:
                        stop_price = self.data.close[0] * (
                            1.0 - self.stop_loss
                        )
                        if self.transaction_logging:
                            self.log("Stop price: {}".format(stop_price))
                        self.stoploss_order = self.sell(
                            exectype=bt.Order.Stop,
                            price=stop_price,
                            size=final_size,
                        )

                    if self.stop_trail:
                        # Create a stoploss trail order if None
                        if self.stoploss_trail_order == None:
                            if self.transaction_logging:
                                self.log("Stop trail: {}".format(self.stop_trail))
                            self.stoploss_trail_order = self.sell(
                                exectype=bt.Order.StopTrail,
                                trailpercent=self.stop_trail,
                                size=final_size,
                            )
                        # Cancel existing stoploss trail order
                        else:
                            self.cancel(self.stoploss_trail_order)
                            

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

                    # Implement stop loss at the purchase level (only this specific trade is closed)
                    if self.stop_loss:
                        stop_price = self.data.close[0] * (
                            1.0 - self.stop_loss
                        )
                        if self.transaction_logging:
                            self.log("Stop price: {}".format(stop_price))
                        self.stoploss_order = self.sell(
                            exectype=bt.Order.Stop,
                            price=stop_price,
                            size=final_size,
                        )

                    if self.stop_trail:
                        if self.transaction_logging:
                            self.log("Stop trail: {}".format(self.stop_trail))
                        self.stoploss_trail_order = self.sell(
                            exectype=bt.Order.StopTrail,
                            trailpercent=self.stop_trail,
                            size=final_size,
                        )

        elif self.sell_signal():
            if self.allow_short:

                # Sell short based on the closing price of the previous day
                if self.execution_type == "close":

                    sell_prop_size = int(
                        SELL_PROP * self.broker.getvalue() / self.dataclose[1]
                    )
                    # The max incremental short allowed is the short that would lead to a cumulative short position
                    # equal to the maximum short position (initial cash times the maximum short ratio, which is 1.5 by default)
                    max_position_size = max(
                        int(
                            self.broker.getvalue()
                            * self.short_max
                            / self.dataclose[1]
                        )
                        + self.position.size,
                        0,
                    )
                    if max_position_size > 0:
                        if self.transaction_logging:
                            self.log("SELL CREATE, %.2f" % self.dataclose[1])
                        self.order = self.sell(
                            size=min(sell_prop_size, max_position_size)
                        )

                # Buy based on the opening price of the next closing day (only works "open" data exists in the dataset)
                else:

                    sell_prop_size = int(
                        SELL_PROP * self.broker.getvalue() / self.dataopen[1]
                    )
                    # The max incremental short allowed is the short that would lead to a cumulative short position
                    # equal to the maximum short position (initial cash times the maximum short ratio, which is 1.5 by default)
                    max_position_size = max(
                        int(
                            self.broker.getvalue()
                            * self.short_max
                            / self.dataopen[1]
                        )
                        + self.position.size,
                        0,
                    )
                    if max_position_size > 0:
                        if self.transaction_logging:
                            self.log("SELL CREATE, %.2f" % self.dataopen[1])
                        self.order = self.sell(
                            size=min(sell_prop_size, max_position_size)
                        )
>>>>>>> master

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
<<<<<<< HEAD
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
=======
                # Sell a 5% sell position (or whatever is afforded by the current stock holding)
                # "size" refers to the number of stocks to purchase
                if self.execution_type == "close":
                    if SELL_PROP == 1:
                        self.order = self.sell(
                            size=self.position.size, exectype=bt.Order.Close
                        )
                    else:
                        # Sell based on the closing price of the previous closing day
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

            # Explicitly cancel stoploss order
            if self.stoploss_order:
                self.cancel(self.stoploss_order)
            
            # Explicitly cancel stoploss trail order
            if self.stoploss_trail_order:
                self.cancel(self.stoploss_trail_order)

        elif self.take_profit_signal():
            # Take profit 
            price_limit = self.price_bought * (1 + self.take_profit)
            
            # Take profit is only triggered when there is a net long position (positive position size)
            # TODO: Make take profit (and stop loss) supported for both net long and short positions
            if self.take_profit and self.position.size > 0:
                if self.data.close[0] >= price_limit:
                    self.sell(
                        exectype=bt.Order.Close, price=price_limit, size=self.position.size,
>>>>>>> master
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
