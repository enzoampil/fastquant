# psequant
[![Build Status](https://travis-ci.com/enzoampil/psequant.svg?token=UHxLpqqapxjVVa2vsreG&branch=master)](https://travis-ci.com/enzoampil/psequant)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
[![License: GPL v3](https://img.shields.io/badge/license-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

## A framework for applying quantitative finance on PSE data

## Goal: 

To  promote data driven investments in the Philippines

## Objectives:

1. To democratize access to PSE data

2. To make it easy to backtest trading strategies

## Setup
```
git clone https://github.com/enzoampil/psequant.git
cd psequant
virtualenv env
source env/bin/activate
pip install -r requirements.txt
```

## Get stock data from PSE
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

## Backtesting examples (using [backtrader](https://github.com/backtrader/backtrader))

### Relative Strength Index Strategy (14 day window)
Daily Jollibee prices from 2017-01-01 to 2019-01-01
```
python examples/jfc_rsi.py
```
![](examples/jfc_rsi.png)

### Min Max Support Resistance Strategy (30 day window)
Daily Jollibee prices from 2017-01-01 to 2019-01-01
```
python examples/jfc_support_resistance.py
```
![](examples/jfc_support_resistance.png)

## Run tests
```
pytest test_pse_pipeline.py
```
