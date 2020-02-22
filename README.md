# fastquant :nerd_face:
[![Build Status](https://travis-ci.com/enzoampil/fastquant.svg?branch=master)](https://travis-ci.com/enzoampil/fastquant)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
[![License: GPL v3](https://img.shields.io/badge/license-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

## Bringing data driven investments to the mainstream

**fastquant** allows you easily backtest investment strategies with as few as 3 lines of python code. Its goal is to promote data driven investments by making quantitative analysis in finance accessible to everyone.

## Features
1. Easily access historical stock data*
2. Backtest trading strategies with only 3 lines of code

`*` - Only Philippine stock data is available so far, but more countries will be covered soon with *Yahoo Finance* integration

## Installation
```
pip install fastquant
```

## Get stock data
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

## Plot daily closing prices
```
from matplotlib import pyplot as plt

df.close.plot(figsize=(10, 6))
plt.title("Daily Closing Prices of JFC\nfrom 2018-01-01 to 2019-01-01", fontsize=20)
```
![](daily_closing.png)

## Backtest trading strategies

### Simple Moving Average Crossover (15 day MA vs 40 day MA)
Daily Jollibee prices from 2018-01-01 to 2019-01-01
```
backtest('smac', jfc, fast_period=15, slow_period=40)
```
![](smac_sample.png)
