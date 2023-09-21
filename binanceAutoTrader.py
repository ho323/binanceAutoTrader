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

# # 레버리지 변경
# client.futures_change_leverage(
#     symbol="BTCUSDT",
#     leverage=3,
# )

# # 선물 마진 타입 변경
# client.futures_change_margin_type(
#     symbol="BTCUSDT",
#     marginType="ISOLATED",  # ISOLATED, CROSSED
# )

# # 선물 잔고 조회
# account = client.futures_account()
# for i in account['assets']:
#     if i['asset'] == 'USDT':
#         print(i)
# for i in account['positions']:
#     if i['symbol'] == 'BTCUSDT':
#         print(i)

# # 주문 생성
# try:
#     client.futures_create_order(
#         symbol="BTCUSDT",  # 주문 종목
#         timeInForce='GTC',
#         type="LIMIT",   # LIMIT, MARKET
#         side='BUY',     # BUY, SELL
#         price=20000,     # 주문 희망가
#         quantity=1     # 주문 수량
#     )
# except Exception as e:
#     print(e)

# # 모든 주문 취소
# client.futures_cancel_all_open_orders(
#     symbol="BTCUSDT"
# )

ticker = "BTCUSDT"
interval='1d'   # 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M

balance = 1000.0
rate = 1

prev_action = 'Stay'  # 이전 Action 값을 저장할 변수
send_message("매매 시작! \n현재 잔고: " + get_balance())
while True:
    try:
        # now = datetime.datetime.now()
        # if now.minute == 0 and now.second == 0:
        df = get_ohlcv(client)
        st = heikinashi_upswing_strategy(df)
        current_action = st['Action'].iloc[-1]
        
        if current_action != prev_action:
            # Action이 이전과 다른 경우에만 거래 수행
            balance = get_balance(client)
            price = get_current_price(client, ticker)
            quantity = balance * rate / price
            
            if current_action == 'Buy':
                order = client.futures_create_order(
                    symbol=ticker,
                    timeInForce='GTC',
                    type="MARKET",
                    side='BUY',
                    quantity=quantity,
                )
            elif current_action == 'Sell':
                order = client.futures_create_order(
                    symbol=ticker,
                    timeInForce='GTC',
                    type="MARKET",
                    side='SELL',
                    quantity=quantity,
                )
            
            prev_action = current_action  # 이전 Action 업데이트
    except Exception as e:
        print(e)
        send_message("Error \n", e)