from datetime import datetime
import pandas as pd
import ccxt

# Only support top 6 listed on https://www.coingecko.com/en/exchanges for now
CRYPTO_EXCHANGES = [
    "binance",
    "coinbasepro",
    "bithumb",
    "kraken",
    "kucoin",
    "bitstamp",
]
# to add more just add more method names to the above
# list of supported exchanges according to the classes mentioned here: https://github.com/ccxt/ccxt/tree/master/python/ccxt


def unix_time_millis(date):
    # epoch = datetime.utcfromtimestamp(0)
    dt = datetime.strptime(date, "%Y-%m-%d")
    # return int((dt - epoch).total_seconds() * 1000)
    return int(dt.timestamp() * 1000)


def get_crypto_data(ticker, start_date, end_date, time_resolution="1d", exchange="binance"):
    """
    Get crypto data in OHLCV format

    Parameters
    ----------
    ticker : str
        List of ticker symbols here: https://coinmarketcap.com/exchanges/binance/
    start_date, end_date : str
        date in YYYY-MM-DD format
    time_resolution : str
       resolutions: '1w', '1d' (default), '1h', '1m'
    exchange : str
       market exchanges: 'binance' (default), 'coinbasepro', 'bithumb', 'kraken', 'kucoin', 'bitstamp'
    """
    start_date_epoch = unix_time_millis(start_date)

    if exchange in CRYPTO_EXCHANGES:
        ex = getattr(ccxt, exchange)({"verbose": False})
        ohlcv_lol = ex.fetch_ohlcv(ticker, time_resolution, since=start_date_epoch)
        ohlcv_df = pd.DataFrame(
            ohlcv_lol, columns=["dt", "open", "high", "low", "close", "volume"]
        )
        ohlcv_df["dt"] = pd.to_datetime(ohlcv_df["dt"], unit="ms")
        ohlcv_df = ohlcv_df[ohlcv_df.dt <= end_date]
        # Save input parameters into dataframe
        ohlcv_df.start_date = start_date
        ohlcv_df.end_date = end_date
        ohlcv_df.symbol = ticker
        return ohlcv_df.set_index("dt")
    else:
        raise NotImplementedError(
            "The exchange "
            + exchange
            + " is not yet supported. Available exchanges: "
            ", ".join(CRYPTO_EXCHANGES)
        )
