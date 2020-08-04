import os
from pkg_resources import resource_filename
from pathlib import Path

DATA_PATH = resource_filename(__name__, "data")

if not Path(DATA_PATH).exists():
    os.makedirs(DATA_PATH)


# Backtesting arguments
INIT_CASH = 100000
COMMISSION_PER_TRANSACTION = 0.0075
DATA_FILE = resource_filename(__name__, "data/JFC_20180101_20190110_DCV.csv")

BUY_PROP = 1
SELL_PROP = 1
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
