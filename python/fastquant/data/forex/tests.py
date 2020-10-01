import pickle
import time

from fastquant.data.forex.forextester import *


def get_forex_data_to_pickle(symbol, size):
    res_dict = get_forextester_data(symbol)[0:size]
    with open(f'{symbol}_pickle.pickle', 'wb') as file:
        pickle.dump(res_dict, file, True)


def read_forex_data_from_pickle(symbol):
    with open(f'{symbol}_pickle.pickle', 'rb') as file:
        df = pickle.load(file)
    return df


def test_shape_data_from_1min_to_other(df):
    return shape_data_from_1min_to_other(df, time_frame='D1')


def gen_candle_chart(df, start_time=None, end_time=None):
    import mplfinance as mpf
    reformatted_data = dict()
    reformatted_data['Date'] = []
    reformatted_data['Open'] = []
    reformatted_data['High'] = []
    reformatted_data['Low'] = []
    reformatted_data['Close'] = []

    for index, row in df.iterrows():
        reformatted_data['Date'].append(row['dt'])
        reformatted_data['Open'].append(row['open'])
        reformatted_data['High'].append(row['high'])
        reformatted_data['Low'].append(row['low'])
        reformatted_data['Close'].append(row['close'])

    pdata = pd.DataFrame.from_dict(reformatted_data)
    pdata.set_index('Date', inplace=True)
    if start_time:
        pdata = pdata.loc[start_time:end_time, :]
    mpf.plot(pdata, type='candle')

