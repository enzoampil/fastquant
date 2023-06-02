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


class DisclosuresInvestagrams:
    """
    Disclosures scraped from investagrams

    Attribues
    ---------
    disclosures_df : pd.DataFrame
        parsed disclosures
    """

    def __init__(self, symbol, from_date, to_date):
        """
        symbol : str
            phisix symbol
        from_date : str
            (%Y-%m-%d)
        end_date = str
            (%Y-%m-%d)
        """
        self.symbol = symbol
        self.from_date = from_date
        self.to_date = to_date
        self.disclosures_json = self.get_disclosures_json()
        self.disclosures_dict = self.get_disclosures_df()
        self.earnings = self.disclosures_dict["E"]
        self.dividends = self.disclosures_dict["D"]

    def get_disclosures_json(self):
        headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Referer": "https://www.investagrams.com/Stock/PSE:JFC",
            "Origin": "https://www.investagrams.com",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36",
            "Content-Type": "text/plain; charset=utf-8",
        }
        from_date_epoch = date_to_epoch(self.from_date)
        to_date_epoch = date_to_epoch(self.to_date)
        params = (
            ("symbol", "PSE:{}".format(self.symbol)),
            ("from", from_date_epoch),
            ("to", to_date_epoch),
            ("resolution", "D"),  # Setting D (daily) by default
        )

        response = requests.post(
            "https://webapi.investagrams.com/InvestaApi/TradingViewChart/timescale_marks",
            headers=headers,
            params=params,
        )
        if hasattr(response, "text"):
            assert len(response.text) > 10, "Empty response from investagrams.com"
        return response.json()

    def disclosures_json_to_df(self):
        disclosure_dfs = {}
        for disc in ["D", "E"]:
            filtered_examples = [
                ex for ex in self.disclosures_json if ex["label"] == disc
            ]
            additional_feats_df = pd.DataFrame(
                [
                    dict(
                        [
                            tuple(item.split(":"))
                            for item in ex["tooltip"]
                            if ":" in item
                        ]
                    )
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

    def get_disclosures_df(self):
        if self.disclosures_json is None:
            self.disclosures_json = self.get_disclosures_json()
        return self.disclosures_json_to_df()
