#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import tweepy
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from datetime import date, datetime
import pandas as pd


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


def get_twitter_sentiment(stock_code, twitter_auth, start_date, twitter_accounts=None):
    """
    This function scrapes twitter data based on stock code and twitter accounts specified
    Parameters
    ----------
    stock_code : str
        The stock code you wanted to scrape from Twitter
    twitter_auth : obj
         Authenticated tweepy.API object
    start_date : str
        Starting date (YYYY-MM-DD) of the period that you want to get twitter data on
    twitter_accounts : list
        List of twitter account names you want to scrape from
    Returns
    ----------
    date_sentiments: dict
        The dictionary output of the scraped data in form of {date: sentiment score}
    """
    year, month, day = map(int, start_date.split(sep="-"))
    start_date = date(year, month, day)

    stock_code = stock_code.lstrip("$")

    # Empty list to store the user tweets
    usertweets = []

    sia = SentimentIntensityAnalyzer()

    if twitter_accounts is None or len(twitter_accounts) == 0:
        raise Exception("You don't have any twitter accounts specified.")
    else:
        for acc in twitter_accounts:
            print(f"Scraping ${stock_code} tweets from {acc}")
            cursor = tweepy.Cursor(
                twitter_auth.user_timeline,
                id=acc,
                count=200,
                tweet_mode="extended",
            )

            item_counter = 1
            for item in cursor.pages():
                new_tweets = [
                    tweet
                    for tweet in item
                    if datetime.strptime(
                        str(tweet.created_at), "%Y-%m-%d %H:%M:%S"
                    ).date()
                    >= start_date
                    and stock_code in tweet.full_text
                ]

                print(f"{len(new_tweets)} tweets scraped from {acc}")

                if len(new_tweets) > 0 and item_counter == 1:
                    usertweets.extend(new_tweets)
                    item_counter += 1
                elif (
                    len(new_tweets) > 0
                    and item_counter != 1
                    and usertweets[-1].created_at.date != start_date
                ):
                    usertweets.extend(new_tweets)
                    item_counter += 1
                else:
                    break  # Break if 0 tweets

        tweet_df = pd.DataFrame([])

        if len(usertweets) > 0:
            tweet_created_at = [tweet.created_at for tweet in usertweets]
            tweet_text = [tweet.full_text for tweet in usertweets]

            tweet_df["tweet_created_at"] = tweet_created_at
            tweet_df["tweet_created_at"] = pd.to_datetime(
                tweet_df["tweet_created_at"]
            ).dt.date
            tweet_df["tweet"] = tweet_text
            tweet_df["sentiment_score"] = tweet_df["tweet"].apply(
                lambda tweet: sia.polarity_scores(tweet)["compound"]
            )

            tweet_avg_df = tweet_df.groupby("tweet_created_at", as_index=False).agg(
                {"sentiment_score": "mean"}
            )

            date_sentiment = dict(
                zip(
                    tweet_avg_df["tweet_created_at"],
                    tweet_avg_df["sentiment_score"],
                )
            )

            return date_sentiment

        else:
            raise Exception(
                f"No tweet found for {stock_code} starting from {start_date}."
            )
