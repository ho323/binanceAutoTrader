import discord
from discord.ext import commands
from binance.client import Client
import yaml
# from BinanceTrade import *
# import time
# from binance.exceptions import BinanceAPIException

with open('/Users/ho/Documents/config.yaml', encoding='UTF-8') as f:
    _cfg = yaml.load(f, Loader=yaml.FullLoader)
API_KEY = _cfg['APP_KEY']
API_SECRET = _cfg['APP_SECRET']
DISCORD_TOKEN = _cfg['DISCORD_TOKEN']
symbol = 'BTCUSDT'

client = Client(API_KEY, API_SECRET)
intents = discord.Intents.default()
intents.message_content = True
intents.typing = False  # 사용자가 타이핑 중인 상태를 봇이 무시합니다.
intents.presences = False  # 사용자 활동 정보를 봇이 무시합니다.
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

@bot.event
async def on_command_error(ctx, error):
    await ctx.send(error)

@bot.command()
async def set_api(ctx, key, secret):
    global API_KEY
    global API_SECRET
    global client
    API_KEY = key
    API_SECRET = secret
    client = Client(API_KEY, API_SECRET)
    await ctx.send(f'API가 설정되었습니다.')

@bot.command()
async def set_api_secret(ctx, secret):
    global API_SECRET
    API_SECRET = secret
    await ctx.send(f'API Secret이 설정되었습니다.')

@bot.command()
async def balance(ctx):
    "현재 선물 USDT 잔고"
    account = client.futures_account()
    for balance in account :
        if balance['asset'] == 'USDT':
            ctx.send('USDT balance:', balance['balance'])
            break

@bot.command()
async def set_coin(ctx, c: str):
    # 거래 코인 설정
    global symbol
    symbol = c
    await ctx.send(f'거래 코인이 {c}으로 설정되었습니다.')

@bot.command()
async def set_leverage(ctx, leverage: int):
    # 레버리지 설정
    client.futures_change_leverage(
        symbol=symbol,
        leverage=leverage,
    )
    await ctx.send(f'레버리지가 {leverage}로 설정되었습니다.')

@bot.command()
async def set_margin_type(ctx, margin_type):
    client.futures_change_margin_type(
        symbol=symbol,
        margin_type=margin_type,
    )
    await ctx.send(f'선물 마진 타입이 {margin_type}로 설정되었습니다.')

@bot.command()
async def stop(ctx):
    # 종료
    await ctx.send('거래를 종료합니다.')
    await exit()

bot.run(DISCORD_TOKEN)