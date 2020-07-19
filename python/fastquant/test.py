from fastquant import get_yahoo_data, get_bt_news_sentiment, get_twitter_sentiment, tweepy_api
import pandas as pd


# data = get_yahoo_data("TSLA", "2020-01-01", "2020-07-04")
# sentiments = get_bt_news_sentiment(keyword="tesla", page_nums=3)
# print(sentiments)

consumer_key = 'O75w6fyBeXvKTT7PoH4OpGVMP'
consumer_secret = '6l0cdPqlGaO9t2ymnjYwjatvBjBtrqqXIgY6jSnBYHmA3w49rA'
access_token = '3305141232-JzoSXEQclgfOjI80eVWIwio8mQtWNC4vA1W5kTm'
access_secret = 'vKw5Oigm0I78OQQRMDIsZWa9ccjBqkJCOIM7aPjXHq2EV'

api = tweepy_api(consumer_key, consumer_secret, access_token, access_secret)

account_list = ['colfinancial']
sentiment = get_twitter_sentiment('$URC', api, '2020-05-14', account_list)
print(sentiment)
