from binance.client import Client
from binance.exceptions import BinanceAPIException
import pandas as pd
import datetime
import time

class BinanceBot():
    def __init__(self, key, secret, ticker, interval, strategy, dca_levels, dcl, mtp, stl):
        self.API_KEY = key
        self.API_SECRET = secret
        self.client = Client(api_key=self.API_KEY, api_secret=self.API_SECRET)
        
        self.ticker = ticker
        self.interval = interval
        self.dca_levels = dca_levels  # 분할매수 비중 (리스트 형식)
        self.dca_level = 0
        self.buy_price = None   # 평균단가
        self.pre_price = None   # 직전 매수가
        self.ror = 0        # 평균단가 대비 수익률
        self.pror = -1       # 직전 매수가 대비 수익률
        self.dcl = dcl      # 분할매수 최소 미만 수익률 
        self.mtp = mtp      # 청산시 최소 수익률
        self.stl = stl      # Stop Loss 설정
        self.fee = 0.001

        self.balance = 0
        self.on_trading = False
        self.strategy = strategy
        self.current_action = 'Stay'
        self.prev_action = 'Stay'

    async def get_ohlcv(self, limit=50):
        # 코인 OHLCV 불러오기
        data = self.client.get_historical_klines(
            symbol=self.ticker,
            interval=self.interval,
            limit=limit
        )
        colums = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close Time', 'Quote asset volume', 'Number of trades', 'Taker buy base asset volume', 'Taker buy quote asset volume', 'Ignore']
        df = pd.DataFrame(data, columns=colums)
        df = df[['Time', 'Open', 'High', 'Low', 'Close', 'Volume']]
        df = df.astype('float')
        df['Time'] = pd.to_datetime(df['Time'], unit='ms')
        return df

    async def get_balance(self):
        # 현재 USDT
        account = self.client.futures_account()
        for balance in account:
            if balance['asset'] == 'USDT':
                return balance['balance']
            
    async def get_futures_position(self):
        # 현재 포지션
        position_info = self.client.futures_position_information(symbol=self.ticker)
        for position in position_info:
            if position['symbol'] == self.ticker:
                return position['positionAmt']
        return 0  # 해당 심볼의 포지션을 찾지 못한 경우 0을 반환

    async def set_strategy(self, st):
        # 매매 전략 설정
        self.strategy = st

    async def stop_trading(self):
        # 매매 종료
        self.on_trading = False

    async def trading(self):
        # 매매 시작
        self.balance = self.get_balance()
        self.on_trading = True
        while self.on_trading:
            try:
                time.sleep(1)
                now = datetime.datetime.now()
                df = self.get_ohlcv(client=self.client,ticker=self.ticker,interval=self.interval,limit=50)
                st = self.strategy(df)
                self.current_action = st['Action'].iloc[-1]
                print(f"{now}, {self.ticker}:{df['Close'].iloc[-1]}$, {self.current_action}")

                if self.current_action != self.prev_action:
                    price = self.client.get_symbol_ticker(symbol=self.ticker)['price']   # 현재가
                    self.pror = (price-self.pre_price) / self.pre_price if self.pre_price!=None else -1

                    # 매수 신호
                    if self.current_action == 'Long' and self.dca_level < len(self.dca_levels) and self.pror < self.dcl:
                        buy_rate = self.dca_levels[self.dca_level]
                        self.balance = self.get_balance()
                        buy_quantity = self.balance * buy_rate / price * (1-self.fee)
                        self.pre_price = price
                        self.dca_level += 1
                        self.client.futures_create_order(
                            symbol=self.ticker,
                            timeInForce='GTC',
                            type='MARKET',  # LIMIT, MARKET
                            side='BUY',
                            quantity=buy_quantity,
                        )
                        self.balance = self.get_balance()
                    
                    # 매도 신호
                    elif self.current_action == 'Short' and self.dca_level > 0 and (self.pror > self.mtp or self.pror < self.stl):
                        sell_rate = 1
                        sell_quantity = self.get_futures_position() * sell_rate
                        self.pre_price = None
                        self.dca_level = 0
                        self.client.futures_create_order(
                            symbol=self.ticker,
                            timeInForce='GTC',
                            type='MARKET',
                            side='SELL',
                            quantity=sell_quantity,
                        )
                        self.balance = self.get_balance()

            except BinanceAPIException as e:
                print(f"Binance Error \n{e}")
                self.on_trading = False
                break
            except Exception as e:
                print(e)
                self.on_trading = False
                break
    
    