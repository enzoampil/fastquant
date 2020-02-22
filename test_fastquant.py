import pandas as pd
from fastquant import (
    get_disclosures_df,
    get_pse_data,
    get_yahoo_data,
    get_stock_data,
    get_company_disclosures,
    pse_data_to_csv,
)

PHISIX_SYMBOL = "JFC"
YAHOO_SYMBOL = "GOOGL"
DATE_START = "2018-01-01"
DATE_END = "2019-01-01"


def test_get_disclosures_df():
    df_dict = get_disclosures_df(PHISIX_SYMBOL, DATE_START, DATE_END)
    dfd = df_dict["D"]
    dfe = df_dict["E"]
    assert isinstance(dfd, pd.DataFrame)
    assert isinstance(dfe, pd.DataFrame)


def test_get_pse_data():
    stock_df = get_pse_data(PHISIX_SYMBOL, DATE_START, DATE_END)
    assert isinstance(stock_df, pd.DataFrame)


def test_get_yahoo_data():
    stock_df = get_yahoo_data(YAHOO_SYMBOL, DATE_START, DATE_END)
    assert isinstance(stock_df, pd.DataFrame)


def test_get_stock_data():
    stock_df = get_stock_data(PHISIX_SYMBOL, DATE_START, DATE_END)
    assert isinstance(stock_df, pd.DataFrame)

    stock_df = get_stock_data(YAHOO_SYMBOL, DATE_START, DATE_END)
    assert isinstance(stock_df, pd.DataFrame)


def test_get_company_disclosures():
    company_disclosures_df = get_company_disclosures(PHISIX_SYMBOL)
    assert isinstance(company_disclosures_df, pd.DataFrame)
