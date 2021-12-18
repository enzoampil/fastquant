import os
import requests
from datetime import datetime, timedelta
import time
from pathlib import Path
from pkg_resources import resource_filename

# Import modules
import pandas as pd
import numpy as np
import lxml.html as LH
from tqdm import tqdm
import tweepy
import yfinance as yf
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk
from urllib.request import urlopen
from bs4 import BeautifulSoup

# Import package modules
from fastquant.config import (
    DATA_PATH,
    PSE_TWITTER_ACCOUNTS,
    DATA_FORMAT_COLS,
    CALENDAR_FORMAT,
    PSE_STOCK_TABLE_FILE,
    PSE_CACHE_FILE,
)


def process_phisix_date_dict(phisix_dict):
    date = datetime.strftime(
        pd.to_datetime(phisix_dict["as_of"]).date(), CALENDAR_FORMAT
    )
    stock_dict = phisix_dict["stock"][0]
    stock_price_dict = stock_dict["price"]
    name = stock_dict["name"]
    currency = stock_price_dict["currency"]
    closing_price = stock_price_dict["amount"]
    percent_change = stock_dict["percent_change"]
    volume = stock_dict["volume"]
    symbol = stock_dict["symbol"]
    return {
        "dt": date,
        "name": name,
        "currency": currency,
        "close": closing_price,
        "percent_change": percent_change,
        "volume": volume,
        "symbol": symbol,
    }


def get_phisix_data_by_date(symbol, date):
    """
    Requests data in json format from phisix API

    Note: new API endpoint is now used, with fallback to old API
    """

    new_endpoint = "http://1.phisix-api.appspot.com/stocks/"
    url = new_endpoint + "{}.{}.json".format(symbol, date)
    res = requests.get(url)
    if res.ok:
        unprocessed_dict = res.json()
        processed_dict = process_phisix_date_dict(unprocessed_dict)
        return processed_dict
    else:
        # fallback to old endpoint
        old_endpoint = "http://phisix-api2.appspot.com/stocks/"
        url = old_endpoint + "{}.{}.json".format(symbol, date)
        res = requests.get(url)
        if res.ok:
            unprocessed_dict = res.json()
            processed_dict = process_phisix_date_dict(unprocessed_dict)
            return processed_dict
        else:
            if res.status_code == 500:
                # server error
                res.raise_for_status()
            else:
                # non-trading day
                return None


def get_phisix_data(symbol, start_date, end_date, save=False, max_straight_nones=10):
    """Returns pricing data for a PHISIX stock symbol.

    Parameters
    ----------
    symbol : str
        Symbol of the stock in the PSE. You can refer to this link: https://www.pesobility.com/stock.
    start_date : str
        Starting date (YYYY-MM-DD) of the period that you want to get data on
    end_date : str
        Ending date (YYYY-MM-DD) of the period you want to get data on

    Returns
    -------
    pandas.DataFrame
        Stock data (in CV format) for the specified company and date range
    """
    date_range = (
        pd.period_range(start_date, end_date, freq="D").to_series().astype(str).values
    )

    max_straight_nones = min(max_straight_nones, len(date_range))
    pse_data_list = []
    straight_none_count = 0
    for i, date in tqdm(enumerate(date_range)):
        iter_num = i + 1
        pse_data_1day = get_phisix_data_by_date(symbol, date)

        # Return None if the first `max_straight_nones` phisix iterations return Nones (status_code != 200)
        if pse_data_1day is None:
            if iter_num < max_straight_nones:
                straight_none_count += 1
            else:
                straight_none_count += 1
                if straight_none_count >= max_straight_nones:
                    print(
                        "{} not found in phisix after the first {} date iterations!".format(
                            symbol, straight_none_count
                        )
                    )
                    return None
            continue
        else:
            # Refresh straight none count when phisix returns
            straight_none_count = 0
        pse_data_list.append(pse_data_1day)
    pse_data_df = pd.DataFrame(pse_data_list)
    pse_data_df = pse_data_df[["dt", "close", "volume"]]
    return pse_data_df
