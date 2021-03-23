# -*- coding: utf-8 -*-
import logging
import sys


class StrategyLogger:

    # """
    # Handles the logging throughout the strategy life-cycle. It is called within the BaseStrategy class
    # Responsible for the log messages

    # """

    def __init__(self, strategy):
        self.strategy = strategy
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
            "position_size": [],
            "cash": [],
        }
        self.trade_history = {"dt": [], "pnl": [], "pnl_comm": []}

        self.periodic_logging = strategy.periodic_logging
        self.transaction_logging = strategy.transaction_logging

        # Configure logging module
        logging.basicConfig(
            level=logging.INFO,  # Log everything above DEBUG level
            format="%(message)s",  # Use display only the message
            stream=sys.stdout,  # use output stream instead of the default error stream (could also be set to a file output)
        )

    def log(self, txt, dt=None, level=logging.INFO):
        try:
            dt = dt or self.strategy.datas[0].datetime.date(0)
            dt = dt.isoformat()
        except:
            dt = ""

        if level == logging.DEBUG:
            logging.debug("%s, %s" % (dt, txt))
        elif level == logging.INFO:
            logging.info("%s, %s" % (dt, txt))
        elif level == logging.WARNING:
            logging.warn("%s, %s" % (dt, txt))

    def strategy_argments(self):
        strategy = self.strategy
        self.log("===Global level arguments===")
        self.log("init_cash : {}".format(strategy.initial_cash))
        self.log("buy_prop : {}".format(strategy.buy_proportion))
        self.log("sell_prop : {}".format(strategy.sell_proportion))
        self.log("commission : {}".format(strategy.commission))
        self.log("stop_loss_percent : {}".format(strategy.stop_loss_percent))
        self.log("stop_trail_percent : {}".format(strategy.stop_trail_percent))

    def order_created(self, order_type_str, text):

        if self.transaction_logging:
            self.log("ORDER CREATED: %s, %s" % (order_type_str.upper(), text))

    def order_executed(self, order, action):
        if self.transaction_logging:
            self.log(
                "ORDER EXECUTED %s , Price: %.2f, Cost: %.2f, Comm: %.2f, Size: %.2f"
                % (
                    action.upper(),
                    order.executed.price,
                    order.executed.value,
                    order.executed.comm,
                    order.executed.size,
                )
            )

    def order_aborted(self, order):
        if self.transaction_logging:
            self.log("Order Canceled/Margin/Rejected")
            self.log("Canceled: {}".format(order.status == order.Canceled))
            self.log("Margin: {}".format(order.status == order.Margin))
            self.log("Rejected: {}".format(order.status == order.Rejected))
            self.log(
                "Cash %s Value %s" % (self.strategy.cash, self.strategy.value)
            )

    def trade_closed(self, trade):
        if self.transaction_logging:
            self.log(
                "TRADE CLOSED: OPERATION PROFIT, GROSS: %.2f, NET: %.2f"
                % (trade.pnl, trade.pnlcomm)
            )

    def cash_value(self):
        if self.periodic_logging:
            self.log(
                "Cash %.2f Value %.2f"
                % (self.strategy.cash, self.strategy.value)
            )

    def initialize_periodic_cash_in(self, start_date, next_cash_datetime):
        if self.transaction_logging:
            self.log("Start date: {}".format(start_date.strftime("%Y-%m-%d")))
            self.log(
                "Next cash date: {}".format(
                    next_cash_datetime.strftime("%Y-%m-%d")
                )
            )

    def periodic_cash_in(
        self, add_cash_amount, total_cash_added, next_cash_datetime
    ):
        if self.transaction_logging:
            self.log("Cash added: {}".format(add_cash_amount))
            self.log("Total cash added: {}".format(total_cash_added))
            self.log(
                "Next cash date: {}".format(
                    next_cash_datetime.strftime("%Y-%m-%d")
                )
            )

    def buy_signal(
        self,
        cash,
        market_price,
        buy_proportion_size,
        afforded_size,
        final_size,
    ):
        if self.transaction_logging:
            self.log("BUY SIGNAL GENERATED")
            self.log("Cash: {}".format(cash))
            self.log("Price: {}".format(market_price))
            self.log("Buy prop size: {}".format(buy_proportion_size))
            self.log("Afforded size: {}".format(afforded_size))
            self.log("Final size: {}".format(final_size))

    def sell_signal(self, size, price):
        if self.transaction_logging:
            self.log("SELL SIGNAL GENERATED")
            self.log("Sell Size: {}".format(size))
            self.log("Sell Price: {}".format(price))

    def update_order_history(self, order):
        self.order_history["dt"].append(
            self.strategy.datas[0].datetime.date(0)
        )
        self.order_history["type"].append("buy" if order.isbuy() else "sell")
        self.order_history["price"].append(order.executed.price)
        self.order_history["size"].append(order.executed.size)
        self.order_history["value"].append(order.executed.value)
        self.order_history["commission"].append(order.executed.comm)
        self.order_history["pnl"].append(order.executed.pnl)

    def update_periodic_history(self):
        self.periodic_history["dt"].append(
            self.strategy.datas[0].datetime.date(0)
        )
        self.periodic_history["portfolio_value"].append(
            self.strategy.broker.getvalue()
        )
        self.periodic_history["position_size"].append(
            self.strategy.position.size
        )
        self.periodic_history["cash"].append(self.strategy.broker.getcash())

    def update_trade_history(self, pnl, pnl_comm):
        self.trade_history["dt"].append(
            self.strategy.datas[0].datetime.date(0)
        )
        self.trade_history["pnl"].append(pnl)
        self.trade_history["pnl_comm"].append(pnl_comm)
