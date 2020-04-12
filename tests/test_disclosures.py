import pandas as pd
from fastquant import CompanyDisclosures

SYMBOL = "JFC"
START_DATE = "1-1-2019"
END_DATE = "4-12-2020"


def test_company_diclosures():
    cd = CompanyDisclosures(
        symbol=SYMBOL, start_date=START_DATE, end_date=END_DATE
    )
    print(cd)
    assert isinstance(cd.company_disclosures, pd.DataFrame)
    assert cd.company_disclosures.shape == (38, 7)
    assert cd.disclosure_tables["dfca1fdb569e514befdfc15ec263a54d"].shape == (
        6,
        2,
    )
    assert isinstance(cd.disclosure_tables, dict)
