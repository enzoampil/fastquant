#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Import standard library
from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)
import warnings

# Import modules
import backtrader as bt
import backtrader.feeds as btfeed
import backtrader.analyzers as btanalyzers
import pandas as pd
import numpy as np
from collections.abc import Iterable
import time
from pandas.api.types import is_numeric_dtype


# Import backtest variables
from fastquant.config import (
    INIT_CASH,
    COMMISSION_PER_TRANSACTION,
    GLOBAL_PARAMS,
    DEFAULT_PANDAS,
)
from fastquant.strategies.mappings import STRATEGY_MAPPING

# Other backtest components
from fastquant.backtest.data_prep import initalize_data
from fastquant.backtest.post_backtest import analyze_strategies, plot_results


strat_docs = "\nExisting strategies:\n\n" + "\n".join(
    [key + "\n" + value.__doc__ for key, value in STRATEGY_MAPPING.items()]
)


def docstring_parameter(*sub):
    def dec(obj):
        obj.__doc__ = obj.__doc__.format(*sub)
        return obj

    return dec


@docstring_parameter(strat_docs)
def backtest(
    strategy,
    data,  # Treated as csv path is str, and dataframe of pd.DataFrame
    commission=COMMISSION_PER_TRANSACTION,
    init_cash=INIT_CASH,
    plot=True,
    verbose=1,
    sort_by="rnorm",
    sentiments=None,
    strats=None,  # Only used when strategy = "multi"
    data_format=None,  # No longer needed but will leave for now to warn removal in a coming release
    return_history=False,
    channel=None,
    symbol=None,
    allow_short=False,
    short_max=1.5,
    figsize=(30, 15),
    data_class=None,
    data_kwargs={},
    **kwargs,
):
    """Backtest financial data with a specified trading strategy

    Parameters
    ----------------
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
    data_class : bt.feed.DataBase
        Custom backtrader database to be used as a parent class instead bt.feed. (default=None)
    data_kwargs : dict
        Data keyword arguments (empty dict by default)
    {0}
    """

    if data_format:
        errmsg = "Warning: data_format argument is no longer needed since formatting is now purely automated based on column names!"
        errmsg += "\nWe will be removing this argument in a coming release!"
        warnings.warn(errmsg, DeprecationWarning)
        print(errmsg)

    # Setting inital support for 1 cpu
    # Return the full strategy object to get all run information
    cerebro = bt.Cerebro(stdstats=False, maxcpus=1, optreturn=False)
    cerebro.addobserver(bt.observers.Broker)
    cerebro.addobserver(bt.observers.Trades)
    cerebro.addobserver(bt.observers.BuySell)

    # Convert all non iterables and strings into lists
    kwargs = {
        k: v if isinstance(v, Iterable) and not isinstance(v, str) else [v]
        for k, v in kwargs.items()
    }

    # Add logging parameters based on the `verbose` parameter
    logging_params = get_logging_params(verbose)
    kwargs.update(logging_params)

    # Add Strategy
    strat_names = []
    strat_name = None
    if strategy == "multi" and strats is not None:
        for strat, params in strats.items():
            cerebro.optstrategy(
                STRATEGY_MAPPING[strat],
                init_cash=[init_cash],
                commission=commission,
                channel=None,
                symbol=None,
                allow_short=allow_short,
                short_max=short_max,
                **params,
            )
            strat_names.append(strat)
    else:

        # Allow instance of BaseStrategy or from the predefined mapping
        if not isinstance(strategy, str) and issubclass(strategy, bt.Strategy):
            strat_name = (
                strategy.__name__
                if hasattr(strategy, "__name__")
                else str(strategy)
            )
        else:
            strat_name = strategy
            strategy = STRATEGY_MAPPING[strategy]

        cerebro.optstrategy(
            strategy,
            init_cash=[init_cash],
            commission=commission,
            channel=None,
            symbol=None,
            allow_short=allow_short,
            short_max=short_max,
            **kwargs,
        )
        strat_names.append(strat_name)

    # Apply Total, Average, Compound and Annualized Returns calculated using a logarithmic approach
    cerebro.addanalyzer(btanalyzers.Returns, _name="returns")
    cerebro.addanalyzer(btanalyzers.SharpeRatio, _name="mysharpe")
    cerebro.addanalyzer(btanalyzers.DrawDown, _name="drawdown")
    cerebro.addanalyzer(btanalyzers.TimeDrawDown, _name="timedraw")

    cerebro.broker.setcommission(commission=commission)

    # Initalize and verify data
    pd_data, data, data_format_dict = initalize_data(
        data, strat_name, symbol, data_class, sentiments, data_kwargs
    )
    cerebro.adddata(pd_data)
    cerebro.broker.setcash(init_cash)
    # Allows us to set buy price based on next day closing
    # (technically impossible, but reasonable assuming you use all your money to buy market at the end of the next day)
    cerebro.broker.set_coc(True)
    if verbose > 0:
        print("Starting Portfolio Value: %.2f" % cerebro.broker.getvalue())

    # clock the start of the process
    tstart = time.time()
    stratruns = cerebro.run()

    # clock the end of the process
    tend = time.time()

    if verbose > 0:
        # print out the result
        print("Time used (seconds):", str(tend - tstart))

    # Get History, Optimal Parameters and Strategy Metrics
    sorted_combined_df, optim_params, history_dict = analyze_strategies(
        stratruns,
        data,
        strat_names,
        strategy,
        strats,
        sort_by,
        return_history,
        verbose,
        **kwargs,
    )

    # Plot
    if plot and strategy != "multi":
        # Plot only with the optimal parameters when multiple strategy runs are required
        if sorted_combined_df.shape[0] != 1:
            if verbose > 0:
                print("=============================================")
                print("Plotting backtest for optimal parameters ...")
            backtest(
                strategy,
                data,
                plot=plot,
                verbose=0,
                sort_by=sort_by,
                **optim_params,
            )
        else:
            plot_results(cerebro, data_format_dict, figsize)

    if return_history:

        return sorted_combined_df, history_dict
    else:
        return sorted_combined_df


def get_logging_params(verbose):
    """
        Adjusts the logging verbosity based on the `verbose` parameter
        0 - No logging
        1 - Strategy Level logs
        2 - Transaction Level logs
        3 - Periodic Logs
    """
    verbosity_args = dict(
        strategy_logging=False,
        transaction_logging=False,
        periodic_logging=False,
    )
    if verbose > 0:
        verbosity_args["strategy_logging"] = True
    if verbose > 1:
        verbosity_args["transaction_logging"] = True
    if verbose > 2:
        verbosity_args["periodic_logging"] = True

    return verbosity_args
