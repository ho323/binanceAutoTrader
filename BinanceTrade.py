from binance.client import Client
import pandas as pd
import numpy as np
import requests
import datetime
import yaml

# 유틸 함수
def send_message(DISCORD_WEBHOOK_URL, msg):
    """디스코드 메세지 전송"""
    now = datetime.datetime.now()
    message = {"content": f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] {str(msg)}"}
    requests.post(DISCORD_WEBHOOK_URL, data=message)
    print(message)

def get_balance(client, asset='USDT'):
    """잔고 조회"""
    balances = client.get_asset_balance(asset=asset)
    if balances['free'] is not None:
        return balances['free']+' USDT'
    else:
        return 0

def get_current_price(client, symbol="BTCUSDT"):
    """현재가 조회"""
    return client.get_symbol_ticker(symbol=symbol)['price']

def get_ohlcv(client, ticker="BTCUSDT", interval="1d"):
    data = client.get_historical_klines(
        symbol=ticker,
        interval=interval,
    )
    colums = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close Time', 'Quote asset volume', 'Number of trades', 'Taker buy base asset volume', 'Taker buy quote asset volume', 'Ignore']
    df = pd.DataFrame(data, columns=colums)
    df = df[['Time', 'Open', 'High', 'Low', 'Close', 'Volume']]
    df = df.astype('float')
    df['Time'] = pd.to_datetime(df['Time'], unit='ms')
    # df.set_index('Time', inplace=True)
    return df

def get_heikinashi(df):
    x = pd.DataFrame()
    x['Time'] = df['Time']
    x['Close'] = (df['Open']+df['High']+df['Low']+df['Close']) / 4
    for i in range(len(df)):
        t = df.index[i]
        if i == 0:
            x.loc[t, 'Open'] = (df['Open'].iloc[0]+df['Close'].iloc[0]) / 2
        else:
            x.loc[t, 'Open'] = (x['Open'].iloc[i-1]+x['Close'].iloc[i-1]) / 2
    x['High'] = x.loc[:, ['Open','Close']].join(df['High']).max(axis=1)
    x['Low'] = x.loc[:, ['Open','Close']].join(df['Low']).min(axis=1)
    x['UD'] = ['Up' if o < c else 'Down' for o, c in zip(x['Open'], x['Close'])]
    return x

# 보조지표
def get_ma(df, n=20):
    """이동 평균선 조회"""
    return df['Close'].rolling(n).mean()

def get_ema(df, n=20):
    x = pd.Series()
    k = 2 / (n+1)
    for i in range(len(df)):
        t = df.index[i]
        if i == 0:
            x[i] = df.loc[t, 'Close']
        else:
            x[i] = (df.loc[t, 'Close']*k) + (x[i-1]*(1-k))
    x.index = df.index
    return x

def get_rsi(df, periods=14):
    """RSI 조회"""
    x = pd.DataFrame()
    x['변화량'] = df['Close'] - df['Close'].shift(1)
    x['상승폭'] = np.where(x['변화량']>=0, x['변화량'], 0)
    x['하락폭'] = np.where(x['변화량'] <0, x['변화량'].abs(), 0)
    x['AU'] = x['상승폭'].ewm(alpha=1/periods, min_periods=periods).mean()
    x['AD'] = x['하락폭'].ewm(alpha=1/periods, min_periods=periods).mean()
    x['RSI'] = x['AU'] / (x['AU'] + x['AD']) * 100
    return x['RSI']

def get_macd(df, macd_short=12, macd_long=26, macd_signal=9):
    """MACD 조회"""
    x = pd.DataFrame()
    x["MACD_short"]=df["Close"].ewm(span=macd_short).mean()
    x["MACD_long"]=df["Close"].ewm(span=macd_long).mean()
    x["MACD"]=x.apply(lambda x: (x["MACD_short"]-x["MACD_long"]), axis=1)
    x["MACD_signal"]=x["MACD"].ewm(span=macd_signal).mean()  
    x["MACD_oscillator"]=x.apply(lambda x:(x["MACD"]-x["MACD_signal"]), axis=1)
    return x[['MACD', 'MACD_signal', 'MACD_oscillator']]

def get_bb(df):
    """볼린저 밴드 조회"""
    x = pd.DataFrame()
    x['BB Middle'] = df['Close'].rolling(window=20).mean()
    std = df['Close'].rolling(20).std(ddof=0)
    x['BB Upper'] = x['BB Middle'] + 2 * std
    x['BB Lower'] = x['BB Middle'] - 2 * std
    return x

# 거래 전략
def ma_cross(df,s=20,l=120):
    x = df.copy()
    x['sMA'] = get_ma(df,s)
    x['lMA'] = get_ma(df,l)
    x['Cross'] = 'N'
    for i in range(1,len(df)):
        p = df.index[i-1]
        c = df.index[i]
        if x.loc[c, 'sMA'] == None:
            continue
        elif x.loc[p,'sMA'] < x.loc[p,'lMA'] and x.loc[c,'sMA'] > x.loc[c,'lMA']:
            x.loc[c, 'Cross'] = 'G'
        elif x.loc[p,'sMA'] > x.loc[p,'lMA'] and x.loc[c,'sMA'] < x.loc[c,'lMA']:
            x.loc[c, 'Cross'] = 'D'
    return x['Cross']

def breakout_strategy(df, k=0.5):
    """변동성 돌파 기본 전략"""
    x = pd.DataFrame()
    x['Range'] = (df['High'] - df['Close']).shift(1)
    x['Target Price'] = df['Open'] + x['Range'] * k
    return x['Target Price']

def heikinashi_upswing_strategy(df,s=13,l=21):
    """하이킨아시 업스윙 전략"""
    x = get_heikinashi(df)
    x['Cross'] = ma_cross(x,s,l)
    x['RSI'] = get_rsi(df)
    x['Action'] = 'Stay'
    for i in range(len(df)):
        t = x.index[i]
        if x.loc[t,'UD']=='Up' and x.loc[t,'Cross']=='G':
            x.loc[t,'Action'] = 'Buy'
        elif x.loc[t,'UD']=='Down' and x.loc[t,'Cross']=='D':
            x.loc[t,'Action'] = 'Sell'
    return x


def grid_strategy(df):
    """그리드 현물매매 전략"""
    pass

def torres_strategy(df):
    """토레스 전략"""
    pass