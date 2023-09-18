from BinanceTrade import *
from binance.client import Client
import pandas as pd
import numpy as np
import datetime
import yaml
import openpyxl
import time

start_time = time.time()

with open('/Users/ho/Documents/config.yaml', encoding='UTF-8') as f:
    _cfg = yaml.load(f, Loader=yaml.FullLoader)
APP_KEY = _cfg['APP_KEY']
APP_SECRET = _cfg['APP_SECRET']
DISCORD_WEBHOOK_URL = _cfg['DISCORD_WEBHOOK_URL']
client = Client(api_key=APP_KEY, api_secret=APP_SECRET)

# 코인 설정
ticker = "ETHUSDT"
interval='15m'   # 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M
limit=1000
df = get_all_ohlcv(ticker,interval)

# 초기 설정
start_balance =100000.0 # 시작 자산
cash = start_balance
fee = 0.0005

# 전략 설정
rmf_threshold=20
dca_levels=[0.2,0.3,0.5,1]
std_dev=2
bt = srp_strategy(df,rmf_threshold,dca_levels,std_dev)

bt[['현금', '보유수량', '총 자산', '수익률']] = 0.0
quantity = 0
dca_level = 0
ror = 0
bt.loc[0, '현금'] = cash
bt.loc[0, '총 자산'] = cash
bt.loc[0, '수익률'] = ror
for i in range(1, len(bt)):
    price = df.loc[i, 'Close']
    bt.loc[i, '총 자산'] = cash + (quantity*price)
    bt.loc[i, '수익률'] = (bt.loc[i,'총 자산'] - start_balance) / start_balance
    ror = bt.loc[i, '수익률']
    if bt.loc[i, 'Action'] == 'Buy' and dca_level < len(dca_levels):
        rate = dca_levels[dca_level]
        buy_quantity = cash*rate / price * (1-fee)  # 매수수량 = 현금*비율 / 현재가*(1-수수료)
        quantity += buy_quantity    # 수량 업데이트
        cash -= cash*rate   # 현금 업데이트
        dca_level += 1
    elif bt.loc[i, 'Action'] == 'Sell' and ror > 0.02:
        cash += quantity * price * (1-fee)
        quantity = 0
        dca_level = 0
    bt.loc[i, '보유수량'] = quantity
    bt.loc[i, '현금'] = cash
    bt.loc[i, '총 자산'] = cash + (quantity*price)
    bt.loc[i, '수익률'] = (bt.loc[i,'총 자산'] - start_balance) / start_balance
bt['수익률'] *= 100

end_time = time.time()
execution_time = end_time - start_time
print(f"실행 시간: {execution_time:.2f} 초")


print("매수 횟수:", len(bt[bt['Action']=='Buy']), "번")
print("매도 횟수:", len(bt[bt['Action']=='Sell']), "번")
print("최고 수익률:", round(max(bt['수익률']),3), "%")
print("MDD:", round(min(bt['수익률']),3), "%")
print("최종 수익률:", round(bt['수익률'].iloc[-1],3), "%")

# 엑셀로 출력
now = datetime.datetime.now()
bt.to_excel(f"backtest/BackTest_SRP_STRATEGY_{ticker}{interval}_[{now.strftime('%Y-%m-%d %H:%M:%S')}].xlsx")
