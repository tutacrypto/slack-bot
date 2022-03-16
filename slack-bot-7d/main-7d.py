import os
from dotenv import load_dotenv
import pandas as pd
from pycoingecko import CoinGeckoAPI
from slack_sdk import WebClient

# loading the .env file
load_dotenv()


def get_coin_data(ordering):
    cg = CoinGeckoAPI()

    crypto_100 = cg.get_coins_markets(vs_currency='usd', price_change_percentage='7d')
    df_top100 = pd.DataFrame(crypto_100, columns=['symbol', 'price_change_percentage_7d_in_currency'])
    
    symbols_to_remove = ['usdc', 'busd', 'dai', 'ust', 'btc', 'tusd', 'pax', 'cdai', 'cusdc', 'ceth', 'husd']
    df_top100 = df_top100[~df_top100['symbol'].isin(symbols_to_remove)]

    df_7d = df_top100[0:80]
    df_7d = df_7d.sort_values('price_change_percentage_7d_in_currency', ascending=False)
    df_7d.columns = ['Token', 'Weekly USD Change']
    df_7d = df_7d.round(decimals=2)
    if ordering == "top":
        df_7d = df_7d.head(15)
    elif ordering == "bottom":
        df_7d = df_7d.tail(15)
        df_7d = df_7d.sort_values('Weekly USD Change', ascending=True)

    print(df_7d)
    return df_7d




def send_to_slack(top, bottom):
    client = WebClient(token=os.environ.get("SLACK_TOKEN"))
    channel = os.environ.get("CHANNEL")


    client.chat_postMessage(
        channel=channel,
        username="The Crypto Bot",
        # this is what will display in the notification
        text= "Crypto Market Weekly Performance (USD)",
        blocks=[
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Top & bottom 15 tokens weekly performance (USD)*",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Weekly performance of the crypto market. Best & worst 15 performing tokens. \n Hope it helps! :ok_hand: \n\n",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Top 15*",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": top.to_markdown(),
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Bottom 15*",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": bottom.to_markdown(),
            },
        },
        
        ]
    )



    
if __name__ == '__main__':
    top = "top"
    bottom = "bottom"
    send_to_slack(get_coin_data(top), get_coin_data(bottom))

