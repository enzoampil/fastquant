# fastquant :nerd_face:
[![Build Status](https://travis-ci.com/enzoampil/fastquant.svg?branch=master)](https://travis-ci.com/enzoampil/fastquant)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
[![License: GPL v3](https://img.shields.io/badge/license-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

## Easiest way to access and analyze Philippine stock data

**fastquant** allows you easily access stock data with as few as 2 lines of python code. Its goal is to promote data driven investments by making quantitative analysis in finance accessible to everyone.

## Features
1. Easy access to *historical* Philippine stock data
2. Templates for backtesting trading strategies on Philippine stocks

## Installation
```
pip install fastquant
```

## Get Philippine stock data
Accessed via the [phisix](http://phisix-api2.appspot.com/) API
```
from fastquant import get_pse_data
df = get_pse_data("JFC", "2018-01-01", "2019-01-01")
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

## Analyze with a simple moving average (SMA) trading strategy
```
ma30 = df.close.rolling(30).mean()
close_ma30 = pd.concat([df.close, ma30], axis=1).dropna()
close_ma30.columns = ['Closing Price', 'Simple Moving Average (30 day)']

close_ma30.plot(figsize=(10, 6))
plt.title("Daily Closing Prices vs 30 day SMA of JFC\nfrom 2018-01-01 to 2019-01-01", fontsize=20)
```
![](daily_closing_sma30.png)

## Backtesting templates
Using the [backtrader](https://github.com/backtrader/backtrader) framework

### Relative strength index (RSI) trading strategy (14 day window)
Daily Jollibee prices from 2017-01-01 to 2019-01-01
```
python examples/jfc_rsi.py
```
![](examples/jfc_rsi.png)

### Min max support resistance trading strategy (30 day window)
Daily Jollibee prices from 2017-01-01 to 2019-01-01
```
python examples/jfc_support_resistance.py
```
![](examples/jfc_support_resistance.png)
