import pandas as pd
from pathlib import Path
from fastquant import backtest, STRATEGY_MAPPING, DATA_PATH, get_yahoo_data

SAMPLE_CSV = Path(DATA_PATH, "JFC_20180101_20190110_DCV.csv")
SAMPLE_STRAT_DICT = {
    "smac": {"fast_period": 35, "slow_period": [40, 50]},
    "rsi": {"rsi_lower": [15, 30], "rsi_upper": 70},
}


def test_backtest():
    """
    Ensures that the backtest function works on all the registered strategies, with their default parameter values
    """
    sample = pd.read_csv(SAMPLE_CSV, parse_dates=["dt"])
    for strategy in STRATEGY_MAPPING.keys():
        if strategy == "sentiment":
            data = get_yahoo_data("TSLA", "2020-01-01", "2020-06-10")
            cerebro = backtest(
                strategy, data, keyword="tesla", page_nums=2, senti=0.4
            )
            errmsg = "Backtest encountered error for strategy '{}'!".format(
                strategy
            )
            assert cerebro is not None, errmsg
        else:
            cerebro = backtest(strategy, sample, plot=False)
            errmsg = "Backtest encountered error for strategy '{}'!".format(
                strategy
            )
            assert cerebro is not None, errmsg


def test_multi_backtest():
    """
    Test multi-strategy
    """
    sample = pd.read_csv(SAMPLE_CSV, parse_dates=["dt"])
    cerebro = backtest("multi", sample, strats=SAMPLE_STRAT_DICT, plot=False)
    assert (
        cerebro is not None
    ), "Backtest encountered error for strategy 'multi'!"
