import os
from pathlib import Path
import zipfile
import logging
import pickle

import requests
import pandas as pd
from pandas import DataFrame

from fastquant.config import DATA_PATH
from fastquant.data.stocks.pse import datestring_to_datetime

handler_format = logging.Formatter('%(asctime)s-%(name)s-%(levelname)s-%(message)s',datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger('forex_logger')
logger_handler = logging.StreamHandler()
logger_handler.setFormatter(handler_format)
logger.setLevel(logging.INFO)
logger.addHandler(logger_handler)


def get_forextester_data(symbol, start_date=None, end_date=None,  time_frame='D1'):
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

    if start_date is not None:
        start_date = datestring_to_datetime(start_date)
        end_date = datestring_to_datetime(end_date)

    logger.info(f'start downloading forex {symbol} data zip file...')
    file_size = 0
    res = requests.get(f'http://www.forextester.com/templates/data/files/{symbol}.zip', stream=True)
    with open(Path(DATA_PATH, f'{symbol}.zip'), 'wb') as forex_zip_file:
        for chunk in res.iter_content(chunk_size=4096):
            file_size+=4096
            if file_size<1048576:
                logger.info(f'download {round(file_size/1024)}KB')
            else:
                logger.info(f'download {round(file_size/1048576)}MB')
            forex_zip_file.write(chunk)
    logger.info('download success')
    zip_file = zipfile.ZipFile(Path(DATA_PATH, f'{symbol}.zip'))
    zip_file.extractall(Path(DATA_PATH))
    logger.info('unzip success')

    forex_dataframe = pd.read_csv(
        Path(DATA_PATH, f'{symbol}.txt'),
        dtype={'<DTYYYYMMDD>': str, '<TIME>': str, '<OPEN>': float, '<HIGH>': float, '<LOW>': float, '<CLOSE>': float}
    )
    logger.info('load txt success')
    del(forex_dataframe['<TICKER>'])
    del(forex_dataframe['<VOL>'])
    rename_list = [
        'date',
        'time',
        'open',
        'high',
        'low',
        'close',
    ]
    rename_dict = {
        '<DTYYYYMMDD>': 'date',
        '<TIME>': 'time',
        '<OPEN>': 'open',
        '<HIGH>': 'high',
        '<LOW>': 'low',
        '<CLOSE>': 'close',
    }
    forex_dataframe = forex_dataframe.rename(columns=rename_dict)[rename_list].drop_duplicates()
    logger.info('change column name success')
    forex_dataframe['dt'] = forex_dataframe['date'] + forex_dataframe['time']
    logger.info('sum date and time success')
    del(forex_dataframe['date'])
    del(forex_dataframe['time'])
    logger.info('start to transfer str datetime to pd.timestamp, this process requires 6 minutes on INTEL-9900k')
    forex_dataframe['dt'] = pd.to_datetime(forex_dataframe.dt)
    forex_dataframe = shape_data_from_1min_to_other(forex_dataframe, time_frame)
    logger.info('start write backup file to disk')
    with open(f'{symbol}_{time_frame}.pickle', 'wb') as df_file:
        pickle.dump(forex_dataframe, df_file, True)
    logger.info('all is done')
    if start_date is None:
        return forex_dataframe
    else:
        forex_dataframe = forex_dataframe[(forex_dataframe['dt'] >= start_date) & (forex_dataframe['dt'] <= end_date)]
        return forex_dataframe


def get_local_data(symbol, start_date=None, end_date=None,  time_frame='D1'):
    if start_date is not None:
        start_date = datestring_to_datetime(start_date)
        end_date = datestring_to_datetime(end_date)
    logger.info('start load pickle to memory')
    try:
        with open(f'{symbol}_{time_frame}.pickle', 'rb') as df_file:
            df = pickle.load(df_file)
    except Exception as e:
        raise FileNotFoundError('backup file not found, try get_forextester_data method first')
    if start_date is None:
        return df
    else:
        df = df[(df['dt'] >= start_date) & (df['dt'] <= end_date)]
        return df


def shape_data_from_1min_to_other(df, time_frame):
    if time_frame not in ["M1", "M15", "H1", "D1", "W1"]:
        raise ValueError('time_frame must in this list:["M1", "M15", "H1", "D1", "W1"]')

    tmp_dict = {
        'dt': [],
        'open': [],
        'high': [],
        'low': [],
        'close': []
    }

    if time_frame == 'M1':
        return df
    elif time_frame == 'M15':
        tmp_datetime = None
        tmp_hour = None
        tmp_minute = None
        tmp_open = None
        tmp_high = None
        tmp_low = None
        tmp_close = None

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
                tmp_close = row['close']

                if tmp_minute<15:
                    # continuous situation
                    if row['dt'].minute >=15 and row['dt'].hour == tmp_hour:
                        tmp_dict['dt'].append(tmp_datetime)
                        tmp_dict['open'].append(tmp_open)
                        tmp_dict['high'].append(tmp_high)
                        tmp_dict['low'].append(tmp_low)
                        tmp_dict['close'].append(tmp_close)
                        tmp_open = row['open']
                        tmp_high = row['high']
                        tmp_low = row['low']
                        tmp_datetime = row['dt']
                        tmp_hour = row['dt'].hour
                        tmp_minute = row['dt'].minute
                        continue
                    # discontinuous situation
                    elif row['dt'].hour != tmp_hour:
                        tmp_dict['dt'].append(tmp_datetime)
                        tmp_dict['open'].append(tmp_open)
                        tmp_dict['high'].append(tmp_high)
                        tmp_dict['low'].append(tmp_low)
                        tmp_dict['close'].append(tmp_close)
                        tmp_open = row['open']
                        tmp_high = row['high']
                        tmp_low = row['low']
                        tmp_datetime = row['dt']
                        tmp_hour = row['dt'].hour
                        tmp_minute = row['dt'].minute
                        continue
                    elif row['dt'].minute <15:
                        continue
                    else:
                        raise ValueError(f'M1 to M15 unkown error, start datetime:{tmp_hour} {tmp_minute} end datetime:{row["dt"].hour} {row["dt"].minute}')
                elif 15<=tmp_minute<30:
                    if row['dt'].minute >=30 and row['dt'].hour == tmp_hour:
                        tmp_dict['dt'].append(tmp_datetime)
                        tmp_dict['open'].append(tmp_open)
                        tmp_dict['high'].append(tmp_high)
                        tmp_dict['low'].append(tmp_low)
                        tmp_dict['close'].append(tmp_close)
                        tmp_open = row['open']
                        tmp_high = row['high']
                        tmp_low = row['low']
                        tmp_datetime = row['dt']
                        tmp_hour = row['dt'].hour
                        tmp_minute = row['dt'].minute
                        continue
                    elif row['dt'].hour != tmp_hour:
                        tmp_dict['dt'].append(tmp_datetime)
                        tmp_dict['open'].append(tmp_open)
                        tmp_dict['high'].append(tmp_high)
                        tmp_dict['low'].append(tmp_low)
                        tmp_dict['close'].append(tmp_close)
                        tmp_open = row['open']
                        tmp_high = row['high']
                        tmp_low = row['low']
                        tmp_datetime = row['dt']
                        tmp_hour = row['dt'].hour
                        tmp_minute = row['dt'].minute
                        continue
                    elif 15<row['dt'].minute <30:
                        continue
                    else:
                        raise ValueError(
                            f'M1 to M15 unkown error, start datetime:{tmp_hour} {tmp_minute} end datetime:{row["dt"].hour} {row["dt"].minute}')
                elif 30<=tmp_minute<45:
                    if row['dt'].minute >=45 and row['dt'].hour == tmp_hour:
                        tmp_dict['dt'].append(tmp_datetime)
                        tmp_dict['open'].append(tmp_open)
                        tmp_dict['high'].append(tmp_high)
                        tmp_dict['low'].append(tmp_low)
                        tmp_dict['close'].append(tmp_close)
                        tmp_open = row['open']
                        tmp_high = row['high']
                        tmp_low = row['low']
                        tmp_datetime = row['dt']
                        tmp_hour = row['dt'].hour
                        tmp_minute = row['dt'].minute
                    elif row['dt'].hour != tmp_hour:
                        tmp_dict['dt'].append(tmp_datetime)
                        tmp_dict['open'].append(tmp_open)
                        tmp_dict['high'].append(tmp_high)
                        tmp_dict['low'].append(tmp_low)
                        tmp_dict['close'].append(tmp_close)
                        tmp_open = row['open']
                        tmp_high = row['high']
                        tmp_low = row['low']
                        tmp_datetime = row['dt']
                        tmp_hour = row['dt'].hour
                        tmp_minute = row['dt'].minute
                    elif 30<row['dt'].minute<45:
                        continue
                    else:
                        raise ValueError(f'M1 to M15 unkown error, start datetime:{tmp_hour} {tmp_minute} end datetime:{row["dt"].hour} {row["dt"].minute}')
                elif tmp_minute>=45:
                    if row['dt'].hour != tmp_hour:
                        tmp_dict['dt'].append(tmp_datetime)
                        tmp_dict['open'].append(tmp_open)
                        tmp_dict['high'].append(tmp_high)
                        tmp_dict['low'].append(tmp_low)
                        tmp_dict['close'].append(tmp_close)
                        tmp_open = row['open']
                        tmp_high = row['high']
                        tmp_low = row['low']
                        tmp_datetime = row['dt']
                        tmp_hour = row['dt'].hour
                        tmp_minute = row['dt'].minute
                    elif 45<row['dt'].minute<=59:
                        continue
                    else:
                        raise ValueError(f'M1 to M15 unkown error, start datetime:{tmp_hour} {tmp_minute} end datetime:{row["dt"].hour} {row["dt"].minute}')
                else:
                    raise ValueError(f'M1 to M15 unkown error, start datetime:{tmp_hour} {tmp_minute} end datetime:{row["dt"].hour} {row["dt"].minute}')
        df = DataFrame(tmp_dict, columns=list(tmp_dict.keys()))
        return df
    elif time_frame == 'H1':
        tmp_datetime = None
        tmp_hour = None
        tmp_open = None
        tmp_high = None
        tmp_low = None
        tmp_close = None

        for index, row in df.iterrows():
            if tmp_open is None:
                tmp_open = row['open']
                tmp_high = row['high']
                tmp_low = row['low']
                tmp_datetime = row['dt']
                tmp_hour = row['dt'].hour
            else:
                if row['high'] > tmp_high:
                    tmp_high = row['high']
                if row['low'] < tmp_low:
                    tmp_low = row['low']
                tmp_close = row['close']

                if row['dt'].hour != tmp_hour:
                    tmp_dict['dt'].append(tmp_datetime)
                    tmp_dict['open'].append(tmp_open)
                    tmp_dict['high'].append(tmp_high)
                    tmp_dict['low'].append(tmp_low)
                    tmp_dict['close'].append(tmp_close)
                    tmp_open = row['open']
                    tmp_high = row['high']
                    tmp_low = row['low']
                    tmp_datetime = row['dt']
                    tmp_hour = row['dt'].hour
                else:
                    continue
        df = DataFrame(tmp_dict, columns=list(tmp_dict.keys()))
        return df
    elif time_frame == 'D1':
        tmp_datetime = None
        tmp_day = None
        tmp_open = None
        tmp_high = None
        tmp_low = None
        tmp_close = None

        for index, row in df.iterrows():
            if tmp_day is None:
                tmp_open = row['open']
                tmp_high = row['high']
                tmp_low = row['low']
                tmp_datetime = row['dt']
                tmp_day = row['dt'].day
            else:
                if row['high'] > tmp_high:
                    tmp_high = row['high']
                if row['low'] < tmp_low:
                    tmp_low = row['low']
                tmp_close = row['close']

                if row['dt'].day != tmp_day:
                    tmp_dict['dt'].append(tmp_datetime)
                    tmp_dict['open'].append(tmp_open)
                    tmp_dict['high'].append(tmp_high)
                    tmp_dict['low'].append(tmp_low)
                    tmp_dict['close'].append(tmp_close)
                    tmp_open = row['open']
                    tmp_high = row['high']
                    tmp_low = row['low']
                    tmp_datetime = row['dt']
                    tmp_day = row['dt'].day
                else:
                    continue
        df = DataFrame(tmp_dict, columns=list(tmp_dict.keys()))
        return df
    elif time_frame == 'W1':
        tmp_datetime = None
        tmp_week = None
        tmp_open = None
        tmp_high = None
        tmp_low = None
        tmp_close = None

        for index, row in df.iterrows():
            if tmp_week is None:
                tmp_open = row['open']
                tmp_high = row['high']
                tmp_low = row['low']
                tmp_datetime = row['dt']
                tmp_week = row['dt'].week
            else:
                if row['high'] > tmp_high:
                    tmp_high = row['high']
                if row['low'] < tmp_low:
                    tmp_low = row['low']
                tmp_close = row['close']

                if row['dt'].week != tmp_week:
                    tmp_dict['dt'].append(tmp_datetime)
                    tmp_dict['open'].append(tmp_open)
                    tmp_dict['high'].append(tmp_high)
                    tmp_dict['low'].append(tmp_low)
                    tmp_dict['close'].append(tmp_close)
                    tmp_open = row['open']
                    tmp_high = row['high']
                    tmp_low = row['low']
                    tmp_datetime = row['dt']
                    tmp_week = row['dt'].week
                else:
                    continue
        df = DataFrame(tmp_dict, columns=list(tmp_dict.keys()))
        return df
    else:
        pass
