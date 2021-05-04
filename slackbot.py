import json
import requests
import os
import ipdb
from dotenv import load_dotenv
import pandas as pd
# import slack
from slack_sdk import WebClient



load_dotenv()


class Slackbot(object):

    # The constructor for the class. It takes the channel name as the a
    # parameter and then sets it as an instance variable
    def __init__(self, data):
        self.channel = '#crypto_screening'
        self.slack_token = os.getenv('SLACK_TOKEN')
        self.error = 'error'
        self.data = data


    # returns a Dict that contains the default text for the message
    def text_block(self):

        text_block = {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": ( f"{self.data.to_markdown()}"
                     ),
                },
            }
        return text_block


    # Crafts and returns the entire message payload as a dictionary.
    def get_message_payload(self):
        message = {
                "channel": self.channel,
                "blocks": [self.text_block()]
            }
        return message


    def send_slack(self):
        # Create a slack client
        slack_web_client = WebClient(self.slack_token)

        message = self.get_message_payload()
        # Post the onboarding message in Slack
        slack_web_client.chat_postMessage(**message)

if __name__ == '__main__':
    main()

