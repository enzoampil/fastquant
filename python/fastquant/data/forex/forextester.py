import os
from pathlib import Path
import zipfile

import requests
import pandas as pd
from pandas import DataFrame

from fastquant.config import DATA_PATH

def get_forextester_data(symbol, start_date, end_date,  time_frame):
    allowed_forex_symbol_list = [
        'AUDJPY',
        'AUDUSD',
        'CHFJPY',
        'EURCAD',
        'EURCHF',
        'EURGBP',
        'EURJPY',
        'EURUSD',
        'GBPCHF',
        'GBPJPY',
        'GBPUSD',
        'NZDJPY',
        'NZDUSD',
        'USDCAD',
        'USDJPY',
        'USDCHF',
        'XAGUSD',
        'XAUUSD'
    ]
    if symbol not in allowed_forex_symbol_list:
        raise ValueError('your symbol is not supported by forextester')

    print('start downloading forex data zip file...')
    res = requests.get(f'http://www.forextester.com/templates/data/files/{symbol}.zip', stream=True)
    with open(Path(DATA_PATH, f'{symbol}.zip'), 'wb') as forex_zip_file:
        for chunk in res.iter_content(chunk_size=1024):
            forex_zip_file.write(chunk)

    zip_file = zipfile.ZipFile(Path(DATA_PATH, f'{symbol}.zip'))
    zip_file.extractall(Path(DATA_PATH))

    tmp_dict = {
        'dt':[],
        'minute':[],
        'open':[],
        'high':[],
        'low':[],
        'close':[]
    }
    with open(Path(DATA_PATH, f'{symbol}.txt')) as forex_txt_file:
        for line in forex_txt_file:
            symbol, data, minute, open_price, high, low, close, vol = line.strip().split(',')
            if data == '<DTYYYYMMDD>':
                continue
            tmp_dict['dt'].append(data+minute)
            tmp_dict['open'].append(open_price)
            tmp_dict['high'].append(high)
            tmp_dict['low'].append(low)
            tmp_dict['close'].append(close)

    forex_dataframe = DataFrame(tmp_dict, columns=list(tmp_dict.keys()))
    forex_dataframe = forex_dataframe.reset_index()
    forex_dataframe["dt"] = pd.to_datetime(forex_dataframe.dt)
    return forex_dataframe.set_index('dt')



def shape_data_from_1min_to_other(df, time_frame):
    if time_frame not in ["M1", "M5", "M15", "H1", "D1", "W1"]:
        raise ValueError('time_frame must in this list:["M1", "M5", "M15", "H1", "D1", "W1"]')

    tmp_dict = {
        'dt': [],
        'minute': [],
        'open': [],
        'high': [],
        'low': [],
        'close': []
    }

    if time_frame == 'M1':
        return df
    elif time_frame == 'M5':
        pass
    elif time_frame == 'M15':
        tmp_datetime = None
        tmp_hour = None
        tmp_minute = None
        tmp_open = None
        tmp_high = None
        tmp_low = None

        for index, row in df.iterrows():
            if tmp_open is None:
                tmp_open = row['open']
                tmp_high = row['high']
                tmp_low = row['low']
                tmp_datetime = row['dt']
                tmp_hour = row['dt'].hour
                tmp_minute = row['dt'].minute
            else:
                if row['high']>tmp_high:
                    tmp_high = row['high']
                if row['low']<tmp_low:
                    tmp_low = row['low']

                if tmp_minute<15:
                    if df[index+1:index+2]['dt'].values[0].minute >=15 and df[index+1:index+2]['dt'].values[0].hour == tmp_hour:
                        tmp_dict['dt'] = tmp_datetime
                        tmp_dict['open'] = tmp_open
                        tmp_dict['high'] = tmp_high
                        tmp_dict['low'] = tmp_low
                        tmp_dict['close'] = row['close']
                        tmp_datetime = None
                        tmp_hour = None
                        tmp_minute = None
                        tmp_open = None
                        tmp_high = None
                        tmp_low = None
                elif 15<tmp_minute<30:
                    pass
                elif 30<tmp_minute<45:
                    pass
                elif tmp_minute>45:
                    pass
                else:
                    pass

    else:
        pass