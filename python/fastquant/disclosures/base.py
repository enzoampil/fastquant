#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 5, 2020

@authors: enzoampil & jpdeleon
"""

from datetime import datetime
import warnings
from string import digits


def _remove_amend(x):
    if len(x.split("]")) == 2:
        return x.split("]")[1]
    else:
        return x


def format_date(date, informat="%Y-%m-%d", outformat="%%m-%d-%Y"):
    return datetime.strptime(date, informat).strftime(outformat)


def date_to_epoch(date, format="%Y-%m-%d"):
    return int(datetime.strptime(date, format).timestamp())


def remove_digits(string):
    remove_digits = str.maketrans("", "", digits)
    res = string.translate(remove_digits)
    return res


def get_company_disclosures(*args, **kwargs):
    errmsg = "This function is deprecated. Use `DisclosuresPSE` class instead."
    warnings.warn(errmsg, DeprecationWarning)
    print(errmsg)
