#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from fastquant.data.stocks.stocks import get_stock_data
import json
import pandas as pd
import subprocess
import requests
import os
from datetime import datetime, timedelta


def daily_fetch(file_dir, symbol, today, add_tomorrow_dummy=False):
    today_df = get_stock_data(symbol, today, today)

    # Retrieve saved historical data on disk and append new data
    # TODO: add checks if daily updates were broken
    df = pd.read_csv(file_dir, parse_dates=["dt"]).set_index("dt")
    df = df.append(today_df)
    if add_tomorrow_dummy:
        tomorrow_dummy = today_df.iloc[-1:].copy()
        tomorrow_dummy.index = tomorrow_dummy.index + timedelta(days=1)
        df = df.append(tomorrow_dummy)

    df.to_csv(file_dir)

    return df


def slack_post(message, webhook_url):
    # See https://api.slack.com/tutorials/slack-apps-hello-world for more information about Slack apps

    requests.post(
        webhook_url,
        data=json.dumps({"text": message}),
        headers={"Content-Type": "application/json"},
    )


def slack_notif(symbol, action, date=None):
    webhook_url = os.getenv('SLACK_URL')
    assert webhook_url, "Please set your slack webhook url as an evironment variable: SLACK_URL"
    # Set date to the current date (UTC + 0) if no date argument is passed
    date = date if date else datetime.utcnow().strftime("%Y-%m-%d")
    message = "Today is " + date + ": " + action + " " + symbol or ""
    slack_post(message, webhook_url)


def trigger_bot(symbol, action, date, channel=None):
    if channel == "slack":
        slack_notif(symbol, action, date=date)
    else:
        if action == "buy":
            print(">>> Notif bot: Today is", date, ":", action, symbol or "", "<<<")
        elif action == "sell":
            print(">>> Notif bot: Today is", date, ":", action, symbol or "", "<<<")
        else:  # hold
            print(">>> Notif bot: Today is", date, ":", action, symbol or "", "<<<")
    return
