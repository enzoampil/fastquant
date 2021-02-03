---
id: get_crypto_data
title: get_crypto_data
---

Get crypto data in OHLCV format

## Parameters

**ticker** : str
    List of ticker symbols here: https://coinmarketcap.com/exchanges/binance/

**start_date**, **end_date** : str
    date in YYYY-MM-DD format

**time_resolution** : str
   resolutions: '1w', '1d' (default), '1h', '1m'

**exchange** : str
   market exchanges: 'binance' (default), 'coinbasepro', 'bithumb', 'kraken', 'kucoin', 'bitstamp'

## Returns

**pandas.DataFrame**
    Stock data (in the specified `format`) for the specified company and date range