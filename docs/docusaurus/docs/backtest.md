---
id: backtest
title: backtest
---

## Description

Backtest financial data with a specified trading strategy
    
## Parameters

**strategy** : str or an instance of `fastquant.strategies.base.BaseStrategy`
    see list of accepted strategy keys below

**data** : pandas.DataFrame
    dataframe with at least close price indexed with time

**commission** : float
    commission per transaction [0, 1]

**init_cash** : float
    initial cash (currency implied from `data`)

**plot** : bool
    show plot backtrader (disabled if `strategy`=="multi")

**verbose** : int
    Verbose can take values: [0, 1, 2, 3], with increasing levels of verbosity (default=1).

**sort_by** : str
    sort result by given metric (default='rnorm')

**sentiments** : pandas.DataFrame
    df of sentiment [0, 1] indexed by time (applicable if `strategy`=='senti')

**strats** : dict
    dictionary of strategy parameters (applicable if `strategy`=='multi')

**return_history** : bool
    return history of transactions (i.e. buy and sell timestamps) (default=False)

**channel** : str
    Channel to be used for notifications - e.g. "slack" (default=None)

**symbol** : str
    Symbol to be referenced in the channel notification if not None (default=None)

**allow_short** : bool
    Whether to allow short selling, with max set as `short_max` times the portfolio value (default=False)

**short_max** : float
    The maximum short position allowable as a ratio relative to the portfolio value at that timepoint(default=1.5)

**figsize** : tuple
    The size of the figure to be displayed at the end of the backtest (default=(30, 15))

**data_class** : bt.feed.DataBase
    Custom backtrader database to be used as a parent class instead bt.feed. (default=None)

**data_kwargs** : dict
    Datafeed keyword arguments (empty dict by default)

## Returns

A plot containing the backtest results and a dictionary of the history and results of the backtest run. 