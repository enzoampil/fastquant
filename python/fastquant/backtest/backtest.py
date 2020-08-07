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

# Import modules
import backtrader as bt
import backtrader.feeds as btfeed
import backtrader.analyzers as btanalyzers
import pandas as pd
import numpy as np
from collections.abc import Iterable
import time

# Import from package
from fastquant.strategies.sentiment import SentimentDF
from fastquant.strategies import (
    RSIStrategy,
    SMACStrategy,
    BaseStrategy,
    MACDStrategy,
    EMACStrategy,
    BBandsStrategy,
    BuyAndHoldStrategy,
    SentimentStrategy,
)

# Import backtest variables
from fastquant.config import (
    INIT_CASH,
    COMMISSION_PER_TRANSACTION,
    DATA_FORMAT_MAPPING,
    # strat_docs,
    # STRATEGY_MAPPING,
    GLOBAL_PARAMS,
    DATA_FORMAT_BASE,
    DATA_FORMAT_COLS,
)


STRATEGY_MAPPING = {
    "rsi": RSIStrategy,
    "smac": SMACStrategy,
    "base": BaseStrategy,
    "macd": MACDStrategy,
    "emac": EMACStrategy,
    "bbands": BBandsStrategy,
    "buynhold": BuyAndHoldStrategy,
    "sentiment": SentimentStrategy,
}

strat_docs = "\nExisting strategies:\n\n" + "\n".join(
    [key + "\n" + value.__doc__ for key, value in STRATEGY_MAPPING.items()]
)


def docstring_parameter(*sub):
    def dec(obj):
        obj.__doc__ = obj.__doc__.format(*sub)
        return obj

    return dec


@docstring_parameter(", ".join(["dt"] + list(DATA_FORMAT_BASE.keys())))
def infer_data_format(data):
    """
    Infers the data format of the dataframe based on the indices of its matched column names

    The detectable column names are {0}
    """
    # Rename "dt" column to "datetime" to match the formal alias
    data = data.rename(columns={"dt": "datetime"})
    cols = data.columns.values.tolist()
    detectable_cols = list(DATA_FORMAT_BASE.keys())
    # Detected columns are those that are in both the dataframe and the list of detectable columns
    detected_cols = set(cols).intersection(detectable_cols)
    # Assertion error if no columns were detected
    assert detected_cols, "No columns were detected! Please have at least one of: {}".format(detectable_cols)
    # Set data format mapping
    data_format = {k: cols.index(k) if k in detected_cols else None for k, _ in DATA_FORMAT_BASE.items()}
    cols_to_alias = {v: k for k, v in DATA_FORMAT_COLS.items()}
    # Ignore "datetime" since it's assumed to be there when writing the alias
    data_format_alias = {cols_to_alias[k]: v for k, v in data_format.items() if k != "datetime"}
    data_format_str = "".join(pd.Series(data_format_alias).dropna().sort_values().index.values.tolist())
    print("Data format detected:", data_format_str)
    return data_format


@docstring_parameter(strat_docs)
def backtest(
    strategy,
    data,  # Treated as csv path is str, and dataframe of pd.DataFrame
    commission=COMMISSION_PER_TRANSACTION,
    init_cash=INIT_CASH,
    plot=True,
    verbose=True,
    sort_by="rnorm",
    sentiments=None,
    strats=None,  # Only used when strategy = "multi"
    data_format=None,  # If none, format is automatically inferred
    **kwargs
):
    """Backtest financial data with a specified trading strategy

    Parameters
    ----------------
    strategy : str 
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
    data_format : str
        input data format e.g. ohlcv (default=None so format is automatically inferred)

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
                commission=commission,
                **params
            )
            strat_names.append(strat)
    else:
        cerebro.optstrategy(
            STRATEGY_MAPPING[strategy],
            init_cash=[init_cash],
            transaction_logging=[verbose],
            commission=commission,
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

    class CustomData(bt.feeds.PandasData):
        """
        Data feed that includes all the columns in the input dataframe
        """
        # Add a custom lines to the inherited ones from the base class
        lines = tuple(data.columns)

        # automatically handle parameter with -1
        # add the parameter to the parameters inherited from the base class
        params = tuple([(col, -1) for col in data.columns])

    # extend the dataframe with sentiment score
    if strategy == "sentiment":
        # initialize series for sentiments
        senti_series = pd.Series(
            sentiments, name="sentiment_score", dtype=float
        )

        # join and reset the index for dt to become the first column
        data = data.merge(
            senti_series, left_index=True, right_index=True, how="left"
        )
        data = data.reset_index()
        data_format_dict = DATA_FORMAT_MAPPING[data_format] if data_format else infer_data_format(data)

        # create PandasData using SentimentDF
        pd_data = SentimentDF(
            dataname=data, **data_format_dict
        )

    else:
        # If data has `dt` as the index, set `dt` as the first column
        # This means `backtest` supports the dataframe whether `dt` is the index or a column
        if data.index.name == "dt":
            data = data.reset_index()
        data_format_dict = DATA_FORMAT_MAPPING[data_format] if data_format else infer_data_format(data)
        pd_data = CustomData(
            dataname=data, **data_format_dict
        )

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
    sorted_combined_df = pd.concat(
        [sorted_params_df, sorted_metrics_df], axis=1
    )

    # print out the result
    print("Time used (seconds):", str(tend - tstart))

    # Save optimal parameters as dictionary
    optim_params = sorted_params_df.iloc[0].to_dict()
    optim_metrics = sorted_metrics_df.iloc[0].to_dict()
    print("Optimal parameters:", optim_params)
    print("Optimal metrics:", optim_metrics)

    if plot and strategy != "multi":
        has_volume = data_format_dict["volume"] is not None
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
