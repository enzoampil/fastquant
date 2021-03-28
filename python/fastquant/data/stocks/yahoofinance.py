#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import yfinance as yf


def get_yahoo_data(symbol, start_date, end_date, dividends=True):
    """Returns pricing data for a YAHOO stock symbol.

    Parameters
    ----------
    symbol : str
        Symbol of the stock in the Yahoo. You can refer to this link:
        https://www.nasdaq.com/market-activity/stocks/screener?exchange=nasdaq.
    start_date : str
        Starting date (YYYY-MM-DD) of the period that you want to get data on
    end_date : str
        Ending date (YYYY-MM-DD) of the period you want to get data on
    dividends: bool
        Include dividends in the dataframe.

    Returns
    -------
    pandas.DataFrame
        Stock data (in OHLCAV format) for the specified company and date range
    """
    df = yf.download(symbol, start=start_date, end=end_date)
    df = df.reset_index()
    rename_dict = {
        "Date": "dt",
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Adj Close": "adj_close",
        "Volume": "volume",
        "Dividends": "dividend",
    }
    if dividends:
        ticker = yf.Ticker(symbol)
        div_df = ticker.dividends

        if div_df.shape[0] > 0:
            df = df.join(div_df, how="left", on="Date")
        else:
            df["dividend"] = 0
    else:
        df["Dividends"] = 0

    rename_list = [
        "dt",
        "open",
        "high",
        "low",
        "close",
        "adj_close",
        "volume",
        "dividend",
    ]
    df = df.rename(columns=rename_dict)[rename_list].drop_duplicates()
    df["dividend"] = df["dividend"].fillna(0)
    df["dt"] = pd.to_datetime(df.dt)
    return df.set_index("dt")
