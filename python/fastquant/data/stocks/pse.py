#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 25 19:48:03 2019

@authors: enzoampil & jpdeleon
"""
# Import standard library
import os
import requests
from datetime import datetime, timedelta
from pathlib import Path

# Import modules
import pandas as pd
from pandas import json_normalize
import numpy as np
import lxml.html as LH
from tqdm import tqdm

# Import package modules
from fastquant.config import (
    DATA_PATH,
    PSE_TWITTER_ACCOUNTS,
    DATA_FORMAT_COLS,
    CALENDAR_FORMAT,
    PSE_STOCK_TABLE_FILE,
    PSE_CACHE_FILE,
)
from fastquant.data.stocks.phisix import get_phisix_data
from fastquant.data.stocks.yahoofinance import get_yahoo_data


def get_stock_table(stock_table_fp=None):
    """
    Returns dataframe containing info about PSE listed stocks while also saving it
    """
    if stock_table_fp is None:
        stock_table_fp = Path(DATA_PATH, PSE_STOCK_TABLE_FILE)

    stock_table = pd.DataFrame(
        columns=[
            "Company Name",
            "Stock Symbol",
            "Sector",
            "Subsector",
            "Listing Date",
            "company_id",
            "security_id",
        ]
    )

    data = {
        "pageNo": "1",
        "companyId": "",
        "keyword": "",
        "sortType": "",
        "dateSortType": "DESC",
        "cmpySortType": "ASC",
        "symbolSortType": "ASC",
        "sector": "ALL",
        "subsector": "ALL",
    }

    for p in range(1, 7):
        print(str(p) + " out of " + str(7 - 1) + " pages", end="\r")
        data["pageNo"] = str(p)
        r = requests.post(
            url="https://edge.pse.com.ph/companyDirectory/search.ax", data=data
        )
        table = LH.fromstring(r.text)
        page_df = (
            pd.concat(
                [
                    pd.read_html(r.text)[0],
                    pd.DataFrame({"attr": table.xpath("//tr/td/a/@onclick")[::2]}),
                ],
                axis=1,
            )
            .assign(
                company_id=lambda x: x["attr"].apply(
                    lambda s: s[s.index("(") + 2 : s.index(",") - 1]
                )
            )
            .assign(
                security_id=lambda x: x["attr"].apply(
                    lambda s: s[s.index(",") + 2 : s.index(")") - 1]
                )
            )
            .drop(["attr"], axis=1)
        )

        # stock_table = stock_table.append(page_df)
        stock_table = pd.concat([stock_table, page_df], ignore_index=True)
    stock_table.to_csv(stock_table_fp, index=False)
    return stock_table


def get_pse_all_stocks():
    """
    Returns dataframe containing all PSE listed stock symbols
    """

    """ Note ID is taken from inkdrop.app """
    res = requests.get("http://phisix-api.appspot.com/stocks.json")
    if not res:
        return pd.DataFrame()

    df = json_normalize(res.json(), "stock")["symbol"].sort_values()
    df.columns = ["symbol"]
    return df


def get_pse_data_old(symbol, start_date, end_date, stock_table_fp=None, verbose=True):
    """Returns pricing data for a specified stock.

    Parameters
    ----------
    symbol : str
        Symbol of the stock in the PSE. You can refer to this link: https://www.pesobility.com/stock.
    start_date : str
        Starting date (YYYY-MM-DD) of the period that you want to get data on
    end_date : str
        Ending date (YYYY-MM-DD) of the period you want to get data on
    stock_table_fp : str
        File path of an existing stock table or where a newly downloaded table should be saved

    Returns
    -------
    pandas.DataFrame
        Stock data (in OHLCV format) for the specified company and date range
    """
    if stock_table_fp is None:
        stock_table_fp = Path(DATA_PATH, "stock_table.csv")

    if stock_table_fp.exists():
        stock_table = pd.read_csv(stock_table_fp)
        if verbose:
            print("Loaded: ", stock_table_fp)
    else:
        stock_table = get_stock_table(stock_table_fp=stock_table_fp)

    data = {
        "cmpy_id": int(
            stock_table["company_id"][stock_table["Stock Symbol"] == symbol].values[0]
        ),
        "security_id": int(
            stock_table["security_id"][stock_table["Stock Symbol"] == symbol].values[0]
        ),
        "startDate": datetime.strptime(start_date, CALENDAR_FORMAT).strftime(
            "%m-%d-%Y"
        ),
        "endDate": datetime.strptime(end_date, CALENDAR_FORMAT).strftime("%m-%d-%Y"),
    }

    r = requests.post(url="https://edge.pse.com.ph/common/DisclosureCht.ax", json=data)
    df = pd.DataFrame(r.json()["chartData"])
    rename_dict = {
        "CHART_DATE": "dt",
        "OPEN": "open",
        "HIGH": "high",
        "LOW": "low",
        "CLOSE": "close",
        "VALUE": "value",
    }
    rename_list = ["dt", "open", "high", "low", "close", "value"]
    df = df.rename(columns=rename_dict)[rename_list].drop_duplicates()
    df.dt = pd.to_datetime(df.dt)
    df = df.set_index("dt")
    return df


def get_pse_data_cache(symbol=None, cache_fp=None, update=False, verbose=False):
    """
    Loads cached historical data
    Returns all if symbol is None
    """
    if update:
        update_pse_data_cache()
    if cache_fp is None:
        cache_fp = Path(DATA_PATH, PSE_CACHE_FILE)

    if cache_fp.exists():
        df = pd.read_csv(cache_fp, index_col=0, header=[0, 1])
        df.index = pd.to_datetime(df.index)
        if verbose:
            print("Loaded: ", cache_fp)
        return df if symbol is None else df[symbol] if symbol in df.columns else None
    else:
        errmsg = "Cache does not exist! Try update=True"
        print(errmsg)
        return None


def update_pse_data_cache(start_date="2010-01-01", verbose=True, cache_fp=None):
    """
    Downloads DOHLC data of all PSE comapnies using get_pse_old
    and saves as .zip in /data to be used as cache

    NOTE: useful to add sector in column
    """
    if verbose:
        print("Updating cache...")
    date_today = datetime.now().date().strftime("%Y-%m-%d")

    names = get_stock_table(stock_table_fp=None)

    data, unavailable = {}, []
    for symbol in tqdm(names["Stock Symbol"].values):
        try:
            df = get_pse_data_old(symbol, start_date, date_today, verbose=False)
            data[symbol] = df
        except Exception as e:
            unavailable.append(symbol)
            print(e)
    if verbose:
        print("No data:\n", unavailable)

    # concatenate by column after sorting by date
    DF = pd.concat(data, axis=1, sort=True)
    DF.columns.names = ["Symbol", None]
    DF.index.name = "dt"

    # save as csv
    if cache_fp is None:
        cache_fp = Path(DATA_PATH, PSE_CACHE_FILE)

    DF.to_csv(cache_fp, index=True)
    if verbose:
        print("Saved: ", cache_fp)
    # return DF


def get_pse_data(
    symbol,
    start_date,
    end_date,
    save=False,
    max_straight_nones=10,
    format="dohlc",
):
    """Returns pricing data for a PHISIX stock symbol with caching.

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
    start = datestring_to_datetime(start_date)
    end = datestring_to_datetime(end_date)

    fp = Path(DATA_PATH, "{}_stock_{}_{}.csv".format(symbol, start_date, end_date))

    if "v" in format:
        if fp.exists():
            pse_data_df = pd.read_csv(fp)
        else:
            pse_data_df = get_phisix_data(
                symbol, start_date, end_date, save=False, max_straight_nones=10
            )
        if pse_data_df is None:
            return None
    else:
        cache = get_pse_data_cache(symbol=symbol)
        # Return None if the column is not in the cached df
        if cache is None:
            return None
        cache = cache.reset_index()
        # oldest_date = cache["dt"].iloc[0]
        newest_date = cache["dt"].iloc[-1]
        if newest_date <= end:
            # overwrite start date
            start_date = newest_date.strftime(CALENDAR_FORMAT)
            pse_data_df = get_phisix_data(
                symbol, start_date, end_date, save=False, max_straight_nones=10
            )
            if not pse_data_df.empty:
                pse_data_df = pd.concat([cache, pse_data_df], ignore_index=True)
        else:
            pse_data_df = cache.copy()

    pse_data_df["dt"] = pd.to_datetime(pse_data_df.dt)
    idx = (start <= pse_data_df["dt"]) & (pse_data_df["dt"] <= end)
    pse_data_df = pse_data_df[idx].drop_duplicates("dt")
    if save:
        pse_data_df.to_csv(fp, index=False)
        print("Saved: ", fp)
    # add dividend column for dividends sake XD

    pse_data_df["dividend"] = 0
    return pse_data_df.set_index("dt")


def datestring_to_datetime(date, sep="-"):
    ymd = date.split(sep)
    errmsg = "date format must be YYYY-MM-DD"
    assert len(ymd[0]) == 4, errmsg
    return datetime(*map(int, ymd))


def pse_data_to_csv(symbol, start_date, end_date, pse_dir=DATA_PATH):
    """"""
    pse = get_pse_data(symbol, start_date, end_date)
    fp = Path(
        pse_dir,
        "{}_{}_{}_OHLCV.csCRYPTO_EXCHANGESv".format(symbol, start_date, end_date),
    )
    if isinstance(pse, pd.DataFrame):
        pse.to_csv(fp)
    else:
        pse[0].to_csv(fp)
        performance_dict = pse[1]
        performance_dict["D"].to_csv(
            Path(pse_dir, "{}_{}_{}_D.csv".format(symbol, start_date, end_date))
        )
        performance_dict["E"].to_csv(
            Path(pse_dir, "{}_{}_{}_E.csv".format(symbol, start_date, end_date))
        )
