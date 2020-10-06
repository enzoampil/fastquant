import unittest
import multiprocessing

from fastquant.data.forex.forextester import *
from fastquant.data.forex.forex import get_forex_data

class TestForexMethod(unittest.TestCase):
    allowed_symbol_list = [
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

    def test_download_and_unzip(self):
        for symbol in self.allowed_symbol_list:
            logger.info(f'start downloading forex {symbol} data zip file...')
            file_size = 0
            res = requests.get(f'http://www.forextester.com/templates/data/files/{symbol}.zip', stream=True)
            with open(Path(DATA_PATH, f'{symbol}.zip'), 'wb') as forex_zip_file:
                for chunk in res.iter_content(chunk_size=4096):
                    file_size += 4096
                    if file_size < 1048576:
                        logger.info(f'download {round(file_size / 1024)}KB')
                    else:
                        logger.info(f'download {round(file_size / 1048576)}MB')
                    forex_zip_file.write(chunk)
            logger.info('download success')
            zip_file = zipfile.ZipFile(Path(DATA_PATH, f'{symbol}.zip'))
            zip_file.extractall(Path(DATA_PATH))
            logger.info('unzip success')

    def test_shape_and_make_tmp(self):
        '''
        transfer txt to pd.timestamp 6min
        M1 to H1 11min
        M1 to M15 15min
        M1 to W1 11min
        M1 to D1 13min

        :return:
        '''
        for symbol in self.allowed_symbol_list:
            time_frame = 'D1'
            forex_dataframe = pd.read_csv(
                Path(DATA_PATH, f'{symbol}.txt'),
                dtype={'<DTYYYYMMDD>': str, '<TIME>': str, '<OPEN>': float, '<HIGH>': float, '<LOW>': float,
                       '<CLOSE>': float}
            )
            logger.info('load txt success')
            del (forex_dataframe['<TICKER>'])
            del (forex_dataframe['<VOL>'])
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
            del (forex_dataframe['date'])
            del (forex_dataframe['time'])
            logger.info('start transfer str datetime to pd.timestamp, this step requires 6 minutes on INTEL-9900k')
            forex_dataframe['dt'] = pd.to_datetime(forex_dataframe.dt)
            logger.info('transfer is done')

            # make other timeframe pickle
            logger.info('start shape M1 data to other time frame, this step need 7GB RAM free')
            multi_jobs = [
                multiprocessing.Process(target=shape_data_from_1min_to_other, args=((symbol, forex_dataframe, _)))
                for _ in {"M1", "M15", "H1", "D1", "W1"} - {time_frame}
            ]
            for job in multi_jobs:
                job.start()
            while multi_jobs:
                multi_jobs.pop().join()
            logger.info('shape other is done')

            # make goal timeframe pickle
            logger.info(f'start shape {symbol} to {time_frame}')
            forex_dataframe = shape_data_from_1min_to_other(symbol, forex_dataframe, time_frame)

            logger.info('all is done')

    def test_combining_test(self):
        from fastquant import backtest
        df = get_forex_data('EURUSD')
        backtest('smac', df, fast_period=20, slow_period=40)

        df = get_forex_data('EURUSD', start_date='2018-01-01', end_date='2019-01-01')
        backtest('smac', df, fast_period=20, slow_period=40)

        df = get_forex_data('EURUSD', read_from_local=True)
        backtest('smac', df, fast_period=20, slow_period=40)

        df = get_forex_data('EURUSD', start_date='2018-01-01', end_date='2019-01-01', read_from_local=True)
        backtest('smac', df, fast_period=20, slow_period=40)


if __name__ == '__main__':
    unittest.main()
