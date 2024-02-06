import os
import requests
from dotenv import load_dotenv

load_dotenv()

class SlackNotification(Notification):
    def __init__(self):
        self.webhook_url = os.getenv("SLACK_WEBHOOK_URL")

    def send(self, message: str):
        payload = {"text": message}
        response = requests.post(self.webhook_url, json=payload)
        if response.status_code != 200:
            raise ValueError(f"Request to Slack returned an error {response.status_code}, the response is:\n{response.text}")
          
