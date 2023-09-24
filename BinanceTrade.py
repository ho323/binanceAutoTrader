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
    message = {"content": f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] \n{str(msg)}"}
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

def get_ohlcv(client, ticker="BTCUSDT", interval="1d",limit=100):
    data = client.get_historical_klines(
        symbol=ticker,
        interval=interval,
        limit=limit
    )
    colums = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close Time', 'Quote asset volume', 'Number of trades', 'Taker buy base asset volume', 'Taker buy quote asset volume', 'Ignore']
    df = pd.DataFrame(data, columns=colums)
    df = df[['Time', 'Open', 'High', 'Low', 'Close', 'Volume']]
    df = df.astype('float')
    df['Time'] = pd.to_datetime(df['Time'], unit='ms')
    # df.set_index('Time', inplace=True)
    return df

def get_all_ohlcv(symbol="BTCUSDT", interval="1d", start_date=datetime.datetime(2017,1,1), end_date=datetime.datetime.now()):
    """
    모든 OHLCV 읽기
    interval: # 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M
    """
    # Binance API endpoint URL
    url = "https://api.binance.com/api/v1/klines"

    # Convert start date to milliseconds (2016년 6월 1일)
    start_time = int(start_date.timestamp()) * 1000

    # Get the current date and time as the end date
    end_time = int(end_date.timestamp()) * 1000

    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1000,      # Maximum limit per request
        "startTime": start_time,
        "endTime": end_time
    }

    # List to store data
    data_list = []

    while True:
        response = requests.get(url, params=params)
        data = response.json()
        
        if len(data) == 0:
            break
        
        data_list.extend(data)
        
        # Update the start time for the next request
        params["startTime"] = data[-1][0] + 1

    # Convert the response data into a DataFrame
    df = pd.DataFrame(data_list, columns=["Time", "Open", "High", "Low", "Close", "Volume", "close_time", "quote_asset_volume", "number_of_trades", "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"])
    df["Time"] = pd.to_datetime(df["Time"], unit="ms")

    # Select only the relevant columns (OHLCV)
    df = df[["Time", "Open", "High", "Low", "Close", "Volume"]]

    # Convert the OHLCV values to numeric
    df[["Open", "High", "Low", "Close", "Volume"]] = df[["Open", "High", "Low", "Close", "Volume"]].apply(pd.to_numeric)

    # Print the DataFrame with the OHLCV data
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

def get_rsi(data, period=14):
    """RSI 조회"""
    delta = data['Close'].diff(1)
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

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

def get_change(source, length=None):
    """
    종가 입력
    """
    if length is None:
        # length가 주어지지 않은 경우, 모든 종가의 변화량 계산
        changes = [0] + [source[i] - source[i - 1] for i in range(1, len(source))]
    else:
        # length가 주어진 경우, 최근 length일 동안의 종가의 변화량 계산
        if length >= len(source):
            raise ValueError("length는 source 리스트의 길이보다 작아야 합니다.")
        changes = [0 for _ in range(length)] + [
            source[i] - source[i - length] for i in range(length, len(source))]
    return changes

def get_rma(source, length):
    """
    종가 입력
    """
    if length <= 0 or length > len(source):
        raise ValueError("Invalid length value")

    rma = [None] * len(source)

    # Calculate the first RMA value as the simple moving average (SMA) of the first 'length' elements
    sma = sum(source[:length]) / length
    rma[length - 1] = sma

    # Calculate RMA for the rest of the data
    for i in range(length, len(source)):
        rma[i] = (rma[i - 1] * (length - 1) + source[i]) / length

    return rma

def get_mfi(data, period=14):
    """MFI 계산"""
    typical_price = (data['High'] + data['Low'] + data['Close']) / 3
    raw_money_flow = typical_price * data['Volume']
    
    money_flow_positive = raw_money_flow.where(data['Close'] > data['Close'].shift(1), 0)
    money_flow_negative = raw_money_flow.where(data['Close'] < data['Close'].shift(1), 0)
    
    money_ratio = money_flow_positive.rolling(window=period).sum() / money_flow_negative.rolling(window=period).sum()
    mfi = 100 - (100 / (1 + money_ratio))
    
    return mfi

def get_rmf(data):
    """RMF 계산"""
    return (get_rsi(data) + get_mfi(data)) / 2

def get_vwma(data, period=14):
    """VWMA 계산"""
    data['Weighted_Price'] = data['Close'] * data['Volume']
    return data['Weighted_Price'].rolling(window=period).sum() / data['Volume'].rolling(window=period).sum()

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

def strategy_breakout(df, k=0.5):
    """변동성 돌파 기본 전략"""
    x = pd.DataFrame()
    x['Range'] = (df['High'] - df['Close']).shift(1)
    x['Target Price'] = df['Open'] + x['Range'] * k
    return x['Target Price']

def strategy_heikinashi_upswing(df,s=13,l=21):
    """하이킨아시 업스윙 전략"""
    x = get_heikinashi(df)
    x['Cross'] = ma_cross(x,s,l)
    x['RSI'] = get_rsi(df)
    x['Action'] = 'Stay'
    for i in range(len(df)):
        t = x.index[i]
        if x.loc[t,'UD']=='Up' and x.loc[t,'Cross']=='G':
            x.loc[t,'Action'] = 'Long'
        elif x.loc[t,'UD']=='Down' and x.loc[t,'Cross']=='D':
            x.loc[t,'Action'] = 'Short'
    return x


def strategy_grid(df):
    """그리드 현물매매 전략"""
    pass

def strategy_toress(df):
    """토레스 전략"""
    pass

def strategy_vwma_long(df, length=14, change_percentage=1.4, below=55, above=100):
    """
    VWMA 현물 15분봉 전략 v2

    change_percentage: SRP %
    below, above: RMF 임계값

    매수 조건: VWMA 밴드 하단 아래, RMF 입력한 임계값 아래
    매도 조건: VWMA 밴드 상단 위, RMF 입력한 임계값 위
    """
    length = 14
    change_percentage = 1.4 # SRP

    core = get_vwma(df, length)
    vwma_above = core * (1 + (change_percentage / 100))
    vwma_below = core * (1 - (change_percentage / 100))

    rsi = get_rsi(df, 7)
    mfi = get_mfi(df, 7)
    rmf = [None if rsi[i] is None else abs(rsi[i] + (mfi[i]/2)) for i in range(len(rsi))]
    
    df['RMF'] = rmf
    df['Action'] = 'Stay'
    df.loc[(df['Low'] <= vwma_below) & (df['RMF'] < below), 'Action'] = 'Long'
    df.loc[(df['High'] >= vwma_above) & (df['RMF'] > above), 'Action'] = 'Short'

    return df