import time
import json
import requests
import os
from dotenv import load_dotenv
import pandas as pd
from pycoingecko import CoinGeckoAPI
from slack_sdk import WebClient
from tabulate import tabulate
import plotly.graph_objects as go


"""
First, we need to get the data from coingecko API. 
Then, we will either plot it to get a bar chart, or send it as a text message. 
"""

# loading the .env file
load_dotenv()

def get_coin_data():
    cg = CoinGeckoAPI()

    # getting the list of ids
    crypto_100 = cg.get_coins_markets(vs_currency='btc')
    df_top100 = pd.DataFrame(crypto_100, columns=['id', 'symbol', 'current_price', 'market_cap', 'market_cap_rank', 'price_change_percentage_24h'])
    
    # removing some coins like stablecoins & btc
    symbols_to_remove = ['usdt', 'usdc', 'busd', 'dai', 'ust', 'btc', 'tusd', 'pax', 'cdai', 'cusdc', 'ceth', 'husd']
    df_top100 = df_top100[~df_top100['symbol'].isin(symbols_to_remove)]
    ids_list = df_top100['id'].tolist()

    # df to which we'll append our 3d data
    df_top100_best_3d = pd.DataFrame(columns=['id', 'price_change_percentage_3d'])

    # getting the 3d performance of the top x coins
    for id in ids_list[:80]:
        # step 1: getting hourly prices for the last 7 days
        coin_data3d = cg.get_coin_market_chart_by_id(id=id, vs_currency='btc', days=3)
        coin_data3d = pd.DataFrame(coin_data3d)
        coin_data3d = coin_data3d['prices']
        coin_data3d = coin_data3d.to_frame() # we get a df of one column with [timestamp, prices] at each row.
        
        # splitting it in two columns
        coin_data3d = pd.DataFrame(coin_data3d['prices'].to_list(), columns=['timestamp', 'prices'])
        
        # step 2: computing the percentage change for the last 3 days
        # we take the mean of prices during the first 12 hours 3 days ago, and the mean of prices during the last 12 hours. 
        oldest_day = coin_data3d.head(12)
        oldest_day_price_avg = oldest_day['prices'].mean()
        mostrecent_day = coin_data3d.tail(12)
        mostrecent_day_price_avg = mostrecent_day['prices'].mean()
        price_change_percentage_3d = ((mostrecent_day_price_avg - oldest_day_price_avg) / oldest_day_price_avg)*100
        
        # step 4: appending the data to the df
        to_append = [[id, price_change_percentage_3d]]
        print(to_append)
        df_top100_best_3d = df_top100_best_3d.append(pd.DataFrame(to_append, columns=['id','price_change_percentage_3d']), ignore_index=True)
        # need 1 sec sleep time so we don't reach coingecko's API limit 
        time.sleep(0.5)

    # merging dataframes to get the symbols and mkcap ranks
    df = pd.merge(df_top100, df_top100_best_3d, on='id')
    df = df.sort_values('price_change_percentage_3d', ascending=False)
    # selecting only specific columns
    df = df[['symbol', 'market_cap_rank', 'price_change_percentage_3d']]
    # renaming the columns
    df.columns = ['Ticker', 'N°', '3d % change (btc)']
    df = df.set_index('N°')
    df = df.round(decimals=2)
    return df




# the function that would be use to plot the data
def plot_data(data, file_type):
    # we need data that renders nice visually if we are going to plot it
    df = data[:15]
    df = df.sort_values('price_change_percentage_24h', ascending=True)

    # plotting the dataframe
    ids = df['symbol']
    fig = go.Figure(data=[
        go.Bar(name='24h', x=df['price_change_percentage_24h'], y=ids, orientation='h'),
        go.Bar(name='7d', x=df['price_change_percentage_7d'], y=ids, orientation='h')
    ])
    # changing the bar mode
    fig.update_layout(barmode='group')

    # saving the plot
    if file_type == "html":
        # save as an html file (interactive)
        fig.write_html("html/file.html")
    else:
        # save as a picture
        fig.write_image("images/fig1.png")





# sending the data to Slack
def send_to_slack(type, data):
    data = data
    client = WebClient(token=os.environ.get("SLACK_TOKEN"))
    channel = os.environ.get("CHANNEL")


    if type == "image":
        plot_data(data, "png")
        # sending the text or image to slack
        client.files_upload(
            channels=channel, 
            initial_comment="Here's the 24h ranking of altcoins with their 7 days data, in BTC terms :rocket:", 
            file="images/fig1.png",
        )

    elif type == "text":
        client.chat_postMessage(
            channel=channel,
            username="The Crypto Bot",
            # this will display in the notification
            text= "Top 25 ALTBTC 3d",
            blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Top 25 ALTBTC - 3d ranking*",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Welcome to The Crypto Bot 3d Perf, giving you daily update of the best performing alts over the past 3 days from the top 80 market cap. \n We hope this helps you in your trading! :pray: \n\n",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": data[:25].to_markdown(),
                },
            },]
        )



    
if __name__ == '__main__':
    # For now we prefer receiving the top 25 by text
    send_to_slack("text", get_coin_data())

