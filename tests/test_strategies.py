import pandas as pd
from pathlib import Path
from fastquant import backtest, STRATEGY_MAPPING, DATA_PATH

SAMPLE_CSV = Path(DATA_PATH, "JFC_20180101_20190110_DCV.csv")


def test_backtest():
    """
    Ensures that the backtest function works on all the registered strategies, with their default parameter values
    """
    sample = pd.read_csv(SAMPLE_CSV, parse_dates=["dt"])
    for strategy in STRATEGY_MAPPING.keys():
        assert backtest(
            strategy, sample, plot=False
        ), "Backtest encountered error for strategy '{}'!".format(strategy)
