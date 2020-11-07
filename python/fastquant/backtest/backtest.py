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

# Import from package
from fastquant.strategies import (
    RSIStrategy,
    SMACStrategy,
    BaseStrategy,
    MACDStrategy,
    EMACStrategy,
    BBandsStrategy,
    BuyAndHoldStrategy,
    SentimentStrategy,
    CustomStrategy,
    TernaryStrategy,
)


# Import backtest variables
from fastquant.config import (
    INIT_CASH,
    COMMISSION_PER_TRANSACTION,
    GLOBAL_PARAMS,
    DEFAULT_PANDAS,
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
    "custom": CustomStrategy,
    "ternary": TernaryStrategy,
}

strat_docs = "\nExisting strategies:\n\n" + "\n".join(
    [key + "\n" + value.__doc__ for key, value in STRATEGY_MAPPING.items()]
)


def docstring_parameter(*sub):
    def dec(obj):
        obj.__doc__ = obj.__doc__.format(*sub)
        return obj

    return dec


def tuple_to_dict(tup):
    di = dict(tup)
    return di


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
    **kwargs
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
                **params
            )
            strat_names.append(strat)
    else:

        # Allow instance of BaseStrategy or from the predefined mapping
        if not isinstance(strategy, str) and issubclass(strategy, bt.Strategy):
            strat_name = str(strategy)
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
            **kwargs
        )
        strat_names.append(strat_name)

    # Apply Total, Average, Compound and Annualized Returns calculated using a logarithmic approach
    cerebro.addanalyzer(btanalyzers.Returns, _name="returns")
    cerebro.addanalyzer(btanalyzers.SharpeRatio, _name="mysharpe")
    cerebro.addanalyzer(btanalyzers.DrawDown, _name="drawdown")
    cerebro.addanalyzer(btanalyzers.TimeDrawDown, _name="timedraw")

    cerebro.broker.setcommission(commission=commission)

    # Treat `data` as a path if it's a string; otherwise, it's treated as a pandas dataframe
    if isinstance(data, str):
        if verbose > 0:
            print("Reading path as pandas dataframe ...")
        # Rename dt to datetime
        data = pd.read_csv(data, header=0, parse_dates=["dt"])

    if strat_name == "sentiment":
        # initialize series for sentiments
        senti_series = pd.Series(
            sentiments, name="sentiment_score", dtype=float
        )

        # join and reset the index for dt to become the first column
        data = data.merge(
            senti_series, left_index=True, right_index=True, how="left"
        )
        data = data.reset_index()

    # If a `close` column exists but an `open` column doesn't, create a new `open` column with the same values as the `close` column
    # This is for easier handling of next day trades (w/ the assumption that next day open is equal to current day close)
    if "close" in data.columns and "open" not in data.columns:
        data["open"] = data.close.shift().values

    # If data has `dt` as the index and `dt` or `datetime` are not already columns, set `dt` as the first column
    # This means `backtest` supports the dataframe whether `dt` is the index or a column
    if len(set(["dt", "datetime"]).intersection(data.columns)) == 0:
        if data.index.name == "dt":
            data = data.reset_index()
        # If the index is a datetime index, set this as the datetime column
        elif isinstance(data.index, pd.DatetimeIndex):
            data.index.name = "dt"
            data = data.reset_index()

    # Rename "dt" column to "datetime" to match the formal alias
    data = data.rename(columns={"dt": "datetime"})
    data["datetime"] = pd.to_datetime(data.datetime)

    numeric_cols = [col for col in data.columns if is_numeric_dtype(data[col])]
    params_tuple = tuple(
        [
            (col, i)
            for i, col in enumerate(data.columns)
            if col in numeric_cols + ["datetime"]
        ]
    )
    default_cols = [c for c, _ in DEFAULT_PANDAS]
    non_default_numeric_cols = tuple(
        [col for col, _ in params_tuple if col not in default_cols]
    )

    class CustomData(bt.feeds.PandasData):
        """
        Data feed that includes all the columns in the input dataframe
        """

        # Need to make sure that the new lines don't overlap w/ the default lines already in PandasData
        lines = non_default_numeric_cols

        # automatically handle parameter with -1
        # add the parameter to the parameters inherited from the base class
        params = params_tuple

    data_format_dict = tuple_to_dict(params_tuple)
    pd_data = CustomData(dataname=data, **data_format_dict)

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

    params = []
    metrics = []
    if verbose > 0:
        print("==================================================")
        print("Number of strat runs:", len(stratruns))
        print("Number of strats per run:", len(stratruns[0]))
        print("Strat names:", strat_names)

    order_history_dfs = []
    periodic_history_dfs = []
    indicator_history_dfs = []
    for strat_idx, stratrun in enumerate(stratruns):
        strats_params = {}

        if verbose > 0:
            print("**************************************************")

        for i, strat in enumerate(stratrun):
            # Get indicator history
            indicators = strat.getindicators()
            indicators_dict = {
                ind.plotlabel()
                if hasattr(ind, "plotlabel")
                else "indicator{}".format(i): ind.lines[0].array
                for i, ind in enumerate(indicators)
            }
            indicators_df = pd.DataFrame(indicators_dict)
            indicators_df.insert(0, "dt", data["datetime"].values)

            strat_name = strat_names[i]
            p_raw = strat.p._getkwargs()
            p, selected_p = {}, {}
            for k, v in p_raw.items():
                if k not in [
                    "strategy_logging",
                    "periodic_logging",
                    "transaction_logging",
                ]:
                    # Make sure the parameters are mapped to the corresponding strategy
                    if strategy == "multi":
                        key = (
                            "{}.{}".format(strat_name, k)
                            if k not in GLOBAL_PARAMS
                            else k
                        )
                        # make key with format: e.g. smac.slow_period40_fast_period10
                        if k in strats[strat_name]:
                            selected_p[k] = v
                        pkeys = "_".join(
                            ["{}{}".format(*i) for i in selected_p.items()]
                        )
                        history_key = "{}.{}".format(strat_name, pkeys)
                    else:
                        key = k

                        # make key with format: e.g. slow_period40_fast_period10
                        if k in kwargs.keys():
                            selected_p[k] = v
                        history_key = "_".join(
                            ["{}{}".format(*i) for i in selected_p.items()]
                        )
                    p[key] = v

            strats_params = {**strats_params, **p}

            if return_history:
                # columns are decided in log method of BaseStrategy class in base.py
                order_history_df = strat.order_history_df
                order_history_df["dt"] = pd.to_datetime(order_history_df.dt)
                # combine rows with identical index
                # history_df = order_history_df.set_index('dt').dropna(how='all')
                # history_dfs[history_key] = order_history_df.stack().unstack().astype(float)
                order_history_df.insert(0, "strat_name", history_key)
                order_history_df.insert(0, "strat_id", strat_idx)
                order_history_dfs.append(order_history_df)

                periodic_history_df = strat.periodic_history_df
                periodic_history_df["dt"] = pd.to_datetime(
                    periodic_history_df.dt
                )
                periodic_history_df.insert(0, "strat_name", history_key)
                periodic_history_df.insert(0, "strat_id", strat_idx)
                periodic_history_df[
                    "return"
                ] = periodic_history_df.portfolio_value.pct_change()
                periodic_history_dfs.append(periodic_history_df)

                indicators_df.insert(0, "strat_name", history_key)
                indicators_df.insert(0, "strat_id", strat_idx)
                indicator_history_dfs.append(indicators_df)

        # We run metrics on the last strat since all the metrics will be the same for all strats
        returns = strat.analyzers.returns.get_analysis()
        sharpe = strat.analyzers.mysharpe.get_analysis()
        drawdown = strat.analyzers.drawdown.get_analysis()
        timedraw = strat.analyzers.timedraw.get_analysis()
        # Combine dicts for returns and sharpe
        m = {
            **returns,
            **drawdown,
            **timedraw,
            **sharpe,
            "pnl": strat.pnl,
            "final_value": strat.final_value,
        }

        params.append(strats_params)
        metrics.append(m)
        if verbose > 0:
            print("--------------------------------------------------")
            print_dict(strats_params, "Strategy Parameters")
            print_dict(returns, "Returns")
            print_dict(sharpe, "Sharpe")
            print_dict(drawdown, "Drawdown")
            print_dict(timedraw, "Timedraw")

    params_df = pd.DataFrame(params)
    # Set the index as a separate strat id column, so that we retain the information after sorting
    strat_ids = pd.DataFrame({"strat_id": params_df.index.values})
    metrics_df = pd.DataFrame(metrics)

    # Get indices based on `sort_by` metric
    optim_idxs = np.argsort(metrics_df[sort_by].values)[::-1]
    sorted_params_df = params_df.iloc[optim_idxs].reset_index(drop=True)
    sorted_metrics_df = metrics_df.iloc[optim_idxs].reset_index(drop=True)
    sorted_strat_ids = strat_ids.iloc[optim_idxs].reset_index(drop=True)
    sorted_combined_df = pd.concat(
        [sorted_strat_ids, sorted_params_df, sorted_metrics_df], axis=1
    )

    # Save optimal parameters as dictionary
    optim_params = sorted_params_df.iloc[0].to_dict()
    optim_metrics = sorted_metrics_df.iloc[0].to_dict()

    if verbose > 0:
        print_dict(optim_params, "Optimal parameters:")
        print_dict(optim_metrics, "Optimal metrics:")

    if plot and strategy != "multi":
        has_volume = (
            data_format_dict["volume"] is not None
            if "volume" in data_format_dict.keys()
            else False
        )
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
            if verbose > 0:
                print("=============================================")
                print("Plotting backtest for optimal parameters ...")
            backtest(
                strategy,
                data,  # Treated as csv path is str, and dataframe of pd.DataFrame
                plot=plot,
                verbose=verbose,
                sort_by=sort_by,
                **optim_params
            )
    # drop extra columns #248
    if (
        len(
            set(["channel" "symbol"]).intersection(
                sorted_combined_df.columns.values
            )
        )
        == 2
    ):
        sorted_combined_df.drop(["channel", "symbol"], axis=1, inplace=True)
    if return_history:
        order_history = pd.concat(order_history_dfs)
        periodic_history = pd.concat(periodic_history_dfs)
        indicator_history = pd.concat(indicator_history_dfs)
        history_dict = dict(
            orders=order_history,
            periodic=periodic_history,
            indicators=indicator_history,
        )

        return sorted_combined_df, history_dict
    else:
        return sorted_combined_df


def print_dict(d, title="", format="inline"):
    if format is None:
        print(title, d)

    if format == "inline":
        items = [title] + ["%s:%s" % (key, value) for key, value in d.items()]
        print("\t".join(items))

    if format == "indent":
        if title != "":
            print(title)
        for key, value in d.items():
            print("\t%s:%s" % (key, value))


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
