import pandas as pd
from pse_pipeline import get_disclosures_df, get_pse_data, get_company_disclosures, pse_data_to_csv

SYMBOL = 'JFC'
DATE_START = '2010-01-01'
DATE_END = '2019-01-01'

def test_get_disclosures_df():
    df_dict = get_disclosures_df(SYMBOL, DATE_START, DATE_END)
    dfd = df_dict['D']
    dfe = df_dict['E']
    assert isinstance(dfd, pd.DataFrame)
    assert isinstance(dfe, pd.DataFrame)

def test_get_pse_data():
    stock_df = get_pse_data(SYMBOL, DATE_START, DATE_END)
    assert isinstance(stock_df, pd.DataFrame)

def test_get_company_disclosures():
    company_disclosures_df = get_company_disclosures(SYMBOL)
    assert isinstance(company_disclosures_df, pd.DataFrame)
    