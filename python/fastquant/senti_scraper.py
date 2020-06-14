#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jun 13, 2020

@authors: rafmacalaba
"""
# Import standard library
from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk
import backtrader as bts
from urllib.request import urlopen
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
from tqdm import tqdm

# download lexicon

def get_bt_news(keyword=None, page_nums=None):
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
    """

    nltk.download('vader_lexicon', quiet=True) #download vader lexicon

    # Check for keyword
    if keyword is None:
        print("keyword is set to None, please type in keyword or company name that you wanted to scrape e.g jollibee, facebook etc.")
        raise TypeError
    if page_nums is None:
        page_nums = 1
        print("no page numbers indicated, setting this variable to 1")

    date_sentiments = {}
    sia = SentimentIntensityAnalyzer()

    for i in tqdm(range(1, page_nums+1)):
        page = urlopen(f"https://www.businesstimes.com.sg/search/{keyword}?page={str(i)}").read()
        soup = BeautifulSoup(page, features="html.parser")
        posts = soup.findAll("div", {"class": "media-body"})
        for post in posts:
            time.sleep(1)
            url = post.a['href']
            date = post.time.text
            try:
                link_page = urlopen(url).read()
            except:
                url = url[:-2]
                link_page = urlopen(url).read()
            link_soup = BeautifulSoup(link_page, features="lxml")
            sentences = link_soup.findAll("p")
            passage = ""
            for sentence in sentences:
                passage += sentence.text
            sentiment = sia.polarity_scores(passage)['compound']
            date_sentiments.setdefault(date, []).append(sentiment)

    date_sentiment = {}

    for k,v in date_sentiments.items():
        date_sentiment[datetime.strptime(k, '%d %b %Y').date() + timedelta(days=1)] = round(sum(v)/float(len(v)),3)

    return date_sentiment