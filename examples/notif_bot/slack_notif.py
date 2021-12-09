import sys
import json
import requests

action = sys.argv[1]
today = sys.argv[2]
symbol = sys.argv[3]

# See https://api.slack.com/tutorials/slack-apps-hello-world for more information about Slack apps
webhook_url = YOUR_WEBHOOK_URL
message = "Today is " + today + ": " + action + " " + symbol

requests.post(
    webhook_url,
    data=json.dumps({"text": message}),
    headers={"Content-Type": "application/json"},
)
