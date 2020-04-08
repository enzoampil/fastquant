# fastquant :nerd_facs
[![Build Status](https://travis-ci.com/enzoampil/fastquant.svg?branch=master)](https://travis-ci.com/enzoampil/fastquant)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
[![License: GPL v3](https://img.shields.io/badge/license-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

## Bringing backtesting to the mainstream

**fastquant** allows you to easily backtest investment strategies with as few as 3 lines of python code. Its goal is to promote data driven investments by making quantitative analysis in finance accessible to everyone.

## Features
1. Easily access historical stock data
2. Backtest trading strategies with only 3 lines of code

<sup>`*` - Both Yahoo Finance and Philippine stock data data are accessible straight from fastquant<sup>

## Installation
```
pip install fastquant
```

## Get stock data
All symbols from [Yahoo Finance](https://finance.yahoo.com/) and Philippine Stock Exchange ([PSE](https://www.pesobility.com/stock)) are accessible via `get_stock_data`.

```
from fastquant import get_stock_data
df = get_stock_data("JFC", "2018-01-01", "2019-01-01")
print(df.head())

#           dt  close   volume
#   2019-01-01  293.0   181410
#   2019-01-02  292.0  1665440
#   2019-01-03  309.0  1622480
#   2019-01-06  323.0  1004160
#   2019-01-07  321.0   623090
```

*Note: Symbols from Yahoo Finance will return closing prices in USD, while symbols from PSE will return closing prices in PHP*

## Backtest trading strategies

### Simple Moving Average Crossover (15 day MA vs 40 day MA)
Daily Jollibee prices from 2018-01-01 to 2019-01-01
```
from fastquant import backtest
backtest('smac', jfc, fast_period=15, slow_period=40)

# Starting Portfolio Value: 100000.00
# Final Portfolio Value: 102272.90
```
![](./docs/assets/smac_sample.png)
