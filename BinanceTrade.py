from binance.client import Client
import pandas as pd
import numpy as np
import requests
import datetime
import yaml

class BinanceTrade:
    def send_message(DISCORD_WEBHOOK_URL, msg):
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

    def get_balance(client, asset='USDT'):
        """잔고 조회"""
        balances = client.get_asset_balance(asset=asset)
        if balances['free'] is not None:
            return balances['free'][:6]+' USDT'
        else:
            return 0

    def get_current_price(client, symbol="BTCUSDT"):
        """현재가 조회"""
        return client.get_symbol_ticker(symbol=symbol)['price']
