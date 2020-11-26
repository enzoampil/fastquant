---
id: backtest
title: backtest
---

Backtest financial data with a specified trading strategy
    
## Parameters

strategy : str or an instance of `fastquant.strategies.base.BaseStrategy`
    see list of accepted strategy keys below

data : pandas.DataFrame
    dataframe with at least close price indexed with time

commission : float
    commission per transaction [0, 1]

init_cash : float
    initial cash (currency implied from `data`)

plot : bool
    show plot backtrader (disabled if `strategy`=="multi")

sort_by : str
    sort result by given metric (default='rnorm')

sentiments : pandas.DataFrame
    df of sentiment [0, 1] indexed by time (applicable if `strategy`=='senti')

strats : dict
    dictionary of strategy parameters (applicable if `strategy`=='multi')

return_history : bool
    return history of transactions (i.e. buy and sell timestamps) (default=False)

channel : str
    Channel to be used for last day notification - e.g. "slack" (default=None)

verbose : int
    Verbose can take values: [0, 1, 2, 3], with increasing levels of verbosity (default=1).
    
symbol : str
    Symbol to be referenced in the channel notification if not None (default=None)