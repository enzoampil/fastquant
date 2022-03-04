from fastquant.strategies.buy_and_hold import BuyAndHoldStrategy
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import backtrader as bt

from fastquant.backtest.backtest_indicators import get_indicators_as_dict
from fastquant.config import GLOBAL_PARAMS

"""
Post backtest functionalities
- Retrieval of hisotry of orders, indicators and perodic logs
- Analysis of each strategy
- Plotting

"""


def analyze_strategies(
    init_cash,
    stratruns,
    data,
    strat_names,
    strategy,
    strats,
    sort_by,
    return_history,
    verbose,
    multi_line_indicators=None,
    **kwargs
):
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
            st_dtime = [
                bt.utils.date.num2date(num) for num in strat.lines.datetime.plot()
            ]
            indicators_dict = get_indicators_as_dict(strat, multi_line_indicators)
            indicators_df = pd.DataFrame(indicators_dict)
            indicators_df.insert(0, "dt", st_dtime)

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
                periodic_history_df["dt"] = pd.to_datetime(periodic_history_df.dt)
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
        tradeanalyzer = strat.analyzers.tradeanalyzer.get_analysis()

        # Combine dicts for returns and sharpe
        m = {
            **returns,
            **drawdown,
            **timedraw,
            **sharpe,
            "pnl": strat.pnl,
            "final_value": strat.final_value,
        }

        if "total" in tradeanalyzer.keys():
            total = tradeanalyzer["total"]["total"]
        else:
            total = np.nan

        if "won" in tradeanalyzer.keys():
            win_rate = tradeanalyzer["won"]["total"] / tradeanalyzer["total"]["total"]
            won = tradeanalyzer["won"]["total"]
            won_avg = tradeanalyzer["won"]["pnl"]["average"]
            won_avg_prcnt = tradeanalyzer["won"]["pnl"]["average"] / init_cash * 100
            won_max = tradeanalyzer["won"]["pnl"]["max"]
            won_max_prcnt = tradeanalyzer["won"]["pnl"]["max"] / init_cash * 100
        else:
            win_rate = np.nan
            won = np.nan
            won_avg = np.nan
            won_avg_prcnt = np.nan
            won_max = np.nan
            won_max_prcnt = np.nan

        if "lost" in tradeanalyzer.keys():
            lost = tradeanalyzer["lost"]["total"]
            lost_avg = tradeanalyzer["lost"]["pnl"]["average"]
            lost_avg_prcnt = tradeanalyzer["lost"]["pnl"]["average"] / init_cash * 100
            lost_max = tradeanalyzer["lost"]["pnl"]["max"]
            lost_max_prcnt = tradeanalyzer["lost"]["pnl"]["max"] / init_cash * 100
        else:
            lost = np.nan
            lost_avg = np.nan
            lost_avg_prcnt = np.nan
            lost_max = np.nan
            lost_max_prcnt = np.nan

        m2 = {
            "total": total,
            "win_rate": win_rate,
            "won": won,
            "lost": lost,
            "won_avg": won_avg,
            "won_avg_prcnt": won_avg_prcnt,
            "lost_avg": lost_avg,
            "lost_avg_prcnt": lost_avg_prcnt,
            "won_max": won_max,
            "won_max_prcnt": won_max_prcnt,
            "lost_max": lost_max,
            "lost_max_prcnt": lost_max_prcnt,
        }

        m = {**m, **m2}

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

    # Find optimal parameters
    sorted_combined_df, optim_params = sort_metrics_params_and_strats(
        metrics_df, params_df, strat_ids, sort_by, verbose
    )

    # History dict
    if return_history:
        order_history = pd.concat(order_history_dfs)
        periodic_history = pd.concat(periodic_history_dfs)
        indicator_history = pd.concat(indicator_history_dfs)
        history_dict = dict(
            orders=order_history,
            periodic=periodic_history,
            indicators=indicator_history,
        )
    else:
        history_dict = dict()

    return sorted_combined_df, optim_params, history_dict


def sort_metrics_params_and_strats(metrics_df, params_df, strat_ids, sort_by, verbose):

    # Get indices based on `sort_by` metric
    optim_idxs = np.argsort(metrics_df[sort_by].values)[::-1]
    sorted_params_df = params_df.iloc[optim_idxs].reset_index(drop=True)
    sorted_metrics_df = metrics_df.iloc[optim_idxs].reset_index(drop=True)
    sorted_strat_ids = strat_ids.iloc[optim_idxs].reset_index(drop=True)
    sorted_combined_df = pd.concat(
        [sorted_strat_ids, sorted_params_df, sorted_metrics_df], axis=1
    )

    optim_params = get_optim_metrics_and_params(
        sorted_metrics_df, sorted_params_df, verbose
    )
    # drop extra columns #248
    if (
        len(set(["channel" "symbol"]).intersection(sorted_combined_df.columns.values))
        == 2
    ):
        sorted_combined_df.drop(["channel", "symbol"], axis=1, inplace=True)

    return sorted_combined_df, optim_params


def get_optim_metrics_and_params(sorted_metrics_df, sorted_params_df, verbose):
    # Save optimal parameters as dictionary
    optim_params = sorted_params_df.iloc[0].to_dict()
    optim_metrics = sorted_metrics_df.iloc[0].to_dict()

    if verbose > 0:
        print_dict(optim_params, "Optimal parameters:")
        print_dict(optim_metrics, "Optimal metrics:")

    return optim_params


def plot_results(cerebro, data_format_dict, figsize=(30, 15), **plot_kwargs):

    try:
        # This handles the Colab Plotting, Simple Check if we are in Colab
        from google.colab import drive

        iplot = False
    except Exception:
        iplot = True

    has_volume = (
        data_format_dict["volume"] is not None
        if "volume" in data_format_dict.keys()
        else False
    )

    # Set matplotlib parameters
    plt.style.use("classic")  # ggplot is also fine
    plt.rcParams["figure.figsize"] = figsize

    fig = cerebro.plot(volume=has_volume, iplot=iplot, **plot_kwargs)

    return fig[0][0]


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
