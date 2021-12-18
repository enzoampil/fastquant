#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 25 19:48:03 2019

@authors: rafmacalaba
"""
# Import standard library
from datetime import datetime, timedelta
import time
from fastquant.disclosures.pse import DisclosuresPSE

# Import modules
from tqdm import tqdm
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk
import pandas as pd


def get_sentiments(passage):
    """
    Helper function to get the sentiment from a blob of words.

    Parameters
    ----------
    passage : str
        The blob of word from description of disclosures

    Returns
    ----------
    score: float
        Output of the nltk sentiment analyzer

    """
    nltk.download("vader_lexicon", quiet=True)
    sia = SentimentIntensityAnalyzer()
    try:
        return sia.polarity_scores(passage)["compound"]
    except AttributeError:
        return 0


def get_disclosure_sentiment(stock_code, start_date, end_date=None, source="pse"):
    """
    This function scrapes pse/investagram disclosure using fastquant and calculate the
    sentiment on each disclosure.

    Parameters
    ----------
    stock_code : str
        The stock code.

    start_date: str
        start date to get the disclosure in form of "%Y-%m-%d"

    end_date: str
        end date in form of "%Y-%m-%d"

    source: str
        pse or investagrams, only supports pse as of now


    Returns
    ----------
    date_sentiments: dict
        The dictionary output of the data in form of {date: sentiment score}

    """
    start_date = datetime.strptime(start_date, "%Y-%m-%d").date().strftime("%m-%d-%Y")
    if end_date is not None:
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date().strftime("%m-%d-%Y")
    dpse = DisclosuresPSE(symbol=stock_code, start_date=start_date, end_date=end_date)

    df = dpse.get_combined_disclosures()[
        ["Announce Date and Time", "Background/Description of the Disclosure"]
    ]
    df.columns = ["date", "description"]
    df["sentiments"] = df["description"].apply(get_sentiments)
    df["date"] = pd.to_datetime(df["date"].apply(lambda x: str(x)[:11])).dt.strftime(
        "%d %b %Y"
    )
    date_sentiment = {}

    for k, v in zip(df["date"], df["sentiments"]):
        date_sentiment[k] = v

    return date_sentiment
