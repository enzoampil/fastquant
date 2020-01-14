#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 25 19:48:03 2019

@author: enzoampil
"""

import os
import requests
from datetime import datetime
import pandas as pd
from string import digits
import lxml.html as LH
from bs4 import BeautifulSoup
import tweepy

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


def get_stock_table(stock_table_fp="stock_table.csv"):
    """
    Returns dataframe containing info about PSE listed stocks while also saving it
    """
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


def date_to_epoch(date):
    return int(datetime.strptime(date, "%Y-%m-%d").timestamp())


def remove_digits(string):
    remove_digits = str.maketrans("", "", digits)
    res = string.translate(remove_digits)
    return res


def get_disclosures_json(symbol, from_date, to_date):
    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Referer": "https://www.investagrams.com/Stock/PSE:JFC",
        "Origin": "https://www.investagrams.com",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36",
        "Content-Type": "text/plain; charset=utf-8",
    }
    from_date_epoch = date_to_epoch(from_date)
    to_date_epoch = date_to_epoch(to_date)
    params = (
        ("symbol", "PSE:{}".format(symbol)),
        ("from", from_date_epoch),
        ("to", to_date_epoch),
        ("resolution", "D"),  # Setting D (daily) by default
    )

    response = requests.post(
        "https://webapi.investagrams.com/InvestaApi/TradingViewChart/timescale_marks",
        headers=headers,
        params=params,
    )
    results = response.json()
    return results


def disclosures_json_to_df(disclosures):
    disclosure_dfs = {}
    for disc in ["D", "E"]:
        filtered_examples = [ex for ex in disclosures if ex["label"] == disc]
        additional_feats_df = pd.DataFrame(
            [
                dict([tuple(item.split(":")) for item in ex["tooltip"] if ":" in item])
                for ex in filtered_examples
            ]
        )
        main_df = pd.DataFrame(filtered_examples)[["id", "time", "color", "label"]]
        combined = pd.concat([main_df, additional_feats_df], axis=1)
        combined["time"] = pd.to_datetime(combined.time, unit="s")
        if "Total Revenue" in combined.columns.values:
            combined["Revenue Unit"] = combined["Total Revenue"].apply(
                lambda x: remove_digits(x).replace(".", "")
            )
            combined["Total Revenue"] = (
                combined["Total Revenue"]
                .str.replace("B", "")
                .str.replace("M", "")
                .astype(float)
            )
            # Net income is followed by a parenthesis which corresponds to that quarter's YoY growth
            combined["NI Unit"] = combined["Net Income"].apply(
                lambda x: remove_digits(x).replace(".", "")
            )
            combined["Net Income Amount"] = (
                combined["Net Income"]
                .str.replace("B", "")
                .str.replace("M", "")
                .apply(lambda x: x.split()[0])
                .astype(float)
            )
            combined["Net Income YoY Growth (%)"] = combined["Net Income"].apply(
                lambda x: str(x)
                .replace("(", "")
                .replace(")", "")
                .replace("%", "")
                .split()[1]
            )
        disclosure_dfs[disc] = combined
    return disclosure_dfs


def get_disclosures_df(symbol, from_date, to_date):
    disclosures = get_disclosures_json(symbol, from_date, to_date)
    disclosures_dfs = disclosures_json_to_df(disclosures)
    return disclosures_dfs


def get_pse_data(
    symbol, start_date, end_date, stock_table_fp="stock_table.csv", disclosures=False
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

    if os.path.isfile(stock_table_fp):
        print("Stock table exists!")
        print("Reading {} ...".format(stock_table_fp))
        stock_table = pd.read_csv(stock_table_fp)
    else:
        stock_table = get_stock_table(stock_table_fp=stock_table_fp)

    data = {
        "cmpy_id": int(
            stock_table["company_id"][stock_table["Stock Symbol"] == symbol].values[0]
        ),
        "security_id": int(
            stock_table["security_id"][stock_table["Stock Symbol"] == symbol].values[0]
        ),
        "startDate": datetime.strptime(start_date, "%Y-%m-%d").strftime("%m-%d-%Y"),
        "endDate": datetime.strptime(end_date, "%Y-%m-%d").strftime("%m-%d-%Y"),
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
    df = df.set_index("dt")
    df.index = pd.to_datetime(df.index)

    return df


def pse_data_to_csv(
    symbol,
    start_date,
    end_date,
    pse_dir="",
    stock_table_fp="stock_table.csv",
    disclosures=False,
):
    pse = get_pse_data(
        symbol,
        start_date,
        end_date,
        stock_table_fp=stock_table_fp,
        disclosures=disclosures,
    )
    if isinstance(pse, pd.DataFrame):
        pse.to_csv("{}{}_{}_{}_OHLCV.csv".format(pse_dir, symbol, start_date, end_date))
    else:
        pse[0].to_csv(
            "{}{}_{}_{}_OHLCV.csv".format(pse_dir, symbol, start_date, end_date)
        )
        performance_dict = pse[1]
        performance_dict["D"].to_csv(
            "{}{}_{}_{}_D.csv".format(pse_dir, symbol, start_date, end_date)
        )
        performance_dict["E"].to_csv(
            "{}{}_{}_{}_E.csv".format(pse_dir, symbol, start_date, end_date)
        )


def get_company_disclosures(symbol, from_date="06-26-2017", to_date="06-26-2019"):
    """
    symbol str - Ticker of the pse stock of choice
    from_date date str %m-%d-%Y - Beginning date of the disclosure data pull
    to_date date str %m-%d-%Y - Ending date of the disclosure data pull
    """
    cookies = {
        "BIGipServerPOOL_EDGE": "1427584378.20480.0000",
        "JSESSIONID": "oAO1PNOZzGBoxIqtxy-32mVx.server-ep",
    }

    headers = {
        "Origin": "https://edge.pse.com.ph",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "en-PH,en-US;q=0.9,en;q=0.8",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Accept": "*/*",
        "Referer": "https://edge.pse.com.ph/announcements/form.do",
        "X-Requested-With": "XMLHttpRequest",
        "Connection": "keep-alive",
    }

    data = {
        "companyId": "",
        "keyword": symbol,
        "tmplNm": "",
        "fromDate": from_date,
        "toDate": to_date,
    }

    response = requests.post(
        "https://edge.pse.com.ph/announcements/search.ax",
        headers=headers,
        cookies=cookies,
        data=data,
    )
    html = response.text
    # Indicating the parser (e.g.  lxml) removes the bs warning
    parsed_html = BeautifulSoup(html, "lxml")
    table = parsed_html.find("table", {"class": "list"})
    table_rows = table.find_all("tr")
    l = []
    edge_nos = []
    for tr in table_rows:
        td = tr.find_all("td")
        row = [tr.text for tr in td]
        onclicks_raw = [tr.a["onclick"] for tr in td if tr.a and "onclick" in tr.a.attrs.keys()]
        onclicks = [s[s.find("('")+2:s.find("')")] for s in onclicks_raw]
        l.append(row)
        if onclicks:
            edge_nos.append(onclicks[0])

    columns = [el.text for el in table.find_all("th")]

    df = pd.DataFrame(l, columns=columns)
    # Filter to rows where not all columns are null
    df = df[df.isna().mean(axis=1) < 1]
    df['edge_nos'] = edge_nos
    df['url'] = "https://edge.pse.com.ph/openDiscViewer.do?edge_no=" + df.edge_nos
    df["Announce Date and Time"] = pd.to_datetime(df["Announce Date and Time"])
    return df


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
