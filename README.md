# psequant
[![Build Status](https://travis-ci.com/enzoampil/psequant.svg?token=UHxLpqqapxjVVa2vsreG&branch=master)](https://travis-ci.com/enzoampil/psequant)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
[![License: GPL v3](https://img.shields.io/badge/license-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
Framework for applying quantitative finance on PSE data with the goal of promoting data driven investments in the Philippines

## Getting started
```
from pse_pipeline import get_pse_data
df = get_pse_data("JFC", "2018-01-01", "2019-01-01")
print(df.head())

#             open   high    low  close        value
#dt                                                 
#2018-01-03  253.4  256.8  253.0  255.4  190253754.0
#2018-01-04  255.4  255.4  253.0  255.0  157152856.0
#2018-01-05  255.6  257.4  255.0  255.0  242201952.0
#2018-01-08  257.4  259.0  253.4  256.0  216069242.0
#2018-01-09  256.0  258.0  255.0  255.8  250188588.0
```
## Setup
```
git clone https://github.com/enzoampil/psequant.git
cd psequant
virtualenv env
source env/bin/activate
pip install -r requirements.txt
```
## Run tests
```
pytest test_pse_pipeline.py
```
## Current features:
### Easy access to stock related data (OHLCV)
1. Basic daily price features
    - Date
    - Open
    - High
    - Low
    - Close
    - Value
2. Company disclosures (WIP)

## Future features
### Processed text information with NLP
1. Disclosure reports summarized in structured tabular form
2. Summary statistics from tweets
3. Company related tweets (WIP)

### Easy to use API for back testing trading strategies
1. Example scripts for backtesting on different companies with different trading strategies
2. High level functions for simple backtesting
    - RSI
    - Support resistance
    - Bollinger bands
    - MACD
