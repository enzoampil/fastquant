import pandas as pd
from fastquant import (
    get_pse_data,
    get_yahoo_data,
    get_stock_data,
    get_crypto_data,
    pse_data_to_csv,
)

PHISIX_SYMBOL = "JFC"
CRYPTO_SYMBOL = "BTC/USDT"
MSFT_SYMBOL = "MSFT"
YAHOO_SYMBOL = "GOOGL"
DATE_START = "2018-01-01"
DATE_END = "2019-01-01"
MSFT_SYMBOL_START = "2020-10-01"
MSFT_SYMBOL_STOP = "2020-12-31"


def test_get_pse_data():
    stock_df = get_pse_data(PHISIX_SYMBOL, DATE_START, DATE_END, format="c")
    assert isinstance(stock_df, pd.DataFrame)

# Unused functions which haven't been tested since newest yfinance update
# def test_get_yahoo_data():
#     stock_df = get_yahoo_data(YAHOO_SYMBOL, DATE_START, DATE_END)
#     assert isinstance(stock_df, pd.DataFrame)

# def test_get_yahoo_data_dividend():
#     stock_df = get_yahoo_data(
#         MSFT_SYMBOL, MSFT_SYMBOL_START, MSFT_SYMBOL_STOP, dividends=True
#     )
#     assert isinstance(stock_df, pd.DataFrame)


def test_get_stock_data():
    # Test w/ respective sources
    stock_df = get_stock_data(PHISIX_SYMBOL, DATE_START, DATE_END, source="phisix")
    assert isinstance(stock_df, pd.DataFrame)

    # stock_df = get_stock_data(YAHOO_SYMBOL, DATE_START, DATE_END, source="yahoo")
    # assert isinstance(stock_df, pd.DataFrame)

    # Test getting yahoo when (default) phisix fails on a non PSE SYMBOL
    stock_df = get_stock_data(YAHOO_SYMBOL, DATE_START, DATE_END)
    assert isinstance(stock_df, pd.DataFrame)


def test_get_crypto_data():
    # test that multiple exchanges work
    from fastquant import CRYPTO_EXCHANGES

    exchange_pairs = {
        "binance": "BTC/BUSD",
        "coinbasepro": "BTC/USD",
        "bithumb": "XRP/KRW",
        "kraken": "BTC/USD",
        "kucoin": "BTC/USDT",
        "bitstamp": "BTC/USD",
    }

    for ex in CRYPTO_EXCHANGES:
        # Github actions for fastquant uses US server, which doesn't have access to binance
        # Using binance elsewhere works without any issues
        if ex == 'binance':
            continue
        crypto_df = get_crypto_data(
            exchange_pairs[ex], DATE_START, DATE_END, exchange=ex
        )
        assert isinstance(crypto_df, pd.DataFrame), ex
