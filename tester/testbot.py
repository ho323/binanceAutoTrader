import time
from binance.client import Client
import pandas as pd
import numpy as np
import requests
import datetime
import yaml
import tratingtool

with open('/Users/ho/Documents/config.yaml', encoding='UTF-8') as f:
    _cfg = yaml.load(f, Loader=yaml.FullLoader)
APP_KEY = _cfg['APP_KEY']
APP_SECRET = _cfg['APP_SECRET']
DISCORD_TOKEN = _cfg['DISCORD_TOKEN']

client = Client(api_key=APP_KEY, api_secret=APP_SECRET)

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
strategy = tratingtool.strategy_vwma_long
balance = 1000.0    # 가상 자산
length=14
change_percentage=1.4
below=55
above=100

# 매매 시작
fee = 0.0005    # 수수료
quantity = 0    # 보유수량
dca_level = 0   # 분할매수 횟수
ror = 0     # 수익률
pror = -1    # 직전매수가 대비 수익률 
buy_price = None    # 평균단가
pre_price = None    # 직전매수가
buy_pur = 0     # 매수 횟수
sell_pur = 0    # 매도 횟수
ar = []     # 청산 수익률 기록
current_action = 'Stay'  
prev_action = 'Stay'  # 이전 Action 값을 저장할 변수

while True:
    try:
        now = datetime.datetime.now()
        if now.second == 0:
            df = tratingtool.get_ohlcv(client=client,ticker=ticker,interval=interval,limit=50)
            st = strategy(df)
            current_action = st['Action'].iloc[-1]
            print(f"{now}, {ticker}:{df['Close'].iloc[-1]}$, {current_action}")
        
        if current_action != prev_action:   # Action이 이전과 다른 경우에만 거래 수행
            price = tratingtool.get_current_price(client, ticker)
            pror = (price-pre_price) / pre_price if pre_price != None else -1

            if current_action == 'Long' and dca_level < len(dca_levels) and pror < dca:
                buy_rate = dca_levels[dca_level]    # 매수 비율
                buy_quantity = balance*buy_rate / price*(1-fee)  # 매수수량 = 현금*비율 / 현재가*(1-수수료)
                if buy_price == None:   # 매수 평균가 조정
                    buy_price = price
                else:
                    buy_price = (buy_price*quantity + price*buy_quantity )/(quantity+buy_quantity)
                pre_price = price
                quantity += buy_quantity    # 수량 업데이트
                balance -= balance*buy_rate   # 현금 업데이트
                dca_level += 1
                buy_pur += 1
                # print(f"{round(price*buy_quantity,2)}$ 매수 완료! ({dca_level}번째 매수) \n현재 잔고: {round(balance,2)}$"))
            elif current_action == 'Short' and quantity > 0 and pror > mtp or pror < stl:
                sell_rate = 1
                sell_quantity = quantity * sell_rate
                balance += sell_quantity * price * (1-fee)
                pre_price = None
                quantity -= sell_quantity
                dca_level = 0
                # print(f"{round(price*sell_quantity,2)}$ 매도 완료! (수익률 {0}%) \n현재 잔고: {round(balance,2)}$"))
            
            prev_action = current_action  # 이전 Action 업데이트
        time.sleep(1)  # 1초 대기
    except Exception as e:
        print(e)
        send_message("Error \n", e)