from fastquant import get_yahoo_data, get_bt_news_sentiment, get_twitter_sentiment, tweepy_api


consumer_key = ''
consumer_secret = ''
access_token = ''
access_secret = ''

api = tweepy_api(consumer_key, consumer_secret, access_token, access_secret)

account_list = ['colfinancial']
sentiment = get_twitter_sentiment('$URC', api, '2020-05-14', account_list)
print(sentiment)
