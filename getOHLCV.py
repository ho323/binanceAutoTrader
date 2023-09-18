import requests
import pandas as pd
from datetime import datetime

# Binance API endpoint URL
url = "https://api.binance.com/api/v1/klines"

# Set the parameters for the API request
symbols = ["BTCUSDT","ETHUSDT","XRPUSDT","BNBUSDT","ADAUSDT","DOGEUSDT"]
interval='15m'   # 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M


# Convert start date to milliseconds (2016년 6월 1일)
start_date = datetime(2017, 8, 15)
start_time = int(start_date.timestamp()) * 1000

# Get the current date and time as the end date
end_date = datetime.now()
end_time = int(end_date.timestamp()) * 1000

for symbol in symbols:
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
    df = pd.DataFrame(data_list, columns=["timestamp", "open", "high", "low", "close", "volume", "close_time", "quote_asset_volume", "number_of_trades", "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

    # Select only the relevant columns (OHLCV)
    df = df[["timestamp", "open", "high", "low", "close", "volume"]]

    # Convert the OHLCV values to numeric
    df[["open", "high", "low", "close", "volume"]] = df[["open", "high", "low", "close", "volume"]].apply(pd.to_numeric)
    
    now = datetime.now()
    df.to_excel(f"data/{symbol}/{symbol}{interval}.xlsx")
    print(f"{now.strftime('%Y-%m-%d %H:%M')} {symbol} 완료!")