import pandas as pd
from fastquant import DisclosuresPSE, DisclosuresInvestagrams

SYMBOL = "JFC"
START_DATE = "1-1-2020"
END_DATE = "2-1-2020"


# def test_diclosures_pse():
#     dp = DisclosuresPSE(
#         symbol=SYMBOL, start_date=START_DATE, end_date=END_DATE
#     )
#     assert isinstance(dp.company_disclosures, pd.DataFrame)
#     assert dp.company_disclosures.shape == (10, 7)
#     assert isinstance(dp.disclosure_tables, dict)
#     assert dp.disclosure_tables["a5df62b1a9558fe60de8473cebbd6407"].shape == (
#         6,
#         2,
#     )


# def test_disclosures_investagrams():
#     di = DisclosuresInvestagrams("JFC", "2020-01-01", "2020-04-01")
#     dfd = di.disclosures_df["D"]
#     dfe = di.disclosures_df["E"]
#     assert isinstance(dfd, pd.DataFrame)
#     assert isinstance(dfe, pd.DataFrame)
