
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime
import os.path
import sys
import backtrader as bt
import backtrader.feeds as btfeed

# Global arguments
INIT_CASH = 100000
COMMISSION_PER_TRANSACTION = 0.006
BUY_PROP = 0.1
SELL_PROP = 0.1
DATA_FILE = 'data/JFC_2010-01-01_2019-01-01_OHLCV.csv'

# Strategy level arguments
RSI_PERIOD = 14
RSI_UPPER = 70
RSI_LOWER = 30

class RSIStrategy(bt.Strategy):
    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Global variables
        self.init_cash = INIT_CASH
        self.commission_per_transaction = COMMISSION_PER_TRANSACTION
        self.buy_prop = BUY_PROP
        self.sell_prop = SELL_PROP
        #
        self.dataclose = self.datas[0].close
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.rsi = bt.indicators.RelativeStrengthIndex(period=RSI_PERIOD)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))
        
    def notify_cashvalue(self, cash, value):
        # Update cash and value every period
        self.log('Cash %s Value %s' % (cash, value))
        self.cash = cash
        self.value = value

    def next(self):
        self.log('Close, %.2f' % self.dataclose[0])
        print('rsi:', self.rsi[0])
        if self.order:
            return

        # Only buy if there is enough cash for at least one stock
        if self.cash >= self.dataclose[0]:
            if (self.rsi[0] < RSI_LOWER):
                self.log('BUY CREATE, %.2f' % self.dataclose[0])
                # Take a 10% long position every time it's a buy signal (or whatever is afforder by the current cash position)
                # "size" refers to the number of stocks to purchase
                self.order = self.buy(size=int(min((INIT_CASH / self.dataclose[0]) * BUY_PROP, self.cash / self.dataclose[0])))

        # Only sell if you hold least one unit of the stock (and sell only that stock, so no short selling)
        if (self.value - self.cash) > 0:
            if (self.rsi[0] > RSI_UPPER):
                self.log('SELL CREATE, %.2f' % self.dataclose[0])
                # Sell a 5% sell position (or whatever is afforded by the current stock holding)
                # "size" refers to the number of stocks to purchase
                self.order = self.sell(size=int((INIT_CASH / self.dataclose[0]) * SELL_PROP))

def backtest(strategy, csv):
    cerebro = bt.Cerebro()
    cerebro.addstrategy(RSIStrategy)
    cerebro.broker.setcommission(commission=COMMISSION_PER_TRANSACTION)

    data = btfeed.GenericCSVData(
        dataname=csv,

        fromdate=datetime.datetime(2017, 1, 1),
        todate=datetime.datetime(2019, 1, 1),

        nullvalue=0.0,

        dtformat=('%Y-%m-%d'),

        datetime=0,
        open=1,
        high=2,
        low=3,
        close=4,
        volume=5,
        openinterest=-1
    )
    cerebro.adddata(data)
    cerebro.broker.setcash(INIT_CASH)
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    cerebro.run()
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    cerebro.plot(figsize=(30, 15))
