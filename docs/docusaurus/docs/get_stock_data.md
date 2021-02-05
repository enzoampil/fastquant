---
id: get_stock_data
title: get_stock_data
---

## Parameters

**symbol** : str
    Symbol of the stock in the PSE or Yahoo.
    You can refer to these links:
    PHISIX: https://www.pesobility.com/stock
    YAHOO: https://www.nasdaq.com/market-activity/stocks/screener?exchange=nasdaq

**start_date** : str
    Starting date (YYYY-MM-DD) of the period that you want to get data on

**end_date** : str
    Ending date (YYYY-MM-DD) of the period you want to get data on

**source** : str
    First source to query from ("pse", "yahoo"). If the stock is not found in the first source, the query is run on the other source.

**format** : str
    Format of the output data

## Returns

**pandas.DataFrame**
    Stock data (in the specified `format`) for the specified company and date range