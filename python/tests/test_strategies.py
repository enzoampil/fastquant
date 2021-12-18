import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from datetime import datetime
from fastquant import (
    backtest,
    STRATEGY_MAPPING,
    DATA_PATH,
    get_yahoo_data,
    get_stock_data,
    get_bt_news_sentiment,
    get_disclosure_sentiment,
)

SENTI_PKL = Path(DATA_PATH, "bt_sentiments_tests.pkl")
DISCLOSURE_PKL = Path(DATA_PATH, "senti_disclosures.pkl")
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
            data = get_yahoo_data("TSLA", "2020-01-01", "2020-07-04", dividends=True)
            # use cached data instead of scraping for tests purposes.
            # sentiments = get_bt_news_sentiment(keyword="tesla", page_nums=2)
            with open(SENTI_PKL, "rb") as handle:
                sentiments = pickle.load(handle)
            cerebro = backtest(
                strategy, data, sentiments=sentiments, senti=0.4, plot=False
            )
            errmsg = "Backtest encountered error for strategy '{}'!".format(strategy)
            assert cerebro is not None, errmsg

            data_disclosures = get_stock_data(
                "TSLA",
                "2020-01-01",
                "2020-09-30",
                dividends=True,  # source="phisix"
            )

            # sentiments_disclosures = get_disclosure_sentiment(
            #     stock_code="JFC",
            #     start_date="2020-07-01",
            #     end_date="2020-09-30",
            # )

            with open(DISCLOSURE_PKL, "rb") as handle_disclosures:
                sentiments_disclosures = pickle.load(handle_disclosures)

            cerebro_disclosures = backtest(
                strategy,
                data_disclosures,
                sentiments=sentiments_disclosures,
                senti=0.2,
                plot=False,
            )
            errmsg_disclosures = "Backtest encountered error for strategy '{}'!".format(
                strategy
            )
            assert cerebro_disclosures is not None, errmsg_disclosures

        else:
            cerebro = backtest(strategy, sample, plot=False)
            errmsg = "Backtest encountered error for strategy '{}'!".format(strategy)
            assert cerebro is not None, errmsg


def test_multi_backtest():
    """
    Test multi-strategy
    """
    sample = pd.read_csv(SAMPLE_CSV, parse_dates=["dt"])
    cerebro = backtest("multi", sample, strats=SAMPLE_STRAT_DICT, plot=False)
    assert cerebro is not None, "Backtest encountered error for strategy 'multi'!"


def test_grid_backtest():
    """
    Test grid search
    """
    sample = pd.read_csv(SAMPLE_CSV, parse_dates=["dt"])
    cerebro = backtest(
        "smac",
        sample,
        fast_period=range(15, 30, 3),
        slow_period=range(40, 55, 3),
        plot=False,
    )
    assert cerebro is not None, "Backtest encountered error doing grid search on SMAC!"
