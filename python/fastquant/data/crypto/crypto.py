from datetime import datetime, timedelta
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

DATETIME_FORMAT = {"daily": "%Y-%m-%d", "intraday": "%Y-%m-%d %H:%M:%S"}


def unix_time_millis(date):
    # epoch = datetime.utcfromtimestamp(0)

    # value will only have : if the date passed is intraday
    dt_format = DATETIME_FORMAT["intraday"] if ":" in date else DATETIME_FORMAT["daily"]
    dt = datetime.strptime(date, dt_format)
    # return int((dt - epoch).total_seconds() * 1000)
    return int(dt.timestamp() * 1000)


def get_crypto_data(
    ticker, start_date, end_date, time_resolution="1d", exchange="binance"
):
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
    dt_format = (
        DATETIME_FORMAT["intraday"]
        if "m" in time_resolution or "h" in time_resolution
        else DATETIME_FORMAT["daily"]
    )
    start_date_epoch = unix_time_millis(start_date)
    end_date_epoch = unix_time_millis(end_date)

    if exchange in CRYPTO_EXCHANGES:
        # Get the exchange we want to use from ccxt's exchange attributes
        ex = getattr(ccxt, exchange)({"verbose": False})

        # We're going to get data in batches, so want to know what the last record in the previous batch was
        previous_request_end_date_epoch = start_date_epoch

        # The time we want data from will shift each batch as well
        request_start_date_epoch = start_date_epoch

        # Variable to store our dataframe as we fill it out
        ohlcv_df = None

        while previous_request_end_date_epoch < end_date_epoch:
            # Pull the data from the exchange
            ohlcv_lol = ex.fetch_ohlcv(
                ticker, time_resolution, since=request_start_date_epoch
            )
            # Convert it to a dataframe
            current_request_df = pd.DataFrame(
                ohlcv_lol,
                columns=["dt", "open", "high", "low", "close", "volume"],
            )

            if current_request_df.size == 0:
                # If we got no results (which happens sometimes, like on binance for ETH/BTC when requesting 2018-02-08)
                # then step forward to the next day
                request_start_date_epoch += (
                    int(timedelta(days=1).total_seconds()) * 1000
                )
                # Make sure we're at the start of that day
                request_start_date_epoch = unix_time_millis(
                    pd.to_datetime(request_start_date_epoch, unit="ms").strftime(
                        dt_format
                    )
                )
                previous_request_end_date_epoch = request_start_date_epoch - 1
                continue

            if ohlcv_df is None:
                # We don't have a dataframe yet, so start with this
                ohlcv_df = current_request_df
            else:
                # Trim any overlap with the new results
                ohlcv_df = ohlcv_df[ohlcv_df.dt < current_request_df.dt.min()]
                # Append the results to what we have so far
                # ohlcv_df = ohlcv_df.append(current_request_df)
                ohlcv_df = pd.concat([ohlcv_df, current_request_df], ignore_index=True)

            # Get the last entry timestamp after we've retrieved (or attempted to) additional records
            current_request_end_date_epoch = int(ohlcv_df.dt.max())

            if current_request_end_date_epoch <= previous_request_end_date_epoch:
                # We haven't gained any additional records, so there's no point in further requests
                # Let's mark this for the data end date, mostly so both end_date and end_date_epoch will be
                # in sync in case someone in future uses them in code futher down and to ensure the loop bails
                end_date_epoch = current_request_end_date_epoch
                # Update the actual end date so that the stored value will reflect the actual end
                end_date = pd.to_datetime(end_date_epoch, unit="ms")
                # The loop would exit based on the end_date_epoch value, but we'll save that check occuring
                break
            else:
                # We've gained some more records, so let's place another request (unless we're past the end, but our loop will catch that without checking here)
                # The next request should start a millisecond after this one ended
                request_start_date_epoch = current_request_end_date_epoch + 1
                # This request's end date should now be set as current for the next loop
                previous_request_end_date_epoch = current_request_end_date_epoch

        if ohlcv_df is not None:
            # Convert the unix timestampe to datetime
            ohlcv_df["dt"] = pd.to_datetime(ohlcv_df["dt"], unit="ms")
            # Trim off any records which were returned beyond the end
            ohlcv_df = ohlcv_df[ohlcv_df.dt <= end_date]
            # Save input parameters into dataframe
            ohlcv_df.start_date = start_date
            ohlcv_df.end_date = end_date
            ohlcv_df.symbol = ticker
            ohlcv_df = ohlcv_df.set_index("dt")

        return ohlcv_df
    else:
        raise NotImplementedError(
            "The exchange " + exchange + " is not yet supported. Available exchanges: "
            ", ".join(CRYPTO_EXCHANGES)
        )
