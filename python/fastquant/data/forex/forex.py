#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np

# Import from config
from fastquant.config import DATA_FORMAT_COLS

# Import package
from fastquant.data.forex.forextester import get_forextester_data, get_local_data


def get_forex_data(symbol, start_date=None, end_date=None, source="forextester", period='D1', read_from_local=False):
    """Returns pricing data for a specified forex pair.

    Parameters
    ----------
    symbol : str
        Symbol of the forex in the forextester.
        https://forextester.com/data/datasources
    start_date : str
        Starting date (YYYY-MM-DD) of the period that you want to get data on
        in most cases we need more wide time period to test strategy, so keep this to None
    end_date : str
        Ending date (YYYY-MM-DD) of the period you want to get data on
        in most cases we need more wide time period to test strategy, so keep this to None
    source : str
         Source of forex history data
    period : str
         time period you want, support 1 minute,15 minutes,1 hour,1 day,1 week
         this parameter must one of them:["M1", "M15", "H1", "D1", "W1"]
    read_from_local : bool
        if this parameter set False, method get data from online
        if set it to True, method get data from local pickle file, faster than set it to False

    Returns
    -------
    pandas.DataFrame
    """

    if source == "forextester":
        if read_from_local is False:
            df = get_forextester_data(symbol, start_date, end_date, period)
        else:
            df = get_local_data(symbol, start_date, end_date, period)
    else:
        raise Exception("Source must be forextester")

    return df
