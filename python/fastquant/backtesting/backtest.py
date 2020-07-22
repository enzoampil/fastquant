#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Import standard library
from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

# Import modules
import backtrader as bt
import backtrader.feeds as btfeed
import backtrader.analyzers as btanalyzers
import pandas as pd
import numpy as np
from collections.abc import Iterable
import time
from fastquant.backtesting.default_values import (
    INIT_CASH,
    BUY_PROP,
    SELL_PROP,
    COMMISSION_PER_TRANSACTION,
)
from fastquant.strategies.base import strat_docs, STRATEGY_MAPPING

DATA_FORMAT_MAPPING = {
    "cv": {
        "datetime": 0,
        "open": None,
        "high": None,
        "low": None,
        "close": 1,
        "volume": 2,
        "openinterest": None,
    },
    "c": {
        "datetime": 0,
        "open": None,
        "high": None,
        "low": None,
        "close": 1,
        "volume": None,
        "openinterest": None,
    },
}
GLOBAL_PARAMS = ["init_cash", "buy_prop", "sell_prop", "execution_type"]


def docstring_parameter(*sub):
    def dec(obj):
        obj.__doc__ = obj.__doc__.format(*sub)
        return obj

    return dec


class SentimentDF(bt.feeds.PandasData):
    # Add a 'sentiment_score' line to the inherited ones from the base class
    lines = ("sentiment_score",)

    # automatically handle parameter with -1
    # add the parameter to the parameters inherited from the base class
    params = (("sentiment_score", -1),)


@docstring_parameter(strat_docs)
def backtest(
    strategy,
    data,  # Treated as csv path is str, and dataframe of pd.DataFrame
    commission=COMMISSION_PER_TRANSACTION,
    init_cash=INIT_CASH,
    data_format="c",
    plot=True,
    verbose=True,
    sort_by="rnorm",
    sentiments=None,
    strats=None,  # Only used when strategy = "multi"
    **kwargs
):
    """
    Backtest financial data with a specified trading strategy

    {0}
    """

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

    strat_names = []
    if strategy == "multi" and strats is not None:
        for strat, params in strats.items():
            cerebro.optstrategy(
                STRATEGY_MAPPING[strat],
                init_cash=[init_cash],
                transaction_logging=[verbose],
                **params
            )
            strat_names.append(strat)
    else:
        cerebro.optstrategy(
            STRATEGY_MAPPING[strategy],
            init_cash=[init_cash],
            transaction_logging=[verbose],
            **kwargs
        )
        strat_names.append(STRATEGY_MAPPING[strategy])

    # Apply Total, Average, Compound and Annualized Returns calculated using a logarithmic approach
    cerebro.addanalyzer(btanalyzers.Returns, _name="returns")
    cerebro.addanalyzer(btanalyzers.SharpeRatio, _name="mysharpe")

    cerebro.broker.setcommission(commission=commission)

    # Treat `data` as a path if it's a string; otherwise, it's treated as a pandas dataframe
    if isinstance(data, str):
        if verbose:
            print("Reading path as pandas dataframe ...")
        data = pd.read_csv(data, header=0, parse_dates=["dt"])

    # extend the dataframe with sentiment score
    if strategy == "sentiment":
        # initialize series for sentiments
        senti_series = pd.Series(sentiments, name="sentiment_score", dtype=float)

        # join and reset the index for dt to become the first column
        data = data.merge(senti_series, left_index=True, right_index=True, how="left")
        data = data.reset_index()

        # create PandasData using SentimentDF
        pd_data = SentimentDF(dataname=data, **DATA_FORMAT_MAPPING[data_format])

    else:
        # If data has `dt` as the index, set `dt` as the first column
        # This means `backtest` supports the dataframe whether `dt` is the index or a column
        if data.index.name == "dt":
            data = data.reset_index()
        pd_data = bt.feeds.PandasData(dataname=data, **DATA_FORMAT_MAPPING[data_format])

    cerebro.adddata(pd_data)
    cerebro.broker.setcash(init_cash)
    # Allows us to set buy price based on next day closing
    # (technically impossible, but reasonable assuming you use all your money to buy market at the end of the next day)
    cerebro.broker.set_coc(True)
    if verbose:
        print("Starting Portfolio Value: %.2f" % cerebro.broker.getvalue())

    # clock the start of the process
    tstart = time.time()
    stratruns = cerebro.run()

    # clock the end of the process
    tend = time.time()

    params = []
    metrics = []
    if verbose:
        print("==================================================")
        print("Number of strat runs:", len(stratruns))
        print("Number of strats per run:", len(stratruns[0]))
        print("Strat names:", strat_names)
    for stratrun in stratruns:
        strats_params = {}

        if verbose:
            print("**************************************************")
        for i, strat in enumerate(stratrun):
            p_raw = strat.p._getkwargs()
            p = {}
            for k, v in p_raw.items():
                if k not in ["periodic_logging", "transaction_logging"]:
                    # Make sure the parameters are mapped to the corresponding strategy
                    if strategy == "multi":
                        key = (
                            "{}.{}".format(strat_names[i], k)
                            if k not in GLOBAL_PARAMS
                            else k
                        )
                    else:
                        key = k
                    p[key] = v

            strats_params = {**strats_params, **p}

        # We run metrics on the last strat since all the metrics will be the same for all strats
        returns = strat.analyzers.returns.get_analysis()
        sharpe = strat.analyzers.mysharpe.get_analysis()
        # Combine dicts for returns and sharpe
        m = {
            **returns,
            **sharpe,
            "pnl": strat.pnl,
            "final_value": strat.final_value,
        }

        params.append(strats_params)
        metrics.append(m)
        if verbose:
            print("--------------------------------------------------")
            print(strats_params)
            print(returns)
            print(sharpe)

    params_df = pd.DataFrame(params)
    metrics_df = pd.DataFrame(metrics)

    # Get indices based on `sort_by` metric
    optim_idxs = np.argsort(metrics_df[sort_by].values)[::-1]
    sorted_params_df = params_df.iloc[optim_idxs].reset_index(drop=True)
    sorted_metrics_df = metrics_df.iloc[optim_idxs].reset_index(drop=True)
    sorted_combined_df = pd.concat([sorted_params_df, sorted_metrics_df], axis=1)

    # print out the result
    print("Time used (seconds):", str(tend - tstart))

    # Save optimal parameters as dictionary
    optim_params = sorted_params_df.iloc[0].to_dict()
    optim_metrics = sorted_metrics_df.iloc[0].to_dict()
    print("Optimal parameters:", optim_params)
    print("Optimal metrics:", optim_metrics)

    if plot and strategy != "multi":
        has_volume = DATA_FORMAT_MAPPING[data_format]["volume"] is not None
        # Plot only with the optimal parameters when multiple strategy runs are required
        if params_df.shape[0] == 1:
            # This handles the Colab Plotting
            # Simple Check if we are in Colab
            try:
                from google.colab import drive

                iplot = False

            except Exception:
                iplot = True
            cerebro.plot(volume=has_volume, figsize=(30, 15), iplot=iplot)
        else:
            print("=============================================")
            print("Plotting backtest for optimal parameters ...")
            backtest(
                strategy,
                data,  # Treated as csv path is str, and dataframe of pd.DataFrame
                commission=commission,
                data_format=data_format,
                plot=plot,
                verbose=verbose,
                sort_by=sort_by,
                **optim_params
            )

    return sorted_combined_df
