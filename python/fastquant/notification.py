#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from fastquant.data.stocks.stocks import get_stock_data
import json
import pandas as pd
import subprocess


def daily_fetch(file_dir, symbol, today):
    today_df = get_stock_data(symbol, today, today)

    # Retrieve saved historical data on disk and append new data
    # TODO: add checks if daily updates were broken
    df = pd.read_csv(file_dir, parse_dates=["dt"]).set_index("dt")
    df = df.append(today_df)
    df.to_csv(file_dir)

    return df


def trigger_bot(action, script_dir, today, symbol):
    if script_dir:
        subprocess.run(["python", script_dir, action, today, symbol])
    else:
        if action == "buy":
            print(">>> Notif bot: BUY! <<<")
        elif action == "sell":
            print(">>> Notif bot: SELL! <<<")
        else:  # hold
            print(">>> Notif bot: HOLD! <<<")

    return
