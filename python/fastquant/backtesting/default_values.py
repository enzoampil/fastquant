#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pkg_resources import resource_filename

# Global arguments
INIT_CASH = 100000
COMMISSION_PER_TRANSACTION = 0.0075
DATA_FILE = resource_filename(__name__, "data/JFC_20180101_20190110_DCV.csv")

BUY_PROP = 1
SELL_PROP = 1
