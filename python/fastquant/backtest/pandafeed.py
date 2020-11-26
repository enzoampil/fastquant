#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015-2020 Daniel Rodriguez
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from backtrader.utils.py3 import filter, string_types, integer_types

from backtrader import date2num
import backtrader.feed as feed
import pandas as pd
import queue
import threading
import time
import schedule
from fastquant.data.stocks.yahoofinance import get_yahoo_data
from fastquant.data.crypto.crypto import get_crypto_data
from datetime import datetime, timedelta
import logging

logging.getLogger().setLevel(logging.INFO)


class PandasDirectData(feed.DataBase):
    '''
    Uses a Pandas DataFrame as the feed source, iterating directly over the
    tuples returned by "itertuples".

    This means that all parameters related to lines must have numeric
    values as indices into the tuples

    Note:

      - The ``dataname`` parameter is a Pandas DataFrame

      - A negative value in any of the parameters for the Data lines
        indicates it's not present in the DataFrame
        it is
    '''

    params = (
        ('datetime', 0),
        ('open', 1),
        ('high', 2),
        ('low', 3),
        ('close', 4),
        ('volume', 5),
        ('openinterest', 6),
    )

    datafields = [
        'datetime', 'open', 'high', 'low', 'close', 'volume', 'openinterest'
    ]

    def start(self):
        super(PandasDirectData, self).start()

        # reset the iterator on each start
        self._rows = self.p.dataname.itertuples()

    def _load(self):
        try:
            row = next(self._rows)
        except StopIteration:
            return None  # Experiment with changing to None, which means we allow for resampling

        # Set the standard datafields - except for datetime
        for datafield in self.getlinealiases():
            if datafield == 'datetime':
                continue

            # get the column index
            colidx = getattr(self.params, datafield)

            if colidx < 0:
                # column not present -- skip
                continue

            # get the line to be set
            line = getattr(self.lines, datafield)

            # indexing for pandas: 1st is colum, then row
            line[0] = row[colidx]

        # datetime
        colidx = getattr(self.params, 'datetime')
        tstamp = row[colidx]

        # convert to float via datetime and store it
        dt = tstamp.to_pydatetime()
        dtnum = date2num(dt)

        # get the line to be set
        line = getattr(self.lines, 'datetime')
        line[0] = dtnum

        # Done ... return
        return True


class PandasData(feed.DataBase):
    '''
    Uses a Pandas DataFrame as the feed source, using indices into column
    names (which can be "numeric")

    This means that all parameters related to lines must have numeric
    values as indices into the tuples

    Params:

      - ``nocase`` (default *True*) case insensitive match of column names

    Note:

      - The ``dataname`` parameter is a Pandas DataFrame

      - Values possible for datetime

        - None: the index contains the datetime
        - -1: no index, autodetect column
        - >= 0 or string: specific colum identifier

      - For other lines parameters

        - None: column not present
        - -1: autodetect
        - >= 0 or string: specific colum identifier
    '''

    params = (
        ('nocase', True),

        # Possible values for datetime (must always be present)
        #  None : datetime is the "index" in the Pandas Dataframe
        #  -1 : autodetect position or case-wise equal name
        #  >= 0 : numeric index to the colum in the pandas dataframe
        #  string : column name (as index) in the pandas dataframe
        ('datetime', None),

        # Possible values below:
        #  None : column not present
        #  -1 : autodetect position or case-wise equal name
        #  >= 0 : numeric index to the colum in the pandas dataframe
        #  string : column name (as index) in the pandas dataframe
        ('open', -1),
        ('high', -1),
        ('low', -1),
        ('close', -1),
        ('volume', -1),
        ('openinterest', -1),
        ('reconntimeout', 5.0),
        ('qcheck', 0.5),
        ('cadence', 'daily'),
        ('source', 'yahoo')
    )

    datafields = [
        'datetime', 'open', 'high', 'low', 'close', 'volume', 'openinterest'
    ]

    def __init__(self):
        super(PandasData, self).__init__()
        self.symbol = self.p.symbol
        self.cadence = self.p.cadence
        self.source = self.p.source
        self.qlive = queue.Queue()
        # This indicates if the current iteration is already "live"
        # Since by default, a historical dataframe is passed in,
        # is_live is False until the the historical dataframe has been finished, and live data is now being pulled
        self.is_live = False
        logging.info("===Datafeed level arguments===")
        logging.info("symbol : {}".format(self.symbol))
        logging.info("cadence : {}".format(self.cadence))
        logging.info("source : {}".format(self.source))

        # these "colnames" can be strings or numeric types
        colnames = list(self.p.dataname.columns.values)
        if self.p.datetime is None:
            # datetime is expected as index col and hence not returned
            pass

        # try to autodetect if all columns are numeric
        cstrings = filter(lambda x: isinstance(x, string_types), colnames)
        colsnumeric = not len(list(cstrings))

        # Where each datafield find its value
        self._colmapping = dict()

        # Build the column mappings to internal fields in advance
        for datafield in self.getlinealiases():
            defmapping = getattr(self.params, datafield)

            if isinstance(defmapping, integer_types) and defmapping < 0:
                # autodetection requested
                for colname in colnames:
                    if isinstance(colname, string_types):
                        if self.p.nocase:
                            found = datafield.lower() == colname.lower()
                        else:
                            found = datafield == colname

                        if found:
                            self._colmapping[datafield] = colname
                            break

                if datafield not in self._colmapping:
                    # autodetection requested and not found
                    self._colmapping[datafield] = None
                    continue
            else:
                # all other cases -- used given index
                self._colmapping[datafield] = defmapping

    def start(self):
        super(PandasData, self).start()

        # reset the length with each start
        self._idx = -1

        # Start the data streaming as its own thread
        self.qlive = self.streaming_data(tmout=self.p.reconntimeout)

        # Transform names (valid for .ix) into indices (good for .iloc)
        if self.p.nocase:
            colnames = [x.lower() for x in self.p.dataname.columns.values]
        else:
            colnames = [x for x in self.p.dataname.columns.values]

        for k, v in self._colmapping.items():
            if v is None:
                continue  # special marker for datetime
            if isinstance(v, string_types):
                try:
                    if self.p.nocase:
                        v = colnames.index(v.lower())
                    else:
                        v = colnames.index(v)
                except ValueError as e:
                    defmap = getattr(self.params, k)
                    if isinstance(defmap, integer_types) and defmap < 0:
                        v = None
                    else:
                        raise e  # let user now something failed

            self._colmapping[k] = v

    def _load(self):
        # Utilize live updates when historical data is finished
        if self._idx + 1 >= len(self.p.dataname):

            # Get new data from the queue when it's available; otherwise, keep listening till it is
            try:
                update_df = self.qlive.get(timeout=self._qcheck)
                self.p.dataname = pd.concat([self.p.dataname, update_df]).reset_index(drop=True)
                logging.info(self.p.dataname.tail())
                # Set live to true the moment new data has been added to the queue
                if not self.is_live:
                    self.is_live = True
                    logging.info("Turning live mode on ...")
            except queue.Empty:
                return None  # indicate timeout situation

        self._idx += 1

        # Set the standard datafields
        for datafield in self.getlinealiases():
            if datafield == 'datetime':
                continue

            colindex = self._colmapping[datafield]
            if colindex is None:
                # datafield signaled as missing in the stream: skip it
                continue

            # get the line to be set
            line = getattr(self.lines, datafield)

            # indexing for pandas: 1st is colum, then row
            line[0] = self.p.dataname.iloc[self._idx, colindex]

        # datetime conversion
        coldtime = self._colmapping['datetime']

        if coldtime is None:
            # standard index in the datetime
            tstamp = self.p.dataname.index[self._idx]
        else:
            # it's in a different column ... use standard column index
            tstamp = self.p.dataname.iloc[self._idx, coldtime]

        # convert to float via datetime and store it
        dt = tstamp.to_pydatetime()
        dtnum = date2num(dt)
        self.lines.datetime[0] = dtnum

        # Done ... return
        return True

    def islive(self):
        '''Returns ``True`` to notify ``Cerebro`` that preloading and runonce
        should be deactivated'''
        return True

    def haslivedata(self):
        return True

    def streaming_data(self, tmout=None):

        q = queue.Queue()
        kwargs = {'q': q, 'tmout': tmout}
        t = threading.Thread(target=self.add_data_periodic, kwargs=kwargs)
        t.daemon = True
        t.start()
        return q

    def add_data(self, q, tmout):
        if tmout is not None:
            time.sleep(tmout)

        # Previous day PHT is also safely previous day UTC, and EST (as of 9:00 PHT)
        current_datetime = self.get_current_datetime(tz="PHT") - timedelta(days=1)
        current_datestr = current_datetime.strftime("%Y-%m-%d")
        current_datetimestr = current_datetime.strftime("%Y-%m-%dT%H:%M:%S")
        logging.info("Pulling {} data from {} ...".format(self.symbol, self.source))
        if self.source == "yahoo":
            current_df = get_yahoo_data(self.symbol, current_datestr, current_datestr)
        # Else pull crypto data
        else:
            current_df = get_crypto_data(self.symbol, current_datestr, current_datestr)
        # Note that the datetime column should be the column, not an index
        # Also, the column has to be called "datetime" exactly
        current_df = current_df.reset_index().rename(columns={"dt": "datetime"})
        q.put(current_df)
        logging.info("Queue updated on {}".format(current_datetimestr))

    def add_data_periodic(self, **kwargs):
        if self.cadence == "daily":
            # This should actually depend on the data source, since different markets have different closing times
            # Setting this to 9:00 for now, since should be okay for both UTC and EST markets
            schedule.every().day.at("9:00").do(self.add_data, **kwargs)
        else:
            logging.info("Scheduling every 10 seconds")
            schedule.every(10).seconds.do(self.add_data, **kwargs)
        while True:
            schedule.run_pending()
            time.sleep(1)

    def get_current_datetime(self, tz="EST"):
        # Setting default timezone to EST since this is the timezone of NASDAQ & NYSE
        if tz == "EST":
            return datetime.utcnow() - timedelta(hours=4)
        elif tz == "UTC":
            return datetime.utcnow()
        # Otherwise, PHT / SGT
        else:
            return datetime.utcnow() + timedelta(hours=8)


class YahooPandasData(PandasData):
    def add_data(self, q, tmout):
        if tmout is not None:
            time.sleep(tmout)
        current_datetime = self.get_current_datetime()
        current_datestr = current_datetime.strftime("%Y-%m-%d")
        current_datetimestr = current_datetime.strftime("%Y-%m-%dT%H:%M:%S")
        logging.info("Pulling data from yahoo ...")
        current_df = get_yahoo_data(self.symbol, current_datestr, current_datestr)
        # Note that the datetime column should be the column, not an index
        # Also, the column has to be called "datetime" exactly
        current_df = current_df.reset_index().rename(columns={"dt": "datetime"})
        q.put(current_df)
        logging.info("Queue updated on {}".format(current_datetimestr))


class CCXTPandasData(PandasData):
    def add_data(self, q, tmout):
        if tmout is not None:
            time.sleep(tmout)
        current_datetime = self.get_current_datetime()
        current_datestr = current_datetime.strftime("%Y-%m-%d")
        current_datetimestr = current_datetime.strftime("%Y-%m-%dT%H:%M:%S")
        logging.info("Pulling data from ccxt ...")
        current_df = get_crypto_data(self.symbol, current_datestr, current_datestr)
        # Note that the datetime column should be the column, not an index
        # Also, the column has to be called "datetime" exactly
        current_df = current_df.reset_index().rename(columns={"dt": "datetime"})
        q.put(current_df)
        logging.info("Queue updated on {}".format(current_datetimestr))
