import pandas as pd
from fastquant import CompanyDisclosures, get_disclosures_df

PHISIX_SYMBOL = "JFC"
DATE_START = "2019-01-01"
DATE_END = "2019-04-12"


def test_company_diclosures_class():
    cd = CompanyDisclosures(
        symbol=PHISIX_SYMBOL, start_date=DATE_START, end_date=DATE_END
    )
    assert isinstance(cd.company_disclosures, pd.DataFrame)
    assert cd.company_disclosures.shape == (38, 7)
    assert cd.disclosure_tables["dfca1fdb569e514befdfc15ec263a54d"].shape == (
        6,
        2,
    )
    assert isinstance(cd.disclosure_tables, dict)


def test_get_disclosures_df():
    df_dict = get_disclosures_df(PHISIX_SYMBOL, DATE_START, DATE_END)
    dfd = df_dict["D"]
    dfe = df_dict["E"]
    assert isinstance(dfd, pd.DataFrame)
    assert isinstance(dfe, pd.DataFrame)
