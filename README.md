# pse-quant
Framework for applying quantitative finance on PSE data with the goal of promoting data driven investments in the Philippines

# Setup
```
git clone https://github.com/enzoampil/pse-quant.git
cd pse-quant
virtualenv env
source env/bin/activate
pip install -r requirements.txt
```

# Current features:
## Easy access to stock related data (OHLCV)
1. Basic daily price features
    - Date
    - Open
    - High
    - Low
    - Close
    - Value
 2. Company disclosures (WIP)
 3. Company related tweets (WIP)

 # Future features
## Processed text information with NLP
1. Disclosure reports summarized in structured tabular form
2. Summary statistics from tweets

## Easy to use API for back testing trading strategies
1. Example scripts for backtesting on different companies with different trading strategies
2. High level functions for simple backtesting
