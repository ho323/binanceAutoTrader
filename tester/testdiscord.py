import asyncio
import discord
from discord.ext import commands
from binance.client import Client
import yaml
import time
from binancebot import BinanceBot

with open('/Users/ho/Documents/config.yaml', encoding='UTF-8') as f:
    _cfg = yaml.load(f, Loader=yaml.FullLoader)
API_KEY = _cfg['APP_KEY']
API_SECRET = _cfg['APP_SECRET']
DISCORD_TOKEN = _cfg['DISCORD_TOKEN']
symbol = 'BTCUSDT'

binance_client = Client(API_KEY, API_SECRET)

intents = discord.Intents.default()
intents.message_content = True
intents.typing = False  # 사용자가 타이핑 중인 상태를 봇이 무시
intents.presences = False  # 사용자 활동 정보를 봇이 무시
discord_bot = commands.Bot(command_prefix='!', intents=intents)

on_trading = False

async def binance_trading_bot(ctx):
    global on_trading
    while on_trading:
        await ctx.send("1")
        await asyncio.sleep(2)

@discord_bot.event
async def on_ready():
    print(f'Logged in as {discord_bot.user.name}')

@discord_bot.event
async def on_command_error(ctx, error):
    await ctx.send(error)

@discord_bot.command()
async def set_api(ctx, key, secret):
    global API_KEY
    global API_SECRET
    global binance_client
    API_KEY = key
    API_SECRET = secret
    binance_client = Client(API_KEY, API_SECRET)
    await ctx.send(f'API가 설정되었습니다.')

@discord_bot.command()
async def balance(ctx):
    "현재 선물 USDT 잔고"
    account = binance_client.futures_account()
    for balance in account :
        if balance['asset'] == 'USDT':
            await ctx.send('USDT balance:', balance['balance'])
            break

@discord_bot.command()
async def set_coin(ctx, c: str):
    # 거래 코인 설정
    global symbol
    symbol = c
    await ctx.send(f'거래 코인이 {c}으로 설정되었습니다.')

@discord_bot.command()
async def set_leverage(ctx, leverage: int):
    # 레버리지 설정
    binance_client.futures_change_leverage(
        symbol=symbol,
        leverage=leverage,
    )
    await ctx.send(f'{symbol}의 레버리지가 {leverage}로 설정되었습니다.')

@discord_bot.command()
async def set_margin_type(ctx, margin_type):
    binance_client.futures_change_margin_type(
        symbol=symbol,
        margin_type=margin_type,
    )
    await ctx.send(f'{symbol}의 선물 마진 타입이 {margin_type}로 설정되었습니다.')

@discord_bot.command()
async def start_trade(ctx):
    # 매매 시작
    global on_trading
    on_trading = True
    await ctx.send('매매를 시작합니다.')
    await binance_trading_bot(ctx)

@discord_bot.command()
async def stop_trade(ctx):
    # 매매 종료
    global on_trading
    on_trading = False
    await ctx.send('매매를 중단합니다.')

@discord_bot.command()
async def exit(ctx):
    # 봇 종료
    await ctx.send('봇을 종료합니다.')
    await discord_bot.close()

discord_bot.run(DISCORD_TOKEN)
