import os
from pathlib import Path
import zipfile
import logging
import pickle
import multiprocessing

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
            file_size += 4096
            forex_zip_file.write(chunk)
    logger.info(f'download {symbol} success')
    zip_file = zipfile.ZipFile(Path(DATA_PATH, f'{symbol}.zip'))
    zip_file.extractall(Path(DATA_PATH))
    logger.info('unzip success')

    forex_df = pd.read_csv(
        Path(DATA_PATH, f'{symbol}.txt'),
        dtype={'<DTYYYYMMDD>': str, '<TIME>': str, '<OPEN>': float, '<HIGH>': float, '<LOW>': float, '<CLOSE>': float}
    )
    logger.info('load txt success')
    del(forex_df['<TICKER>'])
    del(forex_df['<VOL>'])
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
    forex_df = forex_df.rename(columns=rename_dict)[rename_list].drop_duplicates()
    logger.info('change column name success')
    forex_df['dt'] = forex_df['date'] + forex_df['time']
    logger.info('sum date and time success')
    del(forex_df['date'])
    del(forex_df['time'])
    logger.info('start transfer str datetime to pd.timestamp, this step needs 6 minutes on INTEL-9900k')
    forex_df['dt'] = pd.to_datetime(forex_df.dt)
    logger.info('transfer is done')
    # make other timeframe pickle
    logger.info('start shape M1 data to other time frame, this step needs 15 minutes and 7GB RAM free')
    multi_jobs = [
        multiprocessing.Process(target=shape_data_from_1min_to_other, args=((symbol, forex_df, _)))
        for _ in {"M1", "M15", "H1", "D1", "W1"} - {time_frame}
    ]
    for job in multi_jobs:
        job.start()
    while multi_jobs:
        multi_jobs.pop().join()
    logger.info('shape data to other time frame is done')

    # make goal timeframe pickle
    logger.info(f'start shape {symbol} to {time_frame}')
    forex_df = shape_data_from_1min_to_other(symbol, forex_df, time_frame)
    logger.info('all is done')

    if start_date is not None:
        forex_df = forex_df[(forex_df['dt'] >= start_date) & (forex_df['dt'] <= end_date)]
    return forex_df.set_index('dt')


def get_local_data(symbol, start_date=None, end_date=None,  time_frame='D1'):
    if start_date is not None:
        start_date = datestring_to_datetime(start_date)
        end_date = datestring_to_datetime(end_date)
    logger.info(f'start load {symbol} pickle to memory')
    try:
        with open(Path(DATA_PATH, f'{symbol}_{time_frame}.pickle'), 'rb') as df_file:
            df = pickle.load(df_file)
    except Exception as e:
        raise FileNotFoundError('backup file not found, try get_forextester_data method first')
    if start_date is None:
        return df.set_index('dt')
    else:
        df = df[(df['dt'] >= start_date) & (df['dt'] <= end_date)]
        return df.set_index('dt')


def shape_data_from_1min_to_other(symbol, df, time_frame, has_pickle=True):
    if time_frame not in ["M1", "M15", "H1", "D1", "W1"]:
        raise ValueError('time_frame must in this list:["M1", "M15", "H1", "D1", "W1"]')
    logger.info(f'start shape {symbol} to {time_frame}')
    tmp_dict = {
        'dt': [],
        'open': [],
        'high': [],
        'low': [],
        'close': []
    }

    if time_frame == 'M1':
        pass
    elif time_frame == 'M15':
        tmp_datetime = None
        tmp_day = None
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
                tmp_day = row['dt'].day
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
                        tmp_day = row['dt'].day
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
                        tmp_day = row['dt'].day
                        continue
                    elif row['dt'].minute <15:
                        continue
                    elif row['dt'].day != tmp_day:
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
                        tmp_day = row['dt'].day
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
                        tmp_day = row['dt'].day
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
                        tmp_day = row['dt'].day
                        continue
                    elif 15<row['dt'].minute <30:
                        continue
                    elif row['dt'].day != tmp_day:
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
                        tmp_day = row['dt'].day
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
                        tmp_day = row['dt'].day
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
                        tmp_day = row['dt'].day
                    elif 30<row['dt'].minute<45:
                        continue
                    elif row['dt'].day != tmp_day:
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
                        tmp_day = row['dt'].day
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
                        tmp_day = row['dt'].day
                    elif 45<row['dt'].minute<=59:
                        continue
                    elif row['dt'].day != tmp_day:
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
                        tmp_day = row['dt'].day
                    else:
                        raise ValueError(f'M1 to M15 unkown error, start datetime:{tmp_hour} {tmp_minute} end datetime:{row["dt"].hour} {row["dt"].minute}')
                else:
                    raise ValueError(f'M1 to M15 unkown error, start datetime:{tmp_hour} {tmp_minute} end datetime:{row["dt"].hour} {row["dt"].minute}')
        df = DataFrame(tmp_dict, columns=list(tmp_dict.keys()))
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
    else:
        pass
    if has_pickle:
        with open(Path(DATA_PATH, f'{symbol}_{time_frame}.pickle'), 'wb') as df_file:
            pickle.dump(df, df_file, True)
    return df


def gen_candle_chart(df, start_time=None, end_time=None):
    df = df.reset_index()
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
