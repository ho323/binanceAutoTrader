import yaml
import discord
from discord.ext import commands
from binancebot import BinanceBot
from binance.exceptions import BinanceAPIException
import tratingtool
import pandas as pd
import datetime
import time


with open('/Users/ho/Documents/config.yaml', encoding='UTF-8') as f:
    _cfg = yaml.load(f, Loader=yaml.FullLoader)
API_KEY = _cfg['API_KEY']
API_SECRET = _cfg['API_SECRET']
DISCORD_TOKEN = _cfg['DISCORD_TOKEN']

# 디스코드 봇 설정
intents = discord.Intents.default()
intents.message_content = True
intents.typing = False  # 사용자가 타이핑 중인 상태를 봇이 무시
intents.presences = False  # 사용자 활동 정보를 봇이 무시
discord_bot = commands.Bot(command_prefix='!', intents=intents)


# 매매 초기 설정
strategy = tratingtool.strategy_vwma_long   # 전략
start_ticker = "DOGEUSDT"
interval='15m'   # 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M
dca_levels = [0.3,0.5,1.0]      # 분할매수 비율
dcl = -0.02 # 분할매수 진입 최소 수익률 
mtp = -1    # Min Take Profit 매도시 최소 수익률 (미사용 시 -1)
stl = -1    # Stop Loss (미사용 시 -1)

# 매매 봇
binance_bot = BinanceBot(
    key=API_KEY,
    secret=API_SECRET,
    ticker=start_ticker,
    interval=interval,
    strategy=strategy,
    dca_levels=dca_levels,
    dcl=dcl,
    mtp=mtp,
    stl=stl,
)

async def binance_trading_bot():
    # 매매 시작
    await binance_bot.trading()

@discord_bot.event
async def on_ready():
    print(f'Logged in as {discord_bot.user.name}')

@discord_bot.event
async def on_command_error(ctx, error):
    await ctx.send(error)

@discord_bot.command()
async def 잔고(ctx):
    # 현재 선물 USDT 잔고
    usdt = await binance_bot.get_balance()
    await ctx.send(f"현재 USDT 잔고: {usdt}")

@discord_bot.command()
async def 현재포지션(ctx):
    position = await binance_bot.get_futures_position()
    position = float(position)
    if position > 0:
        sign = 'Long'
    elif position < 0:
        sign = 'Short'
    else:
        sign = ''
    ror = binance_bot.ror
    await ctx.send(f"현재 포지션: {binance_bot.ticker} {position} {sign}")
    await ctx.send(f"수익률: {ror}%")

@discord_bot.command()
async def 코인설정(ctx, coin:str, interval:str):
    # 거래 코인 설정
    binance_bot.ticker = coin
    binance_bot.interval = interval
    await ctx.send(f'거래 코인이 {coin}/{interval}으로 설정되었습니다.')

@discord_bot.command()
async def 레버리지설정(ctx, leverage: int):
    # 레버리지 설정
    binance_bot.client.futures_change_leverage(
        symbol=binance_bot.ticker,
        leverage=leverage,
    )
    await ctx.send(f'{binance_bot.ticker}의 레버리지가 {leverage}로 설정되었습니다.')

@discord_bot.command()
async def 마진타입설정(ctx, margin_type):

    await binance_bot.client.futures_change_margin_type(
        symbol=binance_bot.ticker,
        margin_type=margin_type,
    )
    await ctx.send(f'{binance_bot.ticker}의 선물 마진 타입이 {margin_type}로 설정되었습니다.')

@discord_bot.command()
async def 전략설정(ctx, st):
    binance_bot.strategy = st
    await ctx.send(f'매매 전략이 {st}로 설정되었습니다.')

@discord_bot.command()
async def 매매시작(ctx):
    # 매매 시작
    await ctx.send('매매를 시작합니다.')
    await ctx.send(f'현재 {binance_bot.ticker} 가격: {await binance_bot.get_current_price()}')
    await binance_trading_bot()

@discord_bot.command()
async def 매매종료(ctx):
    # 매매 종료
    binance_bot.on_trading = False
    await ctx.send('매매를 중단합니다.')

# @discord_bot.command()
# async def 종료(ctx):
#     # 봇 종료
#     await ctx.send('봇을 종료합니다.')
#     await discord_bot.close()


discord_bot.run(DISCORD_TOKEN)
