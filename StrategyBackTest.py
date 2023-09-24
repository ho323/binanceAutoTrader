from BinanceTrade import *
import pandas as pd
import numpy as np
import datetime

def DCABackTest(data,start_balance=10000.0,fee=0.0005,dca=-0.02,dca_levels=[0.3,0.5,0.1],mtp=-1,stl=-1):
    """
    분할매수 백테스트
    start_balance: 초기자산
    fee: 수수료 
    mtp: Min Take Profit (사용하지 않으면 -1)
    stl: Stop Loss (사용하지 않으면 -1)
    dca: 추가매수 수익률
    """
    data = data.assign(보유현금=0.0, 보유수량=0.0, 평균단가=0.0, 현재수익률=0.0, 총자산=0.0, 총수익률=0.0)
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
    for i in range(len(data)):
        price = data.loc[i, 'Close']  # 현재가
        ror = (price-buy_price) / buy_price if buy_price != None else 0   # 수익률 계산
        pror = (price-pre_price) / pre_price if pre_price != None else -1
        if data.loc[i, 'Action'] == 'Long' and dca_level < len(dca_levels) and pror < dca:
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
            # print(f"{data.loc[i, 'Time']} {buy_quantity*price}$ 매수!")
        elif data.loc[i, 'Action'] == 'Short' and quantity > 0 and pror > mtp or pror < stl:
            rate = 1    # 매도 비율
            sell_quantity = quantity * rate     # 매도 수량
            cash += sell_quantity * price * (1-fee)     # 현금 업데이트 (수수료 포함)
            quantity -= sell_quantity   # 수량 업데이트
            dca_level = 0
            sell_pur += 1
            buy_price = None
            pre_price = None
            ar.append(ror)
            # print(f"{data.loc[i, 'Time']} (수익률: {round(ror*100,3)}%) {sell_quantity*price}$ 매도!")
        data.loc[i, '보유현금'] = cash
        data.loc[i, '보유수량'] = quantity
        data.loc[i, '평균단가'] = buy_price
        data.loc[i, '현재수익률'] = ror*100
        data.loc[i, '총자산'] = cash + (quantity*price)
        data.loc[i, '총수익률'] = ((data.loc[i,'총자산'] - start_balance) / start_balance)*100

    print(f"매수 횟수: {buy_pur}번")
    print(f"매도 횟수: {sell_pur}번")
    print(f"매매 최고 수익률: {round(max(data['현재수익률']),3)}%")
    print(f"매매 평균 수익률: {round((sum(ar)/len(ar))*100,3)}%")
    print(f"MDD: {round(min(data['현재수익률']),3)}%")
    print(f"최저 수익률: {round(min(data['총수익률']),3)}%")
    print(f"최고 수익률: {round(max(data['총수익률']),3)}%")
    print(f"최종 수익률: {round(data['총수익률'].iloc[-1],3)}%")

    return data