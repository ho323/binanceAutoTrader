from binance.client import Client
import pandas as pd
import numpy as np
import requests
import datetime
import yaml
from BinanceTrade import *

with open('/Users/ho/Documents/config.yaml', encoding='UTF-8') as f:
    _cfg = yaml.load(f, Loader=yaml.FullLoader)
APP_KEY = _cfg['APP_KEY']
APP_SECRET = _cfg['APP_SECRET']
DISCORD_WEBHOOK_URL = _cfg['DISCORD_WEBHOOK_URL']

client = Client(api_key=APP_KEY, api_secret=APP_SECRET)

ticker = "BTCUSDT"
interval='1d'   # 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M

balance = 1000.0

df = get_ohlcv(client)
df['MA20'] = get_ma(df, 20)
df['RSI'] = get_rsi(df, 14)
df[['MACD', 'MACD Signal', 'MACD Oscillator']] = get_macd(df)
df[['BB Middle', 'BB Upper', 'BB Lower']] = get_bb(df)
df = df.dropna(axis=0)
print(df)

while True:
    try:
        now = datetime.datetime.now()
        if now.hour == 0 and now.minute == 0:
            df = get_df()
        if df['MACD Oscillator'][-1] > 0:
            print()
        send_message("매매 시작! \n현재 잔고: " + get_balance())

    except Exception as e:
        print(e)
        send_message("Error \n", e)