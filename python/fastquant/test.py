from fastquant import get_yahoo_data, get_bt_news_sentiment, get_twitter_sentiment, tweepy_api


consumer_key = ''
consumer_secret = ''
access_token = ''
access_secret = ''

api = tweepy_api(consumer_key, consumer_secret, access_token, access_secret)

account_list = ['2TradeAsia', 'colfinancial']
sentiment = get_twitter_sentiment('$ALI', api, '2020-06-14', account_list)
print(sentiment)
