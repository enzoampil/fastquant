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


def periodic_fetch(file_dir, symbol, today, next_period_dummy=False):
    today_df = get_stock_data(symbol, today, today)

    # Retrieve saved historical data on disk and append new data
    # TODO: add checks if daily updates were broken
    df = pd.read_csv(file_dir, parse_dates=["dt"]).set_index("dt")
    # df = df.append(today_df)
    df = pd.concat([df, today_df], ignore_index=True)
    if next_period_dummy:
        tomorrow_dummy = today_df.iloc[-1:].copy()
        tomorrow_dummy.index = tomorrow_dummy.index + timedelta(days=1)
        # df = df.append(tomorrow_dummy)
        df = pd.concat([df, tomorrow_dummy], ignore_index=True)

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
    webhook_url = os.getenv("SLACK_URL")
    assert (
        webhook_url
    ), "Please set your slack webhook url as an environment variable: SLACK_URL"
    # Set date to the current date (UTC + 0) if no date argument is passed
    date = date or datetime.utcnow().strftime("%Y-%m-%d")
    message = "Today is " + date + ": " + action + " " + symbol or ""
    slack_post(message, webhook_url)


def email_notif(
    symbol,
    action,
    to_address,
    date=None,
    subject=None,
    message=None,
    host="smtp.gmail.com",
    port=587,
):
    """
    Send email w/ credentials saved as environment variables for security

    If your credentials are correct and the email still doesn't work, refer to the link below:
    https://stackoverflow.com/questions/16512592/login-credentials-not-working-with-gmail-smtp
    """
    my_address = os.getenv("EMAIL_ADDRESS")
    password = os.getenv("EMAIL_PASSWORD")
    # set up the SMTP server
    s = smtplib.SMTP(host=host, port=port)
    s.starttls()
    s.login(my_address, password)

    msg = MIMEMultipart()  # create a message

    date = date or datetime.utcnow().strftime("%Y-%m-%d")
    message = message or "Today is " + date + ": " + action + " " + symbol or ""

    # setup the parameters of the message
    msg["From"] = my_address
    msg["To"] = to_address
    msg["Subject"] = subject or message

    # add in the message body
    msg.attach(MIMEText(message, "plain"))

    # send the message via the server set up earlier.
    s.send_message(msg)


def trigger_bot(symbol, action, date, channel=None, **kwargs):
    if channel == "slack":
        slack_notif(symbol, action, date=date)
    elif channel == "email":
        email_notif(symbol, action, date=date, **kwargs)
    else:
        if action == "buy":
            print(
                ">>> Notif bot: Today is",
                date,
                ":",
                action,
                symbol or "",
                "<<<",
            )
        elif action == "sell":
            print(
                ">>> Notif bot: Today is",
                date,
                ":",
                action,
                symbol or "",
                "<<<",
            )
        else:  # hold
            print(
                ">>> Notif bot: Today is",
                date,
                ":",
                action,
                symbol or "",
                "<<<",
            )
    return
