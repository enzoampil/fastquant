from __future__ import absolute_import, division, print_function, unicode_literals

import datetime
import os.path
import sys
import backtrader as bt
import backtrader.feeds as btfeed
import pandas as pd

# Global arguments
INIT_CASH = 100000
COMMISSION_PER_TRANSACTION = 0.0075
DATA_FILE = "examples/data/JFC_20180101_20190110_DCV.csv"
BUY_PROP = 1
SELL_PROP = 1
DATA_FORMAT_MAPPING = {
    "dcv": {
        "datetime": 0,
        "open": None,
        "high": None,
        "low": None,
        "close": 1,
        "volume": 2,
        "openinterest": None,
    }
}


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
        (
            "execution_type",
            "close",
        ),  # Either open or close, to indicate if a purchase is executed based on the next open or close
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
        print("===Global level arguments===")
        print("init_cash :", self.init_cash)
        print("buy_prop :", self.buy_prop)
        print("sell_prop :", self.sell_prop)

        # Strategy level arguments
        print("===Strategy level arguments===")

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
                self.log(
                    "BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f"
                    % (order.executed.price, order.executed.value, order.executed.comm)
                )

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log(
                    "SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f"
                    % (order.executed.price, order.executed.value, order.executed.comm)
                )

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("Order Canceled/Margin/Rejected")
            print("Canceled:", order.status == order.Canceled)
            print("Margin:", order.status == order.Margin)
            print("Rejected:", order.status == order.Rejected)

        # Write down: no pending order
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log("OPERATION PROFIT, GROSS %.2f, NET %.2f" % (trade.pnl, trade.pnlcomm))

    def notify_cashvalue(self, cash, value):
        # Update cash and value every period
        self.log("Cash %s Value %s" % (cash, value))
        self.cash = cash
        self.value = value

    def next(self):
        self.log("Close, %.2f" % self.dataclose[0])
        if self.order:
            return

        # Skip the last observation since purchases are based on next day closing prices (no value for the last observation)
        if len(self) + 1 >= self.len_data:
            return

        print("CURRENT POSITION SIZE:", self.position.size)
        # Only buy if there is enough cash for at least one stock
        if self.cash >= self.dataclose[1]:
            if self.buy_signal():

                self.log("BUY CREATE, %.2f" % self.dataclose[1])
                # Take a 10% long position every time it's a buy signal (or whatever is afforded by the current cash position)
                # "size" refers to the number of stocks to purchase
                # Afforded size is based on closing price for the next trading day
                print("cash:", self.cash)
                # Margin is required for both the buy and sell commission (which is why we multiply commission by 2)
                afforded_size = int(
                    self.cash
                    / (self.dataclose[1] * (1 + COMMISSION_PER_TRANSACTION * 2))
                )
                buy_prop_size = int(afforded_size * self.buy_prop)
                # Buy based on the closing price of the next closing day
                if self.execution_type == "close":
                    final_size = min(buy_prop_size, afforded_size,)
                    print("Buy prop size:", buy_prop_size)
                    print("Afforded size:", afforded_size)
                    print("Final size:", final_size)
                    self.order = self.buy(size=final_size, exectype=bt.Order.Close,)
                # Buy based on the opening price of the next closing day (only works "open" data exists in the dataset)
                else:
                    # Margin is required for both the buy and sell commission (which is why we multiply commission by 2)
                    afforded_size = int(
                        self.cash / (self.dataopen[1] * COMMISSION_PER_TRANSACTION * 2)
                    )
                    final_size = min(buy_prop_size, afforded_size,)
                    print("Buy prop size:", buy_prop_size)
                    print("Afforded size:", afforded_size)
                    print("Final size:", final_size)
                    self.order = self.buy(size=final_size,)

        # Only sell if you hold least one unit of the stock (and sell only that stock, so no short selling)
        stock_value = self.value - self.cash
        if stock_value > 0:
            if self.sell_signal():
                self.log("SELL CREATE, %.2f" % self.dataclose[1])
                # Sell a 5% sell position (or whatever is afforded by the current stock holding)
                # "size" refers to the number of stocks to purchase
                if self.execution_type == "close":
                    if SELL_PROP == 1:
                        self.order = self.sell(
                            size=self.position.size, exectype=bt.Order.Close,
                        )
                    else:
                        # Sell based on the closing price of the next closing day
                        self.order = self.sell(
                            size=int(
                                (stock_value / (self.dataclose[1])) * self.sell_prop
                            ),
                            exectype=bt.Order.Close,
                        )
                else:
                    # Sell based on the opening price of the next closing day (only works "open" data exists in the dataset)
                    self.order = self.sell(
                        size=int((self.init_cash / self.dataopen[1]) * self.sell_prop),
                    )


class RSIStrategy(BaseStrategy):
    params = (
        ("rsi_period", 14),
        ("rsi_upper", 70),
        ("rsi_lower", 30),
    )

    def __init__(self):
        # Initialize global variables
        super().__init__()
        # Strategy level variables
        self.rsi_period = self.params.rsi_period
        self.rsi_upper = self.params.rsi_upper
        self.rsi_lower = self.params.rsi_lower
        print("===Strategy level arguments===")
        print("rsi_period :", self.rsi_period)
        print("rsi_upper :", self.rsi_upper)
        print("rsi_lower :", self.rsi_lower)
        self.rsi = bt.indicators.RelativeStrengthIndex(period=self.rsi_period)

    def buy_signal(self):
        return self.rsi[0] < self.rsi_lower

    def sell_signal(self):
        return self.rsi[0] > self.rsi_upper


class SMACStrategy(BaseStrategy):
    params = (
        ("fast_period", 10),  # period for the fast moving average
        ("slow_period", 30),
    )

    def __init__(self):
        # Initialize global variables
        super().__init__()
        # Strategy level variables
        self.fast_period = self.params.fast_period
        self.slow_period = self.params.slow_period

        print("===Strategy level arguments===")
        print("fast_period :", self.fast_period)
        print("slow_period :", self.slow_period)
        sma_fast = bt.ind.SMA(period=self.fast_period)  # fast moving average
        sma_slow = bt.ind.SMA(period=self.slow_period)  # slow moving average
        self.crossover = bt.ind.CrossOver(sma_fast, sma_slow)  # crossover signal

    def buy_signal(self):
        return self.crossover > 0

    def sell_signal(self):
        return self.crossover < 0


STRATEGY_MAPPING = {"rsi": RSIStrategy, "smac": SMACStrategy, "base": BaseStrategy}


def backtest(
    strategy,
    data,  # Treated as csv path is str, and dataframe of pd.DataFrame
    commission=COMMISSION_PER_TRANSACTION,
    init_cash=INIT_CASH,
    data_format="dcv",
    plot=True,
    **kwargs
):
    cerebro = bt.Cerebro(stdstats=False)
    cerebro.addobserver(bt.observers.Broker)
    cerebro.addobserver(bt.observers.Trades)
    cerebro.addobserver(bt.observers.BuySell)
    cerebro.addstrategy(STRATEGY_MAPPING[strategy], init_cash=init_cash, **kwargs)
    cerebro.broker.setcommission(commission=commission)

    # Treat `data` as a path if it's a string; otherwise, it's treated as a pandas dataframe
    if isinstance(data, str):
        print("Reading path as pandas dataframe ...")
        data = pd.read_csv(data, header=0, parse_dates=["dt"])

    pd_data = bt.feeds.PandasData(dataname=data, **DATA_FORMAT_MAPPING[data_format])

    cerebro.adddata(pd_data)
    cerebro.broker.setcash(init_cash)
    print("Starting Portfolio Value: %.2f" % cerebro.broker.getvalue())
    cerebro.run()
    print("Final Portfolio Value: %.2f" % cerebro.broker.getvalue())
    if plot:
        cerebro.plot(figsize=(30, 15))


if __name__ == "__main__":
    print("Testing RSI strategy with csv ...")
    backtest("rsi", DATA_FILE, plot=False)
    print("Testing RSI strategy with dataframe ...")
    data = pd.read_csv(DATA_FILE, header=0, parse_dates=["dt"])
    backtest("rsi", data, plot=False)

    print("Testing SMAC strategy with dataframe ...")
    data = pd.read_csv(DATA_FILE, header=0, parse_dates=["dt"])
    backtest("smac", data, plot=False)

    print("Testing Base strategy with dataframe ...")
    data = pd.read_csv(DATA_FILE, header=0, parse_dates=["dt"])
    backtest("base", data, plot=False)
