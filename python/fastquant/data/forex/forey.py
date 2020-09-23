#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np

# Import from config
from fastquant.config import DATA_FORMAT_COLS

# Import package
from fastquant.data.forex.forextester import get_forextester_data


def get_forex_data(symbol, start_date=None, end_date=None, source="forextester", time_frame='day'):
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
    time_frame : str
         time frame you want, support 1 minute,15 minutes,1 hour,1 day,1 week
         this parameter must one of them:["M1", "M5", "M15", "H1", "D1", "W1"]

    Returns
    -------
    pandas.DataFrame
        Forex data (in the specified `format`) for the specified company and date range
    """

    if source == "forextester":
        df = get_forextester_data(symbol, start_date, end_date, time_frame)
    else:
        raise Exception("Source must be either 'phisix' or 'yahoo'")

    return df
