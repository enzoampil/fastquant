from __future__ import absolute_import, division, print_function, unicode_literals

import datetime
import os.path
import sys
import backtrader as bt
import backtrader.feeds as btfeed

# Global arguments
INIT_CASH = 100000
COMMISSION_PER_TRANSACTION = 0.006
DATA_FILE = "examples/data/JFC_20180101_20190101.csv"
BUY_PROP = 0.1
SELL_PROP = 0.1
DATA_FORMAT_MAPPING = {
    "dcv": {
        "datetime": 0,
        "open": -1,
        "high": -1,
        "low": -1,
        "close": 1,
        "volume": 2,
        "openinterest": -1,
    }
}


class RSIStrategy(bt.Strategy):

    # Strategy level arguments
    # After initialization, the `params` variable becomes accessible as an attribute of the strategy object
    # with the properties of a `named tuple`
    params = (
        ("rsi_period", 14),
        ("rsi_upper", 70),
        ("rsi_lower", 30),
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
        self.rsi_period = self.params.rsi_period
        self.rsi_upper = self.params.rsi_upper
        self.rsi_lower = self.params.rsi_lower
        print("===Strategy level arguments===")
        print("rsi_period :", self.rsi_period)
        print("rsi_upper :", self.rsi_upper)
        print("rsi_lower :", self.rsi_lower)

        self.dataclose = self.datas[0].close
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.rsi = bt.indicators.RelativeStrengthIndex(period=self.rsi_period)

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
        print("rsi:", self.rsi[0])
        if self.order:
            return

        # Only buy if there is enough cash for at least one stock
        if self.cash >= self.dataclose[0]:
            if self.rsi[0] < self.rsi_lower:
                self.log("BUY CREATE, %.2f" % self.dataclose[0])
                # Take a 10% long position every time it's a buy signal (or whatever is afforded by the current cash position)
                # "size" refers to the number of stocks to purchase
                buy_prop_size = int(
                    (self.init_cash / self.dataclose[0]) * self.buy_prop
                )
                afforded_size = int(self.cash / self.dataclose[0])
                final_size = min(buy_prop_size, afforded_size,)
                print("Buy prop size:", buy_prop_size)
                print("Afforded size:", afforded_size)
                print("Final size:", final_size)
                # Buy based on the closing price of the next closing day
                if self.execution_type == "close":
                    self.order = self.buy(size=final_size, exectype=bt.Order.Close,)
                # Buy based on the opening price of the next closing day (only works "open" data exists in the dataset)
                else:
                    self.order = self.buy(size=final_size,)

        # Only sell if you hold least one unit of the stock (and sell only that stock, so no short selling)
        if (self.value - self.cash) > 0:
            if self.rsi[0] > self.rsi_upper:
                self.log("SELL CREATE, %.2f" % self.dataclose[0])
                # Sell a 5% sell position (or whatever is afforded by the current stock holding)
                # "size" refers to the number of stocks to purchase
                if self.execution_type == "close":
                    # Sell based on the closing price of the next closing day
                    self.order = self.sell(
                        size=int((self.init_cash / self.dataclose[0]) * self.sell_prop),
                        exectype=bt.Order.Close,
                    )
                else:
                    # Sell based on the opening price of the next closing day (only works "open" data exists in the dataset)
                    self.order = self.sell(
                        size=int((self.init_cash / self.dataclose[0]) * self.sell_prop),
                    )


STRATEGY_MAPPING = {"rsi": RSIStrategy}


def backtest(
    strategy,
    csv,
    commission=COMMISSION_PER_TRANSACTION,
    init_cash=INIT_CASH,
    data_format="dcv",
    **kwargs
):
    cerebro = bt.Cerebro(stdstats=False)
    cerebro.addobserver(bt.observers.Broker)
    cerebro.addobserver(bt.observers.Trades)
    cerebro.addobserver(bt.observers.BuySell)
    cerebro.addstrategy(STRATEGY_MAPPING[strategy], init_cash=init_cash, **kwargs)
    cerebro.broker.setcommission(commission=commission)

    data = btfeed.GenericCSVData(
        dataname=csv,
        # Date filters are note required
        # TODO: Add optional date filter arguments
        # fromdate=datetime.datetime(2017, 1, 1),
        # todate=datetime.datetime(2019, 1, 1),
        nullvalue=0.0,
        dtformat=("%Y-%m-%d"),
        **DATA_FORMAT_MAPPING[data_format]
    )
    cerebro.adddata(data)
    cerebro.broker.setcash(init_cash)
    print("Starting Portfolio Value: %.2f" % cerebro.broker.getvalue())
    cerebro.run()
    print("Final Portfolio Value: %.2f" % cerebro.broker.getvalue())
    cerebro.plot(figsize=(30, 15))


if __name__ == "__main__":
    print("Testing RSI strategy ...")
    backtest("rsi", DATA_FILE)
