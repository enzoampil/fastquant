#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 5, 2020

@authors: enzoampil & jpdeleon
"""
# Import standard library
import os
from inspect import signature
from datetime import datetime
import warnings
from pathlib import Path
from string import digits
import requests
import json
import re

# Import modules
import numpy as np
import pandas as pd
from tqdm import tqdm
from bs4 import BeautifulSoup
from pandas import json_normalize
import matplotlib.pyplot as pl
import matplotlib as mpl

# Import from package
from fastquant.data import get_stock_data
from fastquant.config import DATA_PATH
from fastquant.disclosures.base import (
    _remove_amend,
    format_date,
    date_to_epoch,
    remove_digits,
)

warnings.simplefilter("ignore")

COOKIES = {
    "BIGipServerPOOL_EDGE": "1427584378.20480.0000",
    "JSESSIONID": "r2CYuOovD47c6FDnDoxHKW60.server-ep",
}

CALENDAR_FORMAT = "%m-%d-%Y"
TODAY = datetime.now().date().strftime(CALENDAR_FORMAT)

# __all__ = [
#     "DisclosuresPSE",
#     "DisclosuresInvestagrams",
#     "get_company_disclosures",
# ]


class DisclosuresPSE:
    """
    Disclosures scraped from PSE

    Attribues
    ---------
    disclosures_combined : pd.DataFrame
        Company disclosure summary
    """

    def __init__(
        self,
        symbol,
        disclosure_type="all",
        start_date="1-1-2020",
        end_date=None,
        verbose=True,
        clobber=False,
    ):
        """
        Parameters
        ----------
        symbol : str
            company symbol
        disclosure_type : str
            type of disclosure available
        start_date : str
            start date with format %m-%d-%Y
        end_date : str
            end date with format %m-%d-%Y
        """
        self.symbol = symbol.upper()
        self.start_date = start_date
        self.end_date = TODAY if end_date is None else end_date
        self.disclosure_type = disclosure_type
        self.stock_data = None
        self.verbose = verbose
        self.clobber = clobber
        if self.verbose:
            print("Pulling {} disclosures summary...".format(self.symbol))
        self.files = list(
            Path(DATA_PATH).glob("{}_disclosures_*.csv".format(self.symbol))
        )
        self.fp = Path(
            DATA_PATH,
            "{}_disclosures_{}_{}.csv".format(
                self.symbol, self.start_date, self.end_date
            ),
        )
        self.company_disclosures = self.get_company_disclosures()
        self.disclosure_types = (
            self.company_disclosures["Template Name"].apply(_remove_amend).unique()
        )
        if self.verbose:
            print(
                "Found {} disclosures between {} & {} with {} types:\n{}".format(
                    len(self.company_disclosures),
                    self.start_date,
                    self.end_date,
                    len(self.disclosure_types),
                    self.disclosure_types,
                )
            )
        print("Pulling details in all {} disclosures...".format(self.symbol))
        self.disclosure_tables = self.get_all_disclosure_tables()
        self.disclosure_tables_df = self.get_all_disclosure_tables_df()
        self.disclosure_backgrounds = self.get_disclosure_details()
        self.disclosure_subjects = self.get_disclosure_details(
            key="Subject of the Disclosure"
        )
        self.disclosures_combined = self.get_combined_disclosures()
        errmsg = "{} not available between {} & {}.\n".format(
            self.disclosure_type, self.start_date, self.end_date
        )
        errmsg += "Try {}.".format(self.disclosure_types)
        if self.disclosure_type != "all":
            assert self.disclosure_type in self.disclosure_types, errmsg
        self.page_count, self.results_count = None, None

    def __repr__(self):
        """show class description after istantiation"""
        fields = signature(self.__init__).parameters
        values = ", ".join(repr(getattr(self, f)) for f in fields)
        return "{}({})".format(type(self).__name__, values)

    def get_stock_data(self, format="ohlc"):
        """overwrites get_stock_data

        Note that stock data requires YYYY-MM-DD
        """
        start_date = format_date(
            self.start_date, informat=CALENDAR_FORMAT, outformat="%Y-%m-%d"
        )
        end_date = format_date(
            self.end_date, informat=CALENDAR_FORMAT, outformat="%Y-%m-%d"
        )
        if self.verbose:
            print("Pulling {} stock data...".format(self.symbol))
        data = get_stock_data(
            self.symbol,
            start_date=start_date,
            end_date=end_date,
            format=format,
        )
        self.stock_data = data
        return data

    def get_company_disclosures_page(self, page=1):
        """
        Gets company disclosures for one page

        FIXME:
        This can be loaded using:
        cols = ['Company Name', 'Template Name', 'PSE Form Number',
                'Announce Date and Time', 'Circular Number', 'edge_no', 'url']
        self.company_disclosures = pd.read_csv(self.fp)[cols]
        but posting request is fast anyway
        """

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
            "pageNo": page,
            "companyId": "",
            "keyword": self.symbol,
            "tmplNm": "",
            "fromDate": self.start_date,
            "toDate": self.end_date,
        }

        response = requests.post(
            "https://edge.pse.com.ph/announcements/search.ax",
            headers=headers,
            cookies=COOKIES,
            data=data,
        )
        if hasattr(response, "text"):
            assert len(response.text) > 10, "Empty response from edge.pse.com.ph"

        html = response.text
        # Indicating the parser (e.g.  lxml) removes the bs warning
        parsed_html = BeautifulSoup(html, "lxml")
        current_page, page_count, results_count = re.findall(
            r"[^A-Za-z\[\]\/\s]+",
            parsed_html.find("span", {"class": "count"}).text,
        )
        current_page, self.page_count, self.results_count = (
            int(current_page),
            int(page_count),
            int(results_count),
        )
        assert (
            int(current_page) == page
        ), "Resulting page is not consistent with the requested page!"
        table = parsed_html.find("table", {"class": "list"})
        table_rows = table.find_all("tr")
        lines = []
        edge_nos = []
        for tr in table_rows:
            td = tr.find_all("td")
            row = [tr.text for tr in td]
            onclicks_raw = [
                tr.a["onclick"] for tr in td if tr.a and "onclick" in tr.a.attrs.keys()
            ]
            onclicks = [s[s.find("('") + 2 : s.find("')")] for s in onclicks_raw]
            lines.append(row)
            if onclicks:
                edge_nos.append(onclicks[0])

        columns = [el.text for el in table.find_all("th")]

        if lines[1][0] == "no data.":
            errmsg = "No disclosures between {} & {}. ".format(
                self.start_date, self.end_date
            )
            errmsg += "Try longer date interval."
            raise ValueError(errmsg)
        df = pd.DataFrame(lines, columns=columns)
        # Filter to rows where not all columns are null
        df = df[df.isna().mean(axis=1) < 1]
        df["edge_no"] = edge_nos
        df["url"] = "https://edge.pse.com.ph/openDiscViewer.do?edge_no=" + df.edge_no
        df["Announce Date and Time"] = pd.to_datetime(df["Announce Date and Time"])
        # ensure index starts at 0
        return df.reset_index(drop=True)

    def get_company_disclosures(self):
        """
        Gets company disclosures for all pages

        """

        first_page_df = self.get_company_disclosures_page(page=1)
        print("{} pages detected!".format(self.page_count))
        if self.page_count == 1:
            disclosures_df = first_page_df
        else:
            page_dfs = [first_page_df]
            # We skip the first since we already have it
            for page_num in range(2, self.page_count + 1):
                page_df = self.get_company_disclosures_page(page=page_num)
                page_dfs.append(page_df)
            pages_df = pd.concat(page_dfs).reset_index(drop=True)
            disclosures_df = pages_df
        return disclosures_df

    def get_disclosure_file_id(self, edge_no):
        """
        Returns file ID of a specified disclosure based on its edge number
        ETA: 6.2 seconds per run
        """
        headers = {
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-Mode": "navigate",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-PH,en-US;q=0.9,en;q=0.8",
        }

        params = (("edge_no", edge_no),)

        response = requests.get(
            "https://edge.pse.com.ph/openDiscViewer.do",
            headers=headers,
            params=params,
            cookies=COOKIES,
        )
        html = response.text
        parsed_html = BeautifulSoup(html, "lxml")
        s = parsed_html.iframe["src"]
        file_id = s[s.find("file_id=") + 8 :]
        return file_id

    def get_disclosure_parsed_html(self, disclosure_file_id):
        """
        Returns the bs parsed html for a disclosure given its file id
        ETA: 6.55 seconds per run
        """

        headers = {
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "nested-navigate",
            "Referer": "https://edge.pse.com.ph/openDiscViewer.do?edge_no=8a9a820ee365687cefdfc15ec263a54d",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-PH,en-US;q=0.9,en;q=0.8",
        }

        params = (("file_id", disclosure_file_id),)

        response = requests.get(
            "https://edge.pse.com.ph/downloadHtml.do",
            headers=headers,
            params=params,
            cookies=COOKIES,
        )
        html = response.text

        parsed_html = BeautifulSoup(html, "lxml")
        return parsed_html

    def parse_stock_inventory(self, stock_inventory_str):
        stock_inventory_lol = [
            row.split("\n") for row in stock_inventory_str.split("\n\n\n\n")
        ]
        stock_inventory_df = pd.DataFrame(
            stock_inventory_lol[1:], columns=stock_inventory_lol[0]
        )
        stock_inventory_df.iloc[:, 1] = (
            stock_inventory_df.iloc[:, 1]
            .apply(lambda x: x.replace(",", ""))
            .astype(int)
        )
        return stock_inventory_df

    def get_company_summary(self, edge_no):
        """
        Return the company summary (at the top of edge.pse page) given edge_no
        """
        file_id = self.get_disclosure_file_id(edge_no)
        parsed_html = self.get_disclosure_parsed_html(file_id)

        keys = []
        values = []
        for dt, dd in zip(parsed_html.find_all("dt"), parsed_html.find_all("dd")):
            # Take out first token (number followed by a period)
            key = " ".join(dt.text.strip().split()[1:])
            value = dd.text.strip()
            if "Title of Each Class\n" in value:
                stock_inventory_df = self.parse_stock_inventory(value)
                keys += stock_inventory_df.iloc[:, 0].values.tolist()
                values += stock_inventory_df.iloc[:, 1].values.tolist()
            else:
                keys.append(key)
                values.append(value)

        company_summary_df = pd.DataFrame()
        company_summary_df["key"] = keys
        company_summary_df["value"] = values
        return company_summary_df

    def parse_table(self, table_el):
        """
        Returns a table as a dataframe from a table html element
        """
        table_dict = {"header": [], "value": []}
        for tr in table_el.find_all("tr"):
            th = None
            td = None
            if tr.find("th"):
                th = tr.th.text
            if tr.find("td"):
                td = tr.td.text

            table_dict["header"].append(th)
            table_dict["value"].append(td)
        return pd.DataFrame(table_dict)

    def get_tables(self, parsed_html):
        """
        Returns a list of tables as pd.DataFrame's from parsed HTML
        """
        table_els = parsed_html.find_all("table")
        table_dfs = []
        for table_el in table_els:
            table_df = self.parse_table(table_el)
            table_dfs.append(table_df)
        return table_dfs

    def get_disclosure_tables(self, edge_no):
        """
        Returns the disclosure details (at the bottom of edge.pse page) given edge_no
        """
        file_id = self.get_disclosure_file_id(edge_no)
        parsed_html = self.get_disclosure_parsed_html(file_id)
        tables = self.get_tables(parsed_html)

        k, v = [], []
        for tab in tables:
            header = tab.header.dropna().values
            value = tab.value.dropna().values
            for i, j in zip(header, value):
                k.append(i)
                v.append(j)
        df = pd.DataFrame(np.c_[k, v], columns=["key", "value"])
        return df

    def load_disclosures(self):
        """Loads disclosures data from disk and append older or newer if necessary"""
        errmsg = "No cache file found."
        assert len(self.files) > 0, errmsg
        data = pd.read_csv(self.files[0])
        data = data.dropna(subset=["Announce Date and Time"])
        newest_date = data["Announce Date and Time"].iloc[1]
        oldest_date = data["Announce Date and Time"].iloc[-1]
        disclosure_details = {}

        # append older disclosures
        older = oldest_date > self.company_disclosures["Announce Date and Time"]
        idxs1 = np.flatnonzero(older)
        if older.sum() > 0:
            for idx in tqdm(idxs1):
                edge_no = self.company_disclosures.iloc[idx]["edge_no"]
                df = self.get_disclosure_tables(edge_no)
                disclosure_details[edge_no] = df

        # load local data from disk
        # FIXME: the JSON object must be str, bytes or bytearray, not float
        for key, row in data.iterrows():
            try:
                edge_no = row["edge_no"]
                df = json_normalize(json.loads(row["disclosure_table"])).T
                df = df.reset_index()
                df.columns = ["key", "value"]
                disclosure_details[edge_no] = df
            except Exception as e:
                print(e)

        # append newer disclosures
        newer = newest_date < self.company_disclosures["Announce Date and Time"]
        idxs2 = np.flatnonzero(newer)
        # append newer disclosures
        if newer.sum() > 0:
            for idx in tqdm(idxs2):
                edge_no = self.company_disclosures.iloc[idx]["edge_no"]
                df = self.get_disclosure_tables(edge_no)
                disclosure_details[edge_no] = df
        if self.verbose:
            print("Loaded: {}".format(self.files[0]))

        if (older.sum() > 1) or (newer.sum() > 1):
            # remove older file
            os.remove(self.files[0])
            if self.verbose:
                print("Deleted: {}".format(self.files[0]))
            self.clobber = True
        return disclosure_details

    def get_all_disclosure_tables(self):
        """
        Returns a dict after iterating all disclosures
        """
        if (len(self.files) == 0) or self.clobber:
            disclosure_details = {}
            for edge_no in tqdm(self.company_disclosures["edge_no"].values):
                df = self.get_disclosure_tables(edge_no)
                disclosure_details[edge_no] = df
        else:
            disclosure_details = self.load_disclosures()

        return disclosure_details

    def get_all_disclosure_tables_df(self):
        """
        Returns disclosure tables as a dataframe
        """
        values = []
        for edge_no in self.disclosure_tables.keys():
            df = self.disclosure_tables[edge_no]
            df_dict = {k: v for k, v in df.values}
            # Convert dictionary to string
            values.append(json.dumps(df_dict))
        return pd.DataFrame(values, columns=["disclosure_table"])

    def get_disclosure_details(self, key="Background/Description of the Disclosure"):
        """
        Returns a dataframe of specific data from disclosure_tables
        """
        values = []
        for edge_no in self.disclosure_tables.keys():
            df = self.disclosure_tables[edge_no]
            idx = df["key"].isin([key])
            value = df.loc[idx, "value"].values
            values.append(value)
        # dataframe is used instead of series for better parsing
        s = pd.DataFrame(values, columns=[key])
        return s

    def get_combined_disclosures(self):
        """
        Returns a dataframe of useful disclosure attributes
        """
        df = pd.concat(
            [
                self.company_disclosures,
                self.disclosure_tables_df,
                self.disclosure_backgrounds,
                self.disclosure_subjects,
            ],
            axis=1,
            ignore_index=False,
        )

        if (len(self.files) == 0) or self.clobber:
            df.to_csv(self.fp)
            if self.verbose:
                print("Saved: {}".format(self.fp))
        return df

    def filter_disclosures(self, indicator="close", operation="max"):
        """
        get disclosures co-incident to an extremum in percent change
        """
        # remove NaN
        df = self.disclosures_combined.copy()
        df.dropna(subset=["Announce Date and Time"], inplace=True)

        disclosure_dates = df["Announce Date and Time"].apply(lambda x: x.date())

        if self.stock_data is None:
            _ = self.get_stock_data()

        df2 = self.stock_data[indicator].pct_change()
        idx2 = df2.index.isin(disclosure_dates)
        if operation == "max":
            date = disclosure_dates.iloc[np.argmax(idx2)]
        elif operation == "min":
            date = disclosure_dates.iloc[np.argmin(idx2)]
        else:
            raise ValueError("operation=min,max")
        return df[disclosure_dates == date]

    def plot_disclosures(
        self, disclosure_type=None, indicator="close", diff=True, percent=True
    ):
        """
        Parameters
        ----------
        disclosure_type : str
            type of disclosure to highlight (default=all)
        indicator : str
            stock data to overplot (close or volume)
        diff : bool
            show previous trading day difference
        percent : True
            show percent change if diff=True
        Returns a figure instance
        """
        disclosure_type = (
            self.disclosure_type if disclosure_type is None else disclosure_type
        )

        fig = pl.figure(figsize=(15, 10))

        if self.stock_data is None:
            data = self.get_stock_data()
        else:
            data = self.stock_data

        colors = mpl.cm.rainbow(np.linspace(0, 1, len(self.disclosure_types)))
        color_map = {n: colors[i] for i, n in enumerate(self.disclosure_types)}

        df, label = data[indicator], indicator
        if diff:
            df = data[indicator].diff()
            label = indicator + " diff"
            if percent:
                df = data[indicator].pct_change()
                label = label + " (%)"

        ax = df.plot(c="k", zorder=1, label=label)
        if diff:
            # add horizontal line at zero
            ax.axhline(0, 0, 1, color="k", zorder=0, alpha=0.1)

        # add vertical line for each disclosure release date
        for key, row in self.company_disclosures.iterrows():
            date = row["Announce Date and Time"]
            template = _remove_amend(row["Template Name"])
            if template.lower() == disclosure_type.lower():
                ax.axvline(
                    date,
                    0,
                    1,
                    color=color_map[template],
                    zorder=0,
                    label=template,
                )
            elif disclosure_type == "all":
                ax.axvline(
                    date,
                    0,
                    1,
                    color=color_map[template],
                    zorder=0,
                    label=template,
                )
        # show only unique legends
        handles, labels = ax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        ax.legend(by_label.values(), by_label.keys())
        ax.set_ylabel(label.upper())
        ax.set_title(self.symbol)
        return fig

    def __call__(self):
        # return parsed data after instantiation
        return self.disclosures_combined
