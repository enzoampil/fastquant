import pandas as pd
import backtrader as bt
from pandas.api.types import is_numeric_dtype


from fastquant.config import DEFAULT_PANDAS


def initalize_data(
    data,
    strategy_name,
    symbol=None,
    data_class=None,
    sentiments=None,
    data_kwargs={},
    verbose=None,
):

    # Treat `data` as a path if it's a string; otherwise, it's treated as a pandas dataframe
    if isinstance(data, str):
        if verbose > 0:
            print("Reading path as pandas dataframe ...")
        # Rename dt to datetime
        data = pd.read_csv(data, header=0, parse_dates=["dt"])

    # Add dividend column in case it doesn't exist
    # This is utilized if `invest_div` is set to True in `backtest` `kwargs` (True by default)
    if "dividend" not in data.columns:
        data["dividend"] = 0

    if strategy_name == "sentiment":
        data = include_sentiment_score(data, sentiments)

    # If a `close` column exists but an `open` column doesn't, create a new `open` column with the same values as the `close` column
    # This is for easier handling of next day trades (w/ the assumption that next day open is equal to current day close)
    if "close" in data.columns and "open" not in data.columns:
        data["open"] = data.close.shift().values

    # If data has `dt` as the index and `dt` or `datetime` are not already columns, set `dt` as the first column
    # This means `backtest` supports the dataframe whether `dt` is the index or a column
    if len(set(["dt", "datetime"]).intersection(data.columns)) == 0:
        if data.index.name == "dt":
            data = data.reset_index()
        # If the index is a datetime index, set this as the datetime column
        elif isinstance(data.index, pd.DatetimeIndex):
            data.index.name = "dt"
            data = data.reset_index()

    # Rename "dt" column to "datetime" to match the formal alias
    data = data.rename(columns={"dt": "datetime"})
    data["datetime"] = pd.to_datetime(data.datetime)

    numeric_cols = [col for col in data.columns if is_numeric_dtype(data[col])]
    params_tuple = tuple(
        [
            (col, i)
            for i, col in enumerate(data.columns)
            if col in numeric_cols + ["datetime"]
        ]
    )
    default_cols = [c for c, _ in DEFAULT_PANDAS]
    non_default_numeric_cols = tuple(
        [col for col, _ in params_tuple if col not in default_cols]
    )

    # Use custom data class if input
    if data_class:

        class CustomData(data_class):
            """
            Data feed that includes all the columns in the input dataframe
            """

            # Need to make sure that the new lines don't overlap w/ the default lines already in PandasData
            lines = non_default_numeric_cols

            # automatically handle parameter with -1
            # add the parameter to the parameters inherited from the base class
            params = params_tuple + (("symbol", symbol),)

    else:

        class CustomData(bt.feeds.PandasData):
            """
            Data feed that includes all the columns in the input dataframe
            """

            # Need to make sure that the new lines don't overlap w/ the default lines already in PandasData
            lines = non_default_numeric_cols

            # automatically handle parameter with -1
            # add the parameter to the parameters inherited from the base class
            params = params_tuple + (("symbol", symbol),)

    data_format_dict = tuple_to_dict(params_tuple)

    pd_data = CustomData(
        dataname=data, symbol=symbol, **data_format_dict, **data_kwargs
    )

    return pd_data, data, data_format_dict


def include_sentiment_score(data, sentiments):

    # initialize series for sentiments
    senti_series = pd.Series(sentiments, name="sentiment_score", dtype=float)

    # join and reset the index for dt to become the first column
    data = data.merge(senti_series, left_index=True, right_index=True, how="left")
    data = data.reset_index()

    return data


def tuple_to_dict(tup):
    di = dict(tup)
    return di
