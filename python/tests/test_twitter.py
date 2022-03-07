from fastquant.data.web.twitter import tweepy_api

import os
import sys

import pytest

sys.path.append(os.path.abspath(os.path.join("..", "fastquant")))


def test_get_twitter_sentiment():
    # You need to put your own Twitter API Credentials here
    consumer_key = ""
    consumer_secret = ""
    access_token = ""
    access_secret = ""

    api = tweepy_api(consumer_key, consumer_secret, access_token, access_secret)
    assert api is not None
    # account_list = ["2TradeAsia", "colfinancial"]
    # sentiment_dict = get_twitter_sentiment('$ALI', api, '2020-06-14', account_list)
    # assert isinstance(sentiment_dict, dict)
