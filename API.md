# backtest
Available parameters
* `strategy` : str or an instance of `fastquant.strategies.base.BaseStrategy`
        see list of accepted strategy keys below
* `data` : pandas.DataFrame
      dataframe with at least close price indexed with time
* `commission` : float
      commission per transaction [0, 1] (default 0.0075)
* `init_cash` : float
      initial cash (currency implied from `data`) (default 100000)
* `plot` : bool
      show plot backtrader (disabled if `strategy`=="multi")
* `verbose` : int
      Verbose can take values: [0, 1, 2, 3], with increasing levels of verbosity (default=1).
* `sort_by` : str
      sort result by given metric (default='rnorm')
* `sentiments` : pandas.DataFrame
      df of sentiment [0, 1] indexed by time (applicable if `strategy`=='senti')
* `strats` : dict
      dictionary of strategy parameters (applicable if `strategy`=='multi')
* `return_history` : bool
      return history of transactions (i.e. buy and sell timestamps) (default=False)
* `return_plot`: bool
      return the plot (if you want to save the plot) (default=False)
* `channel` : str
      Channel to be used for notifications - e.g. "slack" (default=None)
* `symbol` : str
      Symbol to be referenced in the channel notification if not None (default=None)
* `allow_short` : bool
      Whether to allow short selling, with max set as `short_max` times the portfolio value (default=False)
* `short_max` : float
      The maximum short position allowable as a ratio relative to the portfolio value at that time point (default=1.5)
* `figsize` : tuple
      The size of the figure to be displayed at the end of the backtest (default=(30, 15))
* `data_class` : bt.feed.DataBase
      Custom backtrader database to be used as a parent class instead bt.feed. (default=None)
* `data_kwargs` : dict
      Datafeed keyword arguments (empty dict by default)
## Strategies
List of accepted strategy keys are
| Strategy | Alias | Parameters |
| --- | --- | --- |
| Relative Strength Index (RSI) | rsi | `rsi_period`, `rsi_upper`,  `rsi_lower` |
| Simple moving average crossover (SMAC) | smac | `fast_period`, `slow_period` |
| Exponential moving average crossover (EMAC) | emac | `fast_period`, `slow_period` |
| Moving Average Convergence Divergence (MACD) | macd | `fast_perod`, `slow_upper`, `signal_period`, `sma_period`, `sma_dir_period` |
| Bollinger Bands | bbands | `period`, `devfactor` |
| Buy and Hold | buynhold | `N/A` |
| Sentiment Strategy | sentiment | `keyword` , `page_nums`, `senti` |
| Custom Prediction Strategy | custom | `upper_limit`, `lower_limit`, `custom_column` |
| Custom Ternary Strategy | ternary | `buy_int`, `sell_int`, `custom_column` |
## Examples
### Return history
```python
from fastquant import backtest
res, hist = backtest(..., return_history=True)
```
### Return plot
```python
from fastquant import backtest
res, plot = backtest(..., return_plot=True)

# Save plot
plot.savefig('example.png')
```

### Return history and plot
```python
from fastquant import backtest
res, hist, plot = backtest(..., return_history=True, return_plot=True,
```
