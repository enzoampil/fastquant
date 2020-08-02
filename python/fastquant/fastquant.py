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
import ccxt

DATA_PATH = resource_filename(__name__, "data")

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


def get_stock_table(stock_table_fp=None):
    """
    Returns dataframe containing info about PSE listed stocks while also saving it
    """
    if stock_table_fp is None:
        stock_table_fp = Path(DATA_PATH, "stock_table.csv")

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
                    pd.DataFrame(
                        {"attr": table.xpath("//tr/td/a/@onclick")[::2]}
                    ),
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

        stock_table = stock_table.append(page_df)
    stock_table.to_csv(stock_table_fp, index=False)
    return stock_table


def fill_gaps(df):
    """
    Fills gaps of time series dataframe with NaN rows
    """
    idx = pd.period_range(df.index.min(), df.index.max(), freq="D")
    # idx_forecast = pd.period_range(start_datetime, end_datetime, freq="H")
    ts = pd.DataFrame({"empty": [0 for i in range(idx.shape[0])]}, index=idx)
    ts = ts.to_timestamp()
    df_filled = pd.concat([df, ts], axis=1)
    del df_filled["empty"]
    return df_filled


def get_pse_data_old(
    symbol, start_date, end_date, stock_table_fp=None, verbose=True
):

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
            stock_table["company_id"][
                stock_table["Stock Symbol"] == symbol
            ].values[0]
        ),
        "security_id": int(
            stock_table["security_id"][
                stock_table["Stock Symbol"] == symbol
            ].values[0]
        ),
        "startDate": datetime.strptime(start_date, CALENDAR_FORMAT).strftime(
            "%m-%d-%Y"
        ),
        "endDate": datetime.strptime(end_date, CALENDAR_FORMAT).strftime(
            "%m-%d-%Y"
        ),
    }

    r = requests.post(
        url="https://edge.pse.com.ph/common/DisclosureCht.ax", json=data
    )
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


def update_pse_data_cache(start_date="2010-01-01", verbose=True):
    """
    Downloads DOHLC data of all PSE comapnies using get_pse_old
    and saves as .zip in /data to be used as cache

    NOTE: useful to add sector in column
    """
    if verbose:
        print("Updating cache...")
    date_today = datetime.now().date().strftime("%Y-%m-%d")

    ifp = Path(DATA_PATH, "company_names.csv")
    names = pd.read_csv(ifp)

    data, unavailable = {}, []
    for symbol in tqdm(names.Symbol):
        try:
            df = get_pse_data_old(
                symbol, start_date, date_today, verbose=False
            )
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
    ofp = Path(DATA_PATH, "merged_stock_data.zip")
    DF.to_csv(ofp, index=True)
    if verbose:
        print("Saved: ", ofp)
    # return DF


def get_pse_data_cache(
    symbol=None, cache_fp=None, update=False, verbose=False
):
    """
    Loads cached historical data
    Returns all if symbol is None
    """
    if update:
        update_pse_data_cache()
    if cache_fp is None:
        cache_fp = Path(DATA_PATH, "merged_stock_data.zip")

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


def get_phisix_data(
    symbol, start_date, end_date, save=False, max_straight_nones=10
):
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
        pd.period_range(start_date, end_date, freq="D")
        .to_series()
        .astype(str)
        .values
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

    fp = Path(
        DATA_PATH, "{}_stock_{}_{}.csv".format(symbol, start_date, end_date)
    )

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
                pse_data_df = pd.concat(
                    [cache, pse_data_df], ignore_index=True
                )
        else:
            pse_data_df = cache.copy()

    pse_data_df["dt"] = pd.to_datetime(pse_data_df.dt)
    idx = (start <= pse_data_df["dt"]) & (pse_data_df["dt"] <= end)
    pse_data_df = pse_data_df[idx].drop_duplicates("dt")
    if save:
        pse_data_df.to_csv(fp, index=False)
        print(f"Saved: ", fp)
    return pse_data_df.set_index("dt")


def get_yahoo_data(symbol, start_date, end_date):
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
    }
    rename_list = ["dt", "open", "high", "low", "close", "adj_close", "volume"]
    df = df.rename(columns=rename_dict)[rename_list].drop_duplicates()
    df["dt"] = pd.to_datetime(df.dt)
    return df.set_index("dt")


def get_stock_data(symbol, start_date, end_date, source="phisix", format="c"):

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

    df_columns = [DATA_FORMAT_COLS[c] for c in format]
    if source == "phisix":
        # The query is run on 'phisix', but if the symbol isn't found, the same query is run on 'yahoo'.
        df = get_pse_data(symbol, start_date, end_date, format=format)
        if df is None:
            df = get_yahoo_data(symbol, start_date, end_date)
    elif source == "yahoo":
        # The query is run on 'yahoo', but if the symbol isn't found, the same query is run on 'phisix'.
        df = get_yahoo_data(symbol, start_date, end_date)
        if df is None:
            df = get_pse_data(symbol, start_date, end_date)
    else:
        raise Exception("Source must be either 'phisix' or 'yahoo'")

    missing_columns = [col for col in df_columns if col not in df.columns]

    # Fill missing columns with np.nan
    for missing_column in missing_columns:
        df[missing_column] = np.nan

    if len(missing_columns) > 0:
        print("Missing columns filled w/ NaN:", missing_columns)

    return df[df_columns]


def unix_time_millis(date):
    epoch = datetime.utcfromtimestamp(0)
    dt = datetime.strptime(date, "%Y-%m-%d")
    # return int((dt - epoch).total_seconds() * 1000)
    return int(dt.timestamp() * 1000)


def get_crypto_data(ticker, start_date, end_date):
    """
    Get crypto data in OHLCV format

    List of tickers here: https://coinmarketcap.com/exchanges/binance/
    """
    start_date_epoch = unix_time_millis(start_date)
    binance = ccxt.binance({"verbose": False})
    ohlcv_lol = binance.fetch_ohlcv(ticker, "1d", since=start_date_epoch)
    ohlcv_df = pd.DataFrame(
        ohlcv_lol, columns=["dt", "open", "high", "low", "close", "volume"]
    )
    ohlcv_df["dt"] = pd.to_datetime(ohlcv_df["dt"], unit="ms")
    ohlcv_df = ohlcv_df[ohlcv_df.dt <= end_date]
    return ohlcv_df.set_index("dt")


def pse_data_to_csv(symbol, start_date, end_date, pse_dir=DATA_PATH):
    """
    """
    pse = get_pse_data(symbol, start_date, end_date)
    fp = Path(
        pse_dir, "{}_{}_{}_OHLCV.csv".format(symbol, start_date, end_date)
    )
    if isinstance(pse, pd.DataFrame):
        pse.to_csv(fp)
    else:
        pse[0].to_csv(fp)
        performance_dict = pse[1]
        performance_dict["D"].to_csv(
            Path(
                pse_dir, "{}_{}_{}_D.csv".format(symbol, start_date, end_date)
            )
        )
        performance_dict["E"].to_csv(
            Path(
                pse_dir, "{}_{}_{}_E.csv".format(symbol, start_date, end_date)
            )
        )


def tweepy_api(consumer_key, consumer_secret, access_token, access_secret):
    """
    Returns authenticated tweepy.API object

    Sample methods:
        user_timeline: returns recent tweets from a specified twitter user
        - screen_name: username of account of interest
        - count: number of most recent tweets to return
    """
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_secret)
    api = tweepy.API(auth)
    return api


def datestring_to_datetime(date, sep="-"):
    ymd = date.split(sep)
    errmsg = "date format must be YYYY-MM-DD"
    assert len(ymd[0]) == 4, errmsg
    return datetime(*map(int, ymd))


def get_bt_news_sentiment(keyword, page_nums=None):
    """
    This function scrapes Business Times (https://www.businesstimes.com.sg) articles by giving
    a specific keyword e.g "facebook, jollibee" and number of pages that you needed.

    Parameters
    ----------
    keyword : str
        The keyword you wanted to search for in Business Times page.
    page_nums : int
        The number of iteration of pages you want to scrape.

    Returns
    ----------
    date_sentiments: dict
        The dictionary output of the scraped data in form of {date: sentiment score}

    TO DO: change page_nums to a start_date (and end_date maybe)
    """

    nltk.download("vader_lexicon", quiet=True)  # download vader lexicon

    if page_nums is None:
        page_nums = 1
        print("no page numbers indicated, setting this variable to 1")

    date_sentiments = {}
    sia = SentimentIntensityAnalyzer()

    for i in tqdm(range(1, page_nums + 1)):
        page = urlopen(
            "https://www.businesstimes.com.sg/search/{}?page={}".format(
                keyword.replace(" ", "%20"), str(i)
            )
        ).read()
        soup = BeautifulSoup(page, features="html.parser")
        posts = soup.findAll("div", {"class": "media-body"})
        for post in posts:
            time.sleep(1)
            url = post.a["href"]
            date = post.time.text
            try:
                link_page = urlopen(url).read()
            except Exception:
                url = url[:-2]
                link_page = urlopen(url).read()
            link_soup = BeautifulSoup(link_page, features="lxml")
            sentences = link_soup.findAll("p")
            passage = ""
            for sentence in sentences:
                passage += sentence.text
            sentiment = sia.polarity_scores(passage)["compound"]
            date_sentiments.setdefault(date, []).append(sentiment)

    date_sentiment = {}

    for k, v in date_sentiments.items():
        date_sentiment[
            datetime.strptime(k, "%d %b %Y").date() + timedelta(days=1)
        ] = round(sum(v) / float(len(v)), 3)

    return date_sentiment
