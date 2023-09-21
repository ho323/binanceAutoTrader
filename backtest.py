from BinanceTrade import *
from binance.client import Client
import pandas as pd
import numpy as np
import datetime
import yaml
import openpyxl
import time

start_time = time.time()

ticker = "STXUSDT"
interval = "15m"
start_date = datetime.datetime(2019, 1, 1)
end_date = datetime.datetime.now()
# df = pd.read_csv(f"data/{ticker}/{ticker}{interval}.csv")
df=get_all_ohlcv(
    symbol=ticker, 
    interval=interval, 
    start_date=start_date, 
    end_date=end_date
    )

# 초기 설정
start_balance =10000.0 # 시작 자산
fee = 0.0005    # 수수료
dca_levels = [0.3,0.5,1]      # 분할매수 비율
dca = -0.02 # 분할매수 진입 최소 수익률 
mtp = -1    # Min Take Profit 매도시 최소 수익률 (미사용 시 -1)
stl = -1    # Stop Loss (미사용 시 -1)
length=14
change_percentage=1.4
below=25
above=50

# 전략 설정
bt = vwma_long_strategy(df=df,change_percentage=change_percentage,below=below,above=above)

# 백테스트 시작
bt['보유현금'] = 0.0
bt['보유수량'] = 0.0
bt['평균단가'] = 0.0
bt['현재수익률'] = 0.0
bt['총자산'] = 0.0
bt['총수익률'] = 0.0
cash = start_balance    # 보유현금
quantity = 0    # 보유수량
dca_level = 0   # 분할매수 횟수
ror = 0     # 수익률
pror = 0    # 직전매수가 대비 수익률 
buy_price = None    # 평균단가
pre_price = None    # 직전매수가
buy_pur = 0     # 매수 횟수
sell_pur = 0    # 매도 횟수
ar = []     # 청산 수익률 기록
for i in range(len(bt)):
    price = df.loc[i, 'Close']  # 현재가
    ror = (price-buy_price) / buy_price if buy_price != None else 0   # 수익률 계산
    pror = (price-pre_price) / pre_price if pre_price != None else -1
    if bt.loc[i, 'Action'] == 'Long' and dca_level < len(dca_levels) and pror < dca:
        rate = dca_levels[dca_level]    # 매수 비율
        buy_quantity = cash*rate / price*(1-fee)  # 매수수량 = 현금*비율 / 현재가*(1-수수료)
        if buy_price == None:   # 매수 평균가 조정
            buy_price = price
        else:
            buy_price = (buy_price*quantity + price*buy_quantity )/(quantity+buy_quantity)
        pre_price = price
        quantity += buy_quantity    # 수량 업데이트
        cash -= cash*rate   # 현금 업데이트
        dca_level += 1
        buy_pur += 1
        # print(f"{bt.loc[i, 'Time']} {buy_quantity*price}$ 매수!")
    elif bt.loc[i, 'Action'] == 'Short' and quantity > 0 and pror > mtp or pror < stl:
        rate = 1    # 매도 비율
        sell_quantity = quantity * rate     # 매도 수량
        cash += sell_quantity * price * (1-fee)     # 현금 업데이트 (수수료 포함)
        quantity -= sell_quantity   # 수량 업데이트
        dca_level = 0
        sell_pur += 1
        buy_price = None
        pre_price = None
        ar.append(ror)
        print(f"{bt.loc[i, 'Time']} (수익률: {round(ror*100,3)}%) {sell_quantity*price}$ 매도!")
    bt.loc[i, '보유현금'] = cash
    bt.loc[i, '보유수량'] = quantity
    bt.loc[i, '평균단가'] = buy_price
    bt.loc[i, '현재수익률'] = ror*100
    bt.loc[i, '총자산'] = cash + (quantity*price)
    bt.loc[i, '총수익률'] = ((bt.loc[i,'총자산'] - start_balance) / start_balance)*100

end_time = time.time()
execution_time = end_time - start_time
print(f"실행 시간: {execution_time:.2f} 초")


print(f"{ticker} {interval}")
print(f"매수 횟수: {buy_pur}번")
print(f"매도 횟수: {sell_pur}번")
print(f"매매 평균 수익률: {(sum(ar)/len(ar))*100}%")
print(f"최고 수익률: {round(max(bt['총수익률']),3)}%")
print(f"MDD: {round(min(bt['현재수익률']),3)}%")
print(f"최종 수익률: {round(bt['총수익률'].iloc[-1],3)}%")


# 엑셀로 출력
strategy_name = "SRP"
now = datetime.datetime.now()
bt.to_excel(f"backtest/[{strategy_name}]BackTest_{ticker}{interval}_{start_date.strftime('%Y%m%d')}~{end_date.strftime('%Y%m%d')}.xlsx")