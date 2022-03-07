import os
from dotenv import load_dotenv
import pandas as pd
from pycoingecko import CoinGeckoAPI
from slack_sdk import WebClient
import plotly.graph_objects as go


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





def plot_data(file_type, data):
    df = data[:15]
    df = df.sort_values('change 7d vs usd', ascending=True)

    # plotting the dataframe
    ids = df['---symbol---']
    fig = go.Figure(data=[
        go.Bar(name='7d', x=df['change 7d vs usd'], y=ids, orientation='h')
    ])
    # changing the bar mode
    fig.update_layout(barmode='group')

    if file_type == "html":
        # save as an html file (interactive)
        fig.write_html("html/file.html")
    else:
        # save as a picture
        fig.write_image("images/fig1.png")



def send_to_slack(type, top, bottom):
    client = WebClient(token=os.environ.get("SLACK_TOKEN"))
    channel = os.environ.get("CHANNEL")


    if type == "image":
        plot_data(top, "png")
        client.files_upload(
            channels=channel, 
            initial_comment="Here's the 24h ranking of altcoins with their 7 days data, in BTC terms :rocket:", 
            file="images/fig1.png",
        )

    elif type == "text":
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
    send_to_slack("text", get_coin_data(top), get_coin_data(bottom))

