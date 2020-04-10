#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 5, 2020

@author: enzoampil & jpdeleon
"""

from inspect import signature
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import matplotlib.cm as cm
import numpy as np
import pandas as pd
from tqdm import tqdm
import matplotlib.pyplot as pl
import matplotlib
from fastquant import get_stock_data

matplotlib.style.use("fivethirtyeight")


COOKIES = {
    "BIGipServerPOOL_EDGE": "1427584378.20480.0000",
    "JSESSIONID": "r2CYuOovD47c6FDnDoxHKW60.server-ep",
}

TODAY = datetime.now().date().strftime("%m-%d-%Y")

__all__ = ["CompanyDisclosures"]


class CompanyDisclosures:
    """
    Attribues
    ---------
    summary : pd.DataFrame
        Company Summary
    company_disclosures :
    """

    def __init__(
        self,
        symbol,
        disclosure_type="all",
        start_date="1-1-2019",
        end_date=None,
        verbose=True,
    ):
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = TODAY if end_date is None else end_date
        self.disclosure_type = disclosure_type
        self.stock_data = None
        # self.company_summary = self.get_company_summary()
        self.verbose = verbose
        if self.verbose:
            print(f"Pulling {self.symbol} disclosures summary...")
        self.company_disclosures = self.get_company_disclosures()
        self.disclosure_types = (
            self.company_disclosures["Template Name"]
            .apply(_remove_amend)
            .unique()
        )
        if self.verbose:
            print(
                f"Found {len(self.company_disclosures)} disclosures with {len(self.disclosure_types)} types:"
            )
            print(
                f"{self.disclosure_types}\nbetween {self.start_date} & {self.end_date}."
            )
        print(f"Pulling details in all {self.symbol} disclosures...")
        self.disclosure_tables = self.get_all_disclosure_tables()
        self.disclosure_tables_df = self.get_all_disclosure_tables_df()
        self.disclosure_backgrounds = self.get_disclosure_details()
        self.disclosure_subjects = self.get_disclosure_details(
            key="Subject of the Disclosure"
        )
        self.disclosures_combined = get_combined_disclosures()
        errmsg = f"{self.disclosure_type} not available between {self.start_date} & {self.end_date}.\n"
        errmsg += f"Try {self.disclosure_types}."
        if self.disclosure_type != "all":
            assert self.disclosure_type in self.disclosure_types, errmsg

    def __repr__(self):
        fields = signature(self.__init__).parameters
        values = ", ".join(repr(getattr(self, f)) for f in fields)
        return f"{type(self).__name__}({values})"

    def get_stock_data(self):
        """overwrites get_stock_data
        """
        if self.verbose:
            print(f"Pulling {self.symbol} stock data...")
        data = get_stock_data(
            self.symbol, start_date=self.start_date, end_date=self.end_date
        )
        data["dt"] = pd.to_datetime(data.dt)
        # set dt as index
        data = data.set_index("dt")
        self.stock_data = data
        return data

    def get_company_disclosures(self):
        """
        symbol str - Ticker of the pse stock of choice
        start_date date str %m-%d-%Y - Beginning date of the disclosure data pull
        end_date date str %m-%d-%Y - Ending date of the disclosure data pull
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
        html = response.text
        # Indicating the parser (e.g.  lxml) removes the bs warning
        parsed_html = BeautifulSoup(html, "lxml")
        table = parsed_html.find("table", {"class": "list"})
        table_rows = table.find_all("tr")
        lines = []
        edge_nos = []
        for tr in table_rows:
            td = tr.find_all("td")
            row = [tr.text for tr in td]
            onclicks_raw = [
                tr.a["onclick"]
                for tr in td
                if tr.a and "onclick" in tr.a.attrs.keys()
            ]
            onclicks = [
                s[s.find("('") + 2 : s.find("')")] for s in onclicks_raw
            ]
            lines.append(row)
            if onclicks:
                edge_nos.append(onclicks[0])

        columns = [el.text for el in table.find_all("th")]

        df = pd.DataFrame(lines, columns=columns)
        # Filter to rows where not all columns are null
        df = df[df.isna().mean(axis=1) < 1]
        df["edge_no"] = edge_nos
        df["url"] = (
            "https://edge.pse.com.ph/openDiscViewer.do?edge_no=" + df.edge_no
        )
        df["Announce Date and Time"] = pd.to_datetime(
            df["Announce Date and Time"]
        )
        return df

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
        Return the company summary (at the top) given edge_no
        """
        file_id = self.get_disclosure_file_id(edge_no)
        parsed_html = self.get_disclosure_parsed_html(file_id)

        keys = []
        values = []
        for dt, dd in zip(
            parsed_html.find_all("dt"), parsed_html.find_all("dd")
        ):
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
        Return the disclosure details (at the bottom page) given the parsed tables
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

    def get_all_disclosure_tables(self):
        """
        iterate all disclosure id and save details in a dictionary
        """
        disclosure_details = {}
        for edge_no in tqdm(self.company_disclosures["edge_no"].values):
            df = self.get_disclosure_tables(edge_no)
            disclosure_details[edge_no] = df
        return disclosure_details

    def get_all_disclosure_tables_df(self):
        """
        Return disclosure tables as a dataframe
        """
        values = []
        for edge_no in self.disclosure_tables.keys():
            df = self.disclosure_tables[edge_no]
            df_dict = {k: v for k, v in df.values}
            # Convert dictionary to string
            values.append(json.dumps(df_dict))
        return pd.DataFrame(values, columns=["disclosure_table"])

    def get_disclosure_details(
        self, key="Background/Description of the Disclosure"
    ):
        """
        return a dataframe of detailed background/decription per date
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
        return pd.concat(
            [
                self.company_disclosures,
                self.disclosure_tables_df,
                self.disclosure_backgrounds,
                self.disclosure_subjects,
            ],
            axis=1,
        )

    def plot_disclosures(self, disclosure_type=None, data_type="close"):
        """
        disclosure_type : str
        """
        disclosure_type = (
            self.disclosure_type
            if disclosure_type is None
            else disclosure_type
        )

        fig = pl.figure(figsize=(15, 10))

        if self.stock_data is None:
            data = self.get_stock_data()
        else:
            data = self.stock_data

        colors = cm.rainbow(np.linspace(0, 1, len(self.disclosure_types)))
        color_map = {n: colors[i] for i, n in enumerate(self.disclosure_types)}

        ax = data[data_type].plot(c="k", zorder=1)
        for key, row in self.company_disclosures.iterrows():
            date = row["Announce Date and Time"]
            template = _remove_amend(row["Template Name"])
            if template.lower() == disclosure_type.lower():
                # vertical line
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
        handles, labels = ax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        ax.legend(by_label.values(), by_label.keys())
        ax.set_ylabel(data_type.upper())
        ax.set_title(self.symbol)
        return fig


def _remove_amend(x):
    if len(x.split("]")) == 2:
        return x.split("]")[1]
    else:
        return x
