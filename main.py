import time
import json
import requests
import os
from dotenv import load_dotenv

import pandas as pd
from pycoingecko import CoinGeckoAPI
from slackbot import Slackbot
from slack import WebClient
from tabulate import tabulate
import plotly.graph_objects as go

def get_coin_data():
    cg = CoinGeckoAPI()

    # getting the list of ids
    crypto_100 = cg.get_coins_markets(vs_currency='btc')
    df_top100 = pd.DataFrame(crypto_100, columns=['id', 'symbol', 'current_price', 'market_cap', 'market_cap_rank', 'price_change_percentage_24h'])
    
    # deleting the stablecoins
    stablecoins = ['usdt', 'usdc', 'busd', 'dai', 'ust']
    df_top100 = df_top100[~df_top100['symbol'].isin(stablecoins)]
    ids_list = df_top100['id'].tolist()

    # getting the 24h ranking
    df_top100_best24h = df_top100.sort_values('price_change_percentage_24h', ascending=False)
    
    # df to which we'll append our 7d data
    df_top100_best7d = pd.DataFrame(columns=['id', 'price_change_percentage_7d'])

    # getting the 7d performance of the top x coins
    for id in ids_list:
        # step 1: getting hourly prices for the last 7 days
        coin_data7d = cg.get_coin_market_chart_by_id(id=id, vs_currency='btc', days=7)
        coin_data7d = pd.DataFrame(coin_data7d)
        coin_data7d = coin_data7d['prices']
        coin_data7d = coin_data7d.to_frame() # we get a df of one column with [timestamp, prices] at each row.
        # splitting it in two columns
        coin_data7d = pd.DataFrame(coin_data7d['prices'].to_list(), columns=['timestamp', 'prices'])

        # step 2: computing the percentage change for the last 7 days
        oldest_day = coin_data7d.head(24)
        oldest_day_price_avg = oldest_day['prices'].mean()
        mostrecent_day = coin_data7d.tail(24)
        mostrecent_day_price_avg = mostrecent_day['prices'].mean()
        price_change_percentage_7d = ((mostrecent_day_price_avg - oldest_day_price_avg) / oldest_day_price_avg)*100

        # step 4: appending the data to the df
        to_append = [[id, price_change_percentage_7d]]
        print(to_append)
        df_top100_best7d = df_top100_best7d.append(pd.DataFrame(to_append, columns=['id','price_change_percentage_7d']),ignore_index=True)
        time.sleep(0.2)

    # getting the final dataframe
    df_top100 = pd.merge(df_top100_best24h, df_top100_best7d, on='id')
    df1 = df_top100.sort_values('price_change_percentage_24h', ascending=True)
    df1 = df1[['symbol', 'market_cap_rank', 'price_change_percentage_24h', 'price_change_percentage_7d']]
    # df7 = df_top100.sort_values('price_change_percentage_7d', ascending=False)
    return df1

def plot_data(data, file_type):
    df = data

    # plotting the dataframe
    ids = df['symbol']
    fig = go.Figure(data=[
        go.Bar(name='24h', x=df['price_change_percentage_24h'], y=ids, orientation='h'),
        go.Bar(name='7d', x=df['price_change_percentage_7d'], y=ids, orientation='h')
    ])
    # Change the bar modes
    fig.update_layout(barmode='group')

    # Saving and sending the graph
    if file_type == "html":
        # save as an html file (interactive)
        fig.write_html("html/file.html")
    else:
        # save as a picture
        fig.write_image("images/fig1.png")



def send_to_slack():

    # sending the image to slack
    client = WebClient(token=os.environ.get("SLACK_TOKEN"))
    client.files_upload(
        channels='#crypto_screening', 
        initial_comment="Here's the 24h ranking of altcoins with their 7 days data, in BTC terms :rocket:", 
        file="images/fig1.png",
    )

    
if __name__ == '__main__':
    data = get_coin_data()
    plot_data(data, "png")
    send_to_slack()

