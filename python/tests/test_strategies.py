import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from fastquant import (
    backtest,
    STRATEGY_MAPPING,
    DATA_PATH,
    get_yahoo_data,
    get_bt_news_sentiment,
)

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
    # Simulate custom indicator
    sample["custom"] = np.random.random((sample.shape[0],)) * 100

    for strategy in STRATEGY_MAPPING.keys():
        if strategy == "sentiment":
            data = get_yahoo_data("TSLA", "2020-01-01", "2020-02-01")
            sentiments = get_bt_news_sentiment(keyword="tesla", page_nums=2)
            cerebro = backtest(
                strategy, data, sentiments=sentiments, senti=0.4, plot=False
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
