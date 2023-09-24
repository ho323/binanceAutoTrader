import time
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

# 초기 설정
ticker = "DOGEUSDT"
interval='15m'   # 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M
dca_levels = [0.3,0.5,1.0]      # 분할매수 비율
dca = -0.02 # 분할매수 진입 최소 수익률 
mtp = -1    # Min Take Profit 매도시 최소 수익률 (미사용 시 -1)
stl = -1    # Stop Loss (미사용 시 -1)

# 전략 설정
length=14
change_percentage=1.4
below=25
above=50
strategy = strategy_vwma_long

# 매매 시작
balance = 0
quantity = 0    # 보유수량
dca_level = 0   # 분할매수 횟수
pror = 0    # 직전매수가 대비 수익률 
pre_price = None    # 직전매수가
ar = []     # 청산 수익률 기록
prev_action = 'Stay'  # 이전 Action 값을 저장할 변수
send_message("매매 시작! \n현재 잔고: " + get_balance(client))
while True:
    try:
        now = datetime.datetime.now()
        if now.second == 0:
            df = get_ohlcv(client=client,ticker=ticker,interval=interval,limit=50)
            st = strategy(df)
            current_action = st['Action'].iloc[-1]
            print(f"{now}, {ticker}:{df['Close'].iloc[-1]}$, {current_action}")
        
        if current_action != prev_action:   # Action이 이전과 다른 경우에만 거래 수행
            balance = get_balance(client)
            price = get_current_price(client, ticker)
            pror = (price-pre_price) / pre_price if pre_price != None else -1

            if current_action == 'Long' and dca_level < len(dca_levels) and pror < dca:
                buy_rate = dca_levels[dca_level]    # 매수 비율
                buy_quantity = balance * buy_rate / price  # 매수수량 = 현금*비율 / 현재가
                order = client.futures_create_order(
                    symbol=ticker,
                    timeInForce='GTC',
                    type="MARKET",
                    side='BUY',
                    quantity=buy_quantity,
                )
                pre_price = price
                quantity += buy_quantity 
                dca_level += 1
            elif current_action == 'Short' and quantity > 0 and pror > mtp or pror < stl:
                sell_rate = 1
                sell_quantity = quantity * sell_rate
                order = client.futures_create_order(
                    symbol=ticker,
                    timeInForce='GTC',
                    type="MARKET",
                    side='SELL',
                    quantity=sell_quantity,
                )
                pre_price = None
                quantity = 0
                dca_level = 0
            
            prev_action = current_action  # 이전 Action 업데이트
        time.sleep(1)  # 1초 대기
    except Exception as e:
        print(e)
        send_message("Error \n", e)