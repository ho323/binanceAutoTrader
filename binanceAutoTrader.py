from binance.client import Client
import pandas as pd
import numpy as np
import requests
import datetime
import yaml

with open('/Users/ho/Documents/config.yaml', encoding='UTF-8') as f:
    _cfg = yaml.load(f, Loader=yaml.FullLoader)
APP_KEY = _cfg['APP_KEY']
APP_SECRET = _cfg['APP_SECRET']
DISCORD_WEBHOOK_URL = _cfg['DISCORD_WEBHOOK_URL']

client = Client(api_key=APP_KEY, api_secret=APP_SECRET)

def send_message(msg):
    """디스코드 메세지 전송"""
    now = datetime.datetime.now()
    message = {"content": f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] {str(msg)}"}
    requests.post(DISCORD_WEBHOOK_URL, data=message)
    print(message)

def get_ma(df, l=20):
    """이동 평균선 조회"""
    return df['Close'].rolling(l).mean()

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

def get_breakout(df, k):
    """변동성 돌파 여부 조회"""
    target_price = df.iloc[-1]['Close'] + (df.iloc[-1]['High'] - df.iloc[0]['Low']) * k
    return target_price

def get_balance(asset='USDT'):
    """잔고 조회"""
    balances = client.get_asset_balance(asset=asset)
    if balances['free'] is not None:
        return balances['free'][:6]+' USDT'
    else:
        return 0

def get_current_price(symbol="BTCUSDT"):
    """현재가 조회"""
    return client.get_symbol_ticker(symbol=symbol)['price']

def get_df(ticker="BTCUSDT", interval="1d"):
    data = client.get_historical_klines(
        symbol=ticker,
        interval=interval,
    )
    colums = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close Time', 'Quote asset volume', 'Number of trades', 'Taker buy base asset volume', 'Taker buy quote asset volume', 'Ignore']
    df = pd.DataFrame(data, columns=colums)
    df = df[['Time', 'Open', 'High', 'Low', 'Close', 'Volume']]
    df = df.astype('float')
    df['Time'] = pd.to_datetime(df['Time'], unit='ms')
    df.set_index('Time', inplace=True)
    df['MA20'] = get_ma(df, 20)
    df['RSI'] = get_rsi(df, 14)
    df[['MACD', 'MACD Signal', 'MACD Oscillator']] = get_macd(df)
    df[['BB Middle', 'BB Upper', 'BB Lower']] = get_bb(df)
    df = df.dropna(axis=0)
    return df


ticker = "BTCUSDT"
interval='1d'   # 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M

balance = 1000.0

df = get_df()
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