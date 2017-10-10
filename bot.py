import requests
import json
import sys
from discord.ext import commands
from datetime import datetime, timedelta

from app.private_settings import TOKEN

RATE_LIMIT_IN_SECONDS = 10

last_query_time = datetime.now()
bot = commands.Bot(command_prefix="!", description="Pulls cryptocurrencies by name from CoinmarketCap")
currency_file = open("currency_list.json", "r")
currency_list = json.load(currency_file)

#@bot.event()
#async def on_ready():
#	print("Ready to go boss!")

@bot.command()
async def price(*, arguments: str):
	global last_query_time # Global variable, yeah, yeah, I know

	arguments = arguments.split()
	symbol = arguments[0]
	currency = "usd"

	if len(arguments) == 2:
		currency = arguments[1].lower()

	symbol = symbol.upper()
	bot_reply = "Sorry, that symbol ({}) was not found".format(symbol)
	rate_limited = datetime.now() < (last_query_time + timedelta(seconds=RATE_LIMIT_IN_SECONDS))
	if (not rate_limited) and (symbol in currency_list):
#		last_query_time = datetime.now()
		url = "https://api.coinmarketcap.com/v1/ticker/{}/?convert={}".format(currency_list[symbol], currency)
		response = requests.get(url)
		result = response.json()

		price_field = "price_{}".format(currency)

		if price_field in result[0]:
			last_query_time = datetime.now()
			bot_reply = "The current price of {} is {} {}".format(symbol, currency.upper(), result[0][price_field])
		else:
			bot_reply = "Sorry I couldn't make sense of that query"
	elif rate_limited:
		bot_reply = "You're checking too fast. Can only check for a price once every {} seconds".format(RATE_LIMIT_IN_SECONDS)

	print(bot_reply)
	await bot.say(bot_reply)

if __name__ == "__main__":
	bot.run(TOKEN)
