#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import pandas as pd
import requests
import os
from datetime import datetime, timedelta
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from fastquant.data.stocks.stocks import get_stock_data
import logging

logging.getLogger().setLevel(logging.INFO)


def periodic_fetch(file_dir, symbol, today, next_period_dummy=False):
    today_df = get_stock_data(symbol, today, today)

    # Retrieve saved historical data on disk and append new data
    # TODO: add checks if daily updates were broken
    df = pd.read_csv(file_dir, parse_dates=["dt"]).set_index("dt")
    df = df.append(today_df)
    if next_period_dummy:
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


def slack_notif(message, date=None):
    webhook_url = os.getenv('SLACK_URL')
    assert webhook_url, "Please set your slack webhook url as an environment variable: SLACK_URL"
    # Set date to the current date (UTC + 0) if no date argument is passed
    date = date or datetime.utcnow().strftime("%Y-%m-%d")
    slack_post(message, webhook_url)


def email_notif(
    message, to_address=None, date=None, subject=None, host="smtp.gmail.com", port=587
):
    """
    Send email w/ credentials saved as environment variables for security

    If your credentials are correct and the email still doesn't work, refer to the link below:
    https://stackoverflow.com/questions/16512592/login-credentials-not-working-with-gmail-smtp
    """
    my_address = os.getenv('EMAIL_ADDRESS')
    password = os.getenv('EMAIL_PASSWORD')
    assert my_address, "Please set your email address as an environment variable: EMAIL_ADDRESS"
    assert password, "Please set your email password as an environment variable: EMAIL_PASSWORD"
    # set up the SMTP server
    s = smtplib.SMTP(host=host, port=port)
    s.starttls()
    s.login(my_address, password)

    msg = MIMEMultipart()  # create a message

    date = date or datetime.utcnow().strftime("%Y-%m-%d")

    # setup the parameters of the message
    msg["From"] = my_address
    msg["To"] = to_address
    msg["Subject"] = subject or message

    # add in the message body
    msg.attach(MIMEText(message, "plain"))

    # send the message via the server set up earlier.
    s.send_message(msg)


def trigger_bot(symbol, action, date, indicators, message=None, channel=None, to_address=None, **kwargs):
    logging.info("Triggering notification via channel: {}".format(channel))
    if not message:
        message = date + ": " + action + " " + symbol + "\n Indicators: \n" + indicators
    if channel == "slack":
        slack_notif(message, date=date)
    elif channel == "email":
        email_notif(message, to_address=to_address, date=date, **kwargs)
    else:
        logging.info(">>> Notif bot: " + message + " <<<")
    return
