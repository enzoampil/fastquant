import os
from pkg_resources import resource_filename
from pathlib import Path


# Backtesting arguments
INIT_CASH = 100000
COMMISSION_PER_TRANSACTION = 0
DATA_FILE = resource_filename(__name__, "data/JFC_20180101_20190110_DCV.csv")

BUY_PROP = 1
SELL_PROP = 1
SHORT_MAX = 1.5

DEFAULT_PANDAS = (
    ("datetime", None),
    ("open", -1),
    ("high", -1),
    ("low", -1),
    ("close", -1),
    ("volume", -1),
    ("openinterest", -1),
)

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

# Data Config

DATA_PATH = resource_filename(__name__, "data")

if not Path(DATA_PATH).exists():
    os.makedirs(DATA_PATH)

# CSV file containing all the listed PSE companies
PSE_STOCK_TABLE_FILE = "stock_table.py"

# Cache file for PSE prices in OHLC format
PSE_CACHE_FILE = "merged_stock_data.zip"

PSE_TWITTER_ACCOUNTS = [
    "phstockexchange",
    "colfinancial",
    "firstmetrosec",
    "BPItrade",
    "Philstocks_",
    "itradeph",
    "UTradePH",
    "wealthsec",
]

DATA_FORMAT_COLS = {
    "o": "open",
    "h": "high",
    "l": "low",
    "c": "close",
    "v": "volume",
    "i": "openinterest",
}

CALENDAR_FORMAT = "%Y-%m-%d"
