# #!/usr/bin/env python3
# # -*- coding: utf-8 -*-
# # Import standard library
# from __future__ import (
#     absolute_import,
#     division,
#     print_function,
#     unicode_literals,
# )
# from pkg_resources import resource_filename
# import datetime
# import sys

# # Import modules
# import backtrader as bt
# import backtrader.feeds as btfeed
# import backtrader.analyzers as btanalyzers
# import pandas as pd
# import numpy as np
# from collections.abc import Iterable
# import time
# from .fastquant import get_bt_news_sentiment
# from .indicators import Sentiment

# # Global arguments
# INIT_CASH = 100000
# COMMISSION_PER_TRANSACTION = 0.0075
# DATA_FILE = resource_filename(__name__, "data/JFC_20180101_20190110_DCV.csv")

# BUY_PROP = 1
# SELL_PROP = 1
# DATA_FORMAT_MAPPING = {
#     "cv": {
#         "datetime": 0,
#         "open": None,
#         "high": None,
#         "low": None,
#         "close": 1,
#         "volume": 2,
#         "openinterest": None,
#     },
#     "c": {
#         "datetime": 0,
#         "open": None,
#         "high": None,
#         "low": None,
#         "close": 1,
#         "volume": None,
#         "openinterest": None,
#     },
# }
# GLOBAL_PARAMS = ["init_cash", "buy_prop", "sell_prop", "execution_type"]


# def docstring_parameter(*sub):
#     def dec(obj):
#         obj.__doc__ = obj.__doc__.format(*sub)
#         return obj

#     return dec


# class BaseStrategy(bt.Strategy):
#     """
#     Base Strategy template for all strategies to be added to fastquant
#     """

#     # Strategy level arguments
#     # After initialization, the `params` variable becomes accessible as an attribute of the strategy object
#     # with the properties of a `named tuple`
#     params = (
#         ("init_cash", INIT_CASH),
#         ("buy_prop", BUY_PROP),
#         ("sell_prop", SELL_PROP),
#         ("commission", COMMISSION_PER_TRANSACTION),
#         (
#             "execution_type",
#             "close",
#         ),  # Either open or close, to indicate if a purchase is executed based on the next open or close
#         ("periodic_logging", False),
#         ("transaction_logging", True),
#     )

#     def log(self, txt, dt=None):
#         dt = dt or self.datas[0].datetime.date(0)
#         print("%s, %s" % (dt.isoformat(), txt))

#     def __init__(self):
#         # Global variables
#         self.init_cash = self.params.init_cash
#         self.buy_prop = self.params.buy_prop
#         self.sell_prop = self.params.sell_prop
#         self.execution_type = self.params.execution_type
#         self.periodic_logging = self.params.periodic_logging
#         self.transaction_logging = self.params.transaction_logging
#         self.commission = self.params.commission
#         print("===Global level arguments===")
#         print("init_cash : {}".format(self.init_cash))
#         print("buy_prop : {}".format(self.buy_prop))
#         print("sell_prop : {}".format(self.sell_prop))
#         print("commission : {}".format(self.commission))

#         self.dataclose = self.datas[0].close
#         self.dataopen = self.datas[0].open

#         self.order = None
#         self.buyprice = None
#         self.buycomm = None
#         # Number of ticks in the input data
#         self.len_data = len(list(self.datas[0]))

#     def buy_signal(self):
#         return True

#     def sell_signal(self):
#         return True

#     def notify_order(self, order):
#         if order.status in [order.Submitted, order.Accepted]:
#             return

#         if order.status in [order.Completed]:
#             if order.isbuy():
#                 if self.transaction_logging:
#                     self.log(
#                         "BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f"
#                         % (
#                             order.executed.price,
#                             order.executed.value,
#                             order.executed.comm,
#                         )
#                     )

#                 self.buyprice = order.executed.price
#                 self.buycomm = order.executed.comm
#             else:  # Sell
#                 if self.transaction_logging:
#                     self.log(
#                         "SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f"
#                         % (
#                             order.executed.price,
#                             order.executed.value,
#                             order.executed.comm,
#                         )
#                     )

#             self.bar_executed = len(self)

#         elif order.status in [order.Canceled, order.Margin, order.Rejected]:
#             if self.transaction_logging:
#                 if not self.periodic_logging:
#                     self.log("Cash %s Value %s" % (self.cash, self.value))
#                 self.log("Order Canceled/Margin/Rejected")
#                 self.log("Canceled: {}".format(order.status == order.Canceled))
#                 self.log("Margin: {}".format(order.status == order.Margin))
#                 self.log("Rejected: {}".format(order.status == order.Rejected))

#         # Write down: no pending order
#         self.order = None

#     def notify_trade(self, trade):
#         if not trade.isclosed:
#             return
#         if self.transaction_logging:
#             self.log(
#                 "OPERATION PROFIT, GROSS %.2f, NET %.2f"
#                 % (trade.pnl, trade.pnlcomm)
#             )

#     def notify_cashvalue(self, cash, value):
#         # Update cash and value every period
#         if self.periodic_logging:
#             self.log("Cash %s Value %s" % (cash, value))
#         self.cash = cash
#         self.value = value

#     def stop(self):
#         # Saving to self so it's accessible later during optimization
#         self.final_value = self.broker.getvalue()
#         self.pnl = round(self.final_value - self.init_cash, 2)
#         print("Final Portfolio Value: {}".format(self.final_value))
#         print("Final PnL: {}".format(self.pnl))

#     def next(self):
#         if self.periodic_logging:
#             self.log("Close, %.2f" % self.dataclose[0])
#         if self.order:
#             return

#         # Skip the last observation since purchases are based on next day closing prices (no value for the last observation)
#         if len(self) + 1 >= self.len_data:
#             return

#         if self.periodic_logging:
#             self.log("CURRENT POSITION SIZE: {}".format(self.position.size))
#         # Only buy if there is enough cash for at least one stock
#         if self.cash >= self.dataclose[0]:
#             if self.buy_signal():

#                 if self.transaction_logging:
#                     self.log("BUY CREATE, %.2f" % self.dataclose[0])
#                 # Take a 10% long position every time it's a buy signal (or whatever is afforded by the current cash position)
#                 # "size" refers to the number of stocks to purchase
#                 # Afforded size is based on closing price for the current trading day
#                 # Margin is required for buy commission
#                 # Add allowance to commission per transaction (avoid margin)
#                 afforded_size = int(
#                     self.cash
#                     / (self.dataclose[0] * (1 + self.commission + 0.001))
#                 )
#                 buy_prop_size = int(afforded_size * self.buy_prop)
#                 # Buy based on the closing price of the next closing day
#                 if self.execution_type == "close":
#                     final_size = min(buy_prop_size, afforded_size)
#                     if self.transaction_logging:
#                         self.log("Cash: {}".format(self.cash))
#                         self.log("Price: {}".format(self.dataclose[0]))
#                         self.log("Buy prop size: {}".format(buy_prop_size))
#                         self.log("Afforded size: {}".format(afforded_size))
#                         self.log("Final size: {}".format(final_size))
#                     # Explicitly setting exectype=bt.Order.Close will make the next day's closing the reference price
#                     self.order = self.buy(size=final_size)
#                 # Buy based on the opening price of the next closing day (only works "open" data exists in the dataset)
#                 else:
#                     # Margin is required for buy commission
#                     afforded_size = int(
#                         self.cash
#                         / (self.dataopen[1] * (1 + self.commission + 0.001))
#                     )
#                     final_size = min(buy_prop_size, afforded_size)
#                     if self.transaction_logging:
#                         self.log("Buy prop size: {}".format(buy_prop_size))
#                         self.log("Afforded size: {}".format(afforded_size))
#                         self.log("Final size: {}".format(final_size))
#                     self.order = self.buy(size=final_size)

#         # Only sell if you hold least one unit of the stock (and sell only that stock, so no short selling)
#         stock_value = self.value - self.cash
#         if stock_value > 0:
#             if self.sell_signal():
#                 if self.transaction_logging:
#                     self.log("SELL CREATE, %.2f" % self.dataclose[1])
#                 # Sell a 5% sell position (or whatever is afforded by the current stock holding)
#                 # "size" refers to the number of stocks to purchase
#                 if self.execution_type == "close":
#                     if SELL_PROP == 1:
#                         self.order = self.sell(
#                             size=self.position.size, exectype=bt.Order.Close
#                         )
#                     else:
#                         # Sell based on the closing price of the next closing day
#                         self.order = self.sell(
#                             size=int(
#                                 (stock_value / (self.dataclose[1]))
#                                 * self.sell_prop
#                             ),
#                             exectype=bt.Order.Close,
#                         )
#                 else:
#                     # Sell based on the opening price of the next closing day (only works "open" data exists in the dataset)
#                     self.order = self.sell(
#                         size=int(
#                             (self.init_cash / self.dataopen[1])
#                             * self.sell_prop
#                         )
#                     )


# class RSIStrategy(BaseStrategy):
#     """
#     Relative Strength Index (RSI) trading strategy

#     Parameters
#     ----------
#     rsi_period : int
#         Period used as basis in computing RSI
#     rsi_upper : int
#         The RSI upper limit, above which the assess is considered "overbought" and is sold
#     rsi_lower : int
#         The RSI lower limit, below which the assess is considered "oversold" and is bought
#     """

#     params = (("rsi_period", 14), ("rsi_upper", 70), ("rsi_lower", 30))

#     def __init__(self):

#         # Initialize global variables
#         super().__init__()
#         # Strategy level variables
#         self.rsi_period = self.params.rsi_period
#         self.rsi_upper = self.params.rsi_upper
#         self.rsi_lower = self.params.rsi_lower
#         print("===Strategy level arguments===")
#         print("rsi_period :", self.rsi_period)
#         print("rsi_upper :", self.rsi_upper)
#         print("rsi_lower :", self.rsi_lower)
#         self.rsi = bt.indicators.RelativeStrengthIndex(period=self.rsi_period)

#     def buy_signal(self):
#         return self.rsi[0] < self.rsi_lower

#     def sell_signal(self):
#         return self.rsi[0] > self.rsi_upper


# class SMACStrategy(BaseStrategy):
#     """
#     Simple moving average crossover strategy

#     Parameters
#     ----------
#     fast_period : int
#         The period used for the fast moving average line (should be smaller than `slow_upper`)
#     slow_period : int
#         The period used for the slow moving average line (should be larger than `fast_upper`)

#     """

#     params = (
#         ("fast_period", 10),  # period for the fast moving average
#         ("slow_period", 30),
#     )

#     def __init__(self):
#         # Initialize global variables
#         super().__init__()
#         # Strategy level variables
#         self.fast_period = self.params.fast_period
#         self.slow_period = self.params.slow_period

#         print("===Strategy level arguments===")
#         print("fast_period :", self.fast_period)
#         print("slow_period :", self.slow_period)
#         sma_fast = bt.ind.SMA(period=self.fast_period)  # fast moving average
#         sma_slow = bt.ind.SMA(period=self.slow_period)  # slow moving average
#         self.crossover = bt.ind.CrossOver(
#             sma_fast, sma_slow
#         )  # crossover signal

#     def buy_signal(self):
#         return self.crossover > 0

#     def sell_signal(self):
#         return self.crossover < 0


# class EMACStrategy(BaseStrategy):
#     """
#     Exponential moving average crossover strategy

#     Parameters
#     ----------
#     fast_period : int
#         The period used for the fast exponential moving average line (should be smaller than `slow_upper`)
#     slow_period : int
#         The period used for the slow exponential moving average line (should be larger than `fast_upper`)

#     """

#     params = (
#         ("fast_period", 10),  # period for the fast moving average
#         ("slow_period", 30),
#     )

#     def __init__(self):
#         # Initialize global variables
#         super().__init__()
#         # Strategy level variables
#         self.fast_period = self.params.fast_period
#         self.slow_period = self.params.slow_period

#         print("===Strategy level arguments===")
#         print("fast_period :", self.fast_period)
#         print("slow_period :", self.slow_period)
#         ema_fast = bt.ind.EMA(period=self.fast_period)  # fast moving average
#         ema_slow = bt.ind.EMA(period=self.slow_period)  # slow moving average
#         self.crossover = bt.ind.CrossOver(
#             ema_fast, ema_slow
#         )  # crossover signal

#     def buy_signal(self):
#         return self.crossover > 0

#     def sell_signal(self):
#         return self.crossover < 0


# class MACDStrategy(BaseStrategy):
#     """
#     Moving Average Convergence Divergence (MACD) strategy
#     Simple implementation of backtrader MACD reference: https://www.backtrader.com/blog/posts/2016-07-30-macd-settings/macd-settings/

#     Summary:
#     Enter if the macd line crosses the signal line to the upside and a control Simple Moving Average has had a
#     net negative direction in the last x periods (current SMA value below the value x periods ago).
#     In the opposite situation, given a market position exists, a sell position is made.

#     Parameters
#     ----------
#     fast_period : int
#         The period used for the fast exponential moving average line (should be smaller than `slow_upper`)
#     slow_period : int
#         The period used for the slow exponential moving average line (should be larger than `fast_upper`)
#     signal_period : int
#         The period used for the signal line for MACD
#     allowance : float
#         Proportion of macd to be exceeded by the excess macd to consitute a buy or sell signal
#     """

#     params = (
#         ("fast_period", 12),  # period for the fast moving average
#         ("slow_period", 26),
#         ("signal_period", 9),
#         ("sma_period", 30),
#         ("dir_period", 10),
#     )

#     def __init__(self):
#         # Initialize global variables
#         super().__init__()
#         # Strategy level variables
#         self.fast_period = self.params.fast_period
#         self.slow_period = self.params.slow_period
#         self.signal_period = self.params.signal_period
#         self.sma_period = self.params.sma_period
#         self.dir_period = self.params.dir_period

#         print("===Strategy level arguments===")
#         print("fast_period :", self.fast_period)
#         print("slow_period :", self.slow_period)
#         print("signal_period :", self.signal_period)
#         print("sma_period :", self.sma_period)
#         print("dir_period :", self.dir_period)
#         macd_ind = bt.ind.MACD(
#             period_me1=self.fast_period,
#             period_me2=self.slow_period,
#             period_signal=self.signal_period,
#         )
#         self.macd = macd_ind.macd
#         self.signal = macd_ind.signal
#         self.crossover = bt.ind.CrossOver(
#             self.macd, self.signal
#         )  # crossover buy signal

#         # Control market trend
#         self.sma = bt.indicators.SMA(period=self.sma_period)
#         self.smadir = self.sma - self.sma(-self.dir_period)

#     def buy_signal(self):
#         return self.crossover > 0 and self.smadir < 0.0

#     def sell_signal(self):
#         return self.crossover < 0 and self.smadir > 0.0


# class BBandsStrategy(BaseStrategy):
#     """
#     Bollinger Bands strategy
#     Simple implementation of backtrader BBands strategy reference: https://community.backtrader.com/topic/122/bband-strategy/2

#     Parameters
#     ----------
#     period : int
#         Period used as basis in calculating the moving average and standard deviation
#     devfactor : int
#         The number of standard deviations from the moving average to derive the upper and lower bands

#     TODO: Study this strategy closer based on the above reference. Current implementation is naive.
#     """

#     params = (
#         ("period", 20),  # period for the fast moving average
#         ("devfactor", 2.0),
#     )

#     def __init__(self):
#         # Initialize global variables
#         super().__init__()
#         # Strategy level variables
#         self.period = self.params.period
#         self.devfactor = self.params.devfactor

#         print("===Strategy level arguments===")
#         print("period :", self.period)
#         print("devfactor :", self.devfactor)
#         bbands = bt.ind.BBands(period=self.period, devfactor=self.devfactor)
#         self.mid = bbands.mid
#         self.top = bbands.top
#         self.bot = bbands.bot

#     def buy_signal(self):
#         return self.dataclose[0] < self.bot

#     def sell_signal(self):
#         return self.dataclose[0] > self.top


# class BuyAndHoldStrategy(BaseStrategy):
#     """
#     Buy and Hold Strategy
#     """

#     def _init_(self):
#         # Initialize global variables
#         super().__init__()
#         # Strategy level variables
#         self.buy_and_hold = None
#         self.buy_and_hold_sell = None

#     def buy_signal(self):
#         if not self.position:
#             self.buy_and_hold = True
#         return self.buy_and_hold

#     def sell_signal(self):
#         if (len(self) + 2) >= self.len_data:
#             self.buy_and_hold_sell = True
#         else:
#             self.buy_and_hold_sell = False
#         return self.buy_and_hold_sell


# class SentimentStrategy(BaseStrategy):
#     """
#     SentimentStrategy
#     Implementation of sentiment strategy using nltk/textblob pre-built sentiment models

#     Parameters
#     ----------
#     senti : float
#         The sentiment score threshold to indicate when to buy/sell

#     TODO: Textblob implementation for Sentiment indicator

#     """

#     params = (("senti", 0.2),)

#     def __init__(self):
#         # Initialize global variables
#         super().__init__()
#         # Strategy level variables
#         self.senti = self.params.senti
#         print("===Strategy level arguments===")
#         print("sentiment threshold :", self.senti)
#         self.datasentiment = Sentiment(self.data)

#     def buy_signal(self):
#         return self.datasentiment[0] >= self.senti

#     def sell_signal(self):
#         return self.datasentiment[0] <= self.senti


# STRATEGY_MAPPING = {
#     "rsi": RSIStrategy,
#     "smac": SMACStrategy,
#     "base": BaseStrategy,
#     "macd": MACDStrategy,
#     "emac": EMACStrategy,
#     "bbands": BBandsStrategy,
#     "buynhold": BuyAndHoldStrategy,
#     "sentiment": SentimentStrategy,
# }

# strat_docs = "\nExisting strategies:\n\n" + "\n".join(
#     [key + "\n" + value.__doc__ for key, value in STRATEGY_MAPPING.items()]
# )


# class SentimentDF(bt.feeds.PandasData):
#     # Add a 'sentiment_score' line to the inherited ones from the base class
#     lines = ("sentiment_score",)

#     # automatically handle parameter with -1
#     # add the parameter to the parameters inherited from the base class
#     params = (("sentiment_score", -1),)


# @docstring_parameter(strat_docs)
# def backtest(
#     strategy,
#     data,  # Treated as csv path is str, and dataframe of pd.DataFrame
#     commission=COMMISSION_PER_TRANSACTION,
#     init_cash=INIT_CASH,
#     data_format="c",
#     plot=True,
#     verbose=True,
#     sort_by="rnorm",
#     sentiments=None,
#     strats=None,  # Only used when strategy = "multi"
#     **kwargs
# ):
#     """
#     Backtest financial data with a specified trading strategy

#     {0}
#     """

#     # Setting inital support for 1 cpu
#     # Return the full strategy object to get all run information
#     cerebro = bt.Cerebro(stdstats=False, maxcpus=1, optreturn=False)
#     cerebro.addobserver(bt.observers.Broker)
#     cerebro.addobserver(bt.observers.Trades)
#     cerebro.addobserver(bt.observers.BuySell)

#     # Convert all non iterables and strings into lists
#     kwargs = {
#         k: v if isinstance(v, Iterable) and not isinstance(v, str) else [v]
#         for k, v in kwargs.items()
#     }

#     strat_names = []
#     if strategy == "multi" and strats is not None:
#         for strat, params in strats.items():
#             cerebro.optstrategy(
#                 STRATEGY_MAPPING[strat],
#                 init_cash=[init_cash],
#                 transaction_logging=[verbose],
#                 commission=commission,
#                 **params
#             )
#             strat_names.append(strat)
#     else:
#         cerebro.optstrategy(
#             STRATEGY_MAPPING[strategy],
#             init_cash=[init_cash],
#             transaction_logging=[verbose],
#             commission=commission,
#             **kwargs
#         )
#         strat_names.append(STRATEGY_MAPPING[strategy])

#     # Apply Total, Average, Compound and Annualized Returns calculated using a logarithmic approach
#     cerebro.addanalyzer(btanalyzers.Returns, _name="returns")
#     cerebro.addanalyzer(btanalyzers.SharpeRatio, _name="mysharpe")

#     cerebro.broker.setcommission(commission=commission)

#     # Treat `data` as a path if it's a string; otherwise, it's treated as a pandas dataframe
#     if isinstance(data, str):
#         if verbose:
#             print("Reading path as pandas dataframe ...")
#         data = pd.read_csv(data, header=0, parse_dates=["dt"])

#     # extend the dataframe with sentiment score
#     if strategy == "sentiment":
#         # initialize series for sentiments
#         senti_series = pd.Series(
#             sentiments, name="sentiment_score", dtype=float
#         )

#         # join and reset the index for dt to become the first column
#         data = data.merge(
#             senti_series, left_index=True, right_index=True, how="left"
#         )
#         data = data.reset_index()

#         # create PandasData using SentimentDF
#         pd_data = SentimentDF(
#             dataname=data, **DATA_FORMAT_MAPPING[data_format]
#         )

#     else:
#         # If data has `dt` as the index, set `dt` as the first column
#         # This means `backtest` supports the dataframe whether `dt` is the index or a column
#         if data.index.name == "dt":
#             data = data.reset_index()
#         pd_data = bt.feeds.PandasData(
#             dataname=data, **DATA_FORMAT_MAPPING[data_format]
#         )

#     cerebro.adddata(pd_data)
#     cerebro.broker.setcash(init_cash)
#     # Allows us to set buy price based on next day closing
#     # (technically impossible, but reasonable assuming you use all your money to buy market at the end of the next day)
#     cerebro.broker.set_coc(True)
#     if verbose:
#         print("Starting Portfolio Value: %.2f" % cerebro.broker.getvalue())

#     # clock the start of the process
#     tstart = time.time()
#     stratruns = cerebro.run()

#     # clock the end of the process
#     tend = time.time()

#     params = []
#     metrics = []
#     if verbose:
#         print("==================================================")
#         print("Number of strat runs:", len(stratruns))
#         print("Number of strats per run:", len(stratruns[0]))
#         print("Strat names:", strat_names)
#     for stratrun in stratruns:
#         strats_params = {}

#         if verbose:
#             print("**************************************************")
#         for i, strat in enumerate(stratrun):
#             p_raw = strat.p._getkwargs()
#             p = {}
#             for k, v in p_raw.items():
#                 if k not in ["periodic_logging", "transaction_logging"]:
#                     # Make sure the parameters are mapped to the corresponding strategy
#                     if strategy == "multi":
#                         key = (
#                             "{}.{}".format(strat_names[i], k)
#                             if k not in GLOBAL_PARAMS
#                             else k
#                         )
#                     else:
#                         key = k
#                     p[key] = v

#             strats_params = {**strats_params, **p}

#         # We run metrics on the last strat since all the metrics will be the same for all strats
#         returns = strat.analyzers.returns.get_analysis()
#         sharpe = strat.analyzers.mysharpe.get_analysis()
#         # Combine dicts for returns and sharpe
#         m = {
#             **returns,
#             **sharpe,
#             "pnl": strat.pnl,
#             "final_value": strat.final_value,
#         }

#         params.append(strats_params)
#         metrics.append(m)
#         if verbose:
#             print("--------------------------------------------------")
#             print(strats_params)
#             print(returns)
#             print(sharpe)

#     params_df = pd.DataFrame(params)
#     metrics_df = pd.DataFrame(metrics)

#     # Get indices based on `sort_by` metric
#     optim_idxs = np.argsort(metrics_df[sort_by].values)[::-1]
#     sorted_params_df = params_df.iloc[optim_idxs].reset_index(drop=True)
#     sorted_metrics_df = metrics_df.iloc[optim_idxs].reset_index(drop=True)
#     sorted_combined_df = pd.concat(
#         [sorted_params_df, sorted_metrics_df], axis=1
#     )

#     # print out the result
#     print("Time used (seconds):", str(tend - tstart))

#     # Save optimal parameters as dictionary
#     optim_params = sorted_params_df.iloc[0].to_dict()
#     optim_metrics = sorted_metrics_df.iloc[0].to_dict()
#     print("Optimal parameters:", optim_params)
#     print("Optimal metrics:", optim_metrics)

#     if plot and strategy != "multi":
#         has_volume = DATA_FORMAT_MAPPING[data_format]["volume"] is not None
#         # Plot only with the optimal parameters when multiple strategy runs are required
#         if params_df.shape[0] == 1:
#             # This handles the Colab Plotting
#             # Simple Check if we are in Colab
#             try:
#                 from google.colab import drive

#                 iplot = False

#             except Exception:
#                 iplot = True
#             cerebro.plot(volume=has_volume, figsize=(30, 15), iplot=iplot)
#         else:
#             print("=============================================")
#             print("Plotting backtest for optimal parameters ...")
#             backtest(
#                 strategy,
#                 data,  # Treated as csv path is str, and dataframe of pd.DataFrame
#                 commission=commission,
#                 data_format=data_format,
#                 plot=plot,
#                 verbose=verbose,
#                 sort_by=sort_by,
#                 **optim_params
#             )

#     return sorted_combined_df
