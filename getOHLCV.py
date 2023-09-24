import os
import requests
import pandas as pd
from datetime import datetime

# Binance API endpoint URL
url = "https://api.binance.com/api/v1/klines"

# Set the parameters for the API request
symbols = ["SOLUSDT", "TRXUSDT", "LTCUSDT", "STXUSDT", "EOSUSDT", "LINKUSDT"]
intervals = ["15m"]  # ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "1d"]  # 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M

# Convert start date to milliseconds
start_date = datetime(2017, 8, 15)
start_time = int(start_date.timestamp()) * 1000

# Get the current date and time as the end date
end_date = datetime.now()
end_time = int(end_date.timestamp()) * 1000

for symbol in symbols:
    for interval in intervals:
        df_path = f"/Users/ho/Documents/coin/data/{symbol}/"
        df_name = f"{symbol}{interval}.csv"
        if not os.path.exists(df_path):
            os.makedirs(df_path)    # 폴더가 없으면 생성

        fl = os.listdir(df_path)
        if df_name in fl:
            continue    # 파일이 존재하면 통과

        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": 1000,  # Maximum limit per request
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
        df = pd.DataFrame(data_list, columns=['Time', 'Open', 'High', 'Low', 'Close', 'Volume', "close_time",
                                            "quote_asset_volume", "number_of_trades", "taker_buy_base_asset_volume",
                                            "taker_buy_quote_asset_volume", "ignore"])
        df['Time'] = pd.to_datetime(df['Time'], unit='ms')

        # Select only the relevant columns (OHLCV)
        df = df[['Time', 'Open', 'High', 'Low', 'Close', 'Volume']]

        # Convert the OHLCV values to numeric
        df[['Open', 'High', 'Low', 'Close', 'Volume']] = df[['Open', 'High', 'Low', 'Close', 'Volume']].apply(pd.to_numeric)

        # Save the data as a CSV file
        df.to_csv(df_path+df_name, index=False)

        now = datetime.now()
        print(f"{now.strftime('%Y-%m-%d %H:%M')} {df_name} 데이터 저장 완료!")
