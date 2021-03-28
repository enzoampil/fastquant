#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 25 19:48:03 2019

@authors: enzoampil & jpdeleon
"""
import numpy as np

# Import from config
from fastquant.config import DATA_FORMAT_COLS

# Import package
from fastquant.data.stocks.pse import get_pse_data
from fastquant.data.stocks.yahoofinance import get_yahoo_data


def get_stock_data(
    symbol,
    start_date,
    end_date,
    source="yahoo",
    format="ohlcv",
    dividends=True,
):
    """Returns pricing data for a specified stock and source.

    Parameters
    ----------
    symbol : str
        Symbol of the stock in the PSE or Yahoo.
        You can refer to these links:
        PHISIX: https://www.pesobility.com/stock
        YAHOO: https://www.nasdaq.com/market-activity/stocks/screener?exchange=nasdaq
    start_date : str
        Starting date (YYYY-MM-DD) of the period that you want to get data on
    end_date : str
        Ending date (YYYY-MM-DD) of the period you want to get data on
    source : str
        First source to query from ("pse", "yahoo").
        If the stock is not found in the first source,
        the query is run on the other source.
    format : str
        Format of the output data

    Returns
    -------
    pandas.DataFrame
        Stock data (in the specified `format`) for the specified company and date range
    """

    if source == "yahoo":
        # The query is run on 'yahoo', but if the symbol isn't found, the same query is run on 'phisix'.
        df = get_yahoo_data(symbol, start_date, end_date, dividends)
        if df is None or symbol == "JFC":
            format = "c"
            df = get_pse_data(symbol, start_date, end_date, format=format)

    elif source == "phisix":
        # The query is run on 'phisix', but if the symbol isn't found, the same query is run on 'yahoo'.
        format = "c"
        df = get_pse_data(symbol, start_date, end_date, format=format)
        if df is None:
            df = get_yahoo_data(symbol, start_date, end_date, dividends)

    else:
        raise Exception("Source must be either 'phisix' or 'yahoo'")

    df_columns = [DATA_FORMAT_COLS[c] for c in format]
    missing_columns = [col for col in df_columns if col not in df.columns]

    # Fill missing columns with np.nan
    for missing_column in missing_columns:
        df[missing_column] = np.nan

    if len(missing_columns) > 0:
        print("Missing columns filled w/ NaN:", missing_columns)

    # Save input parameters into dataframe
    df.start_date = start_date
    df.end_date = end_date
    df.symbol = symbol

    return df[df_columns]
