import requests
import json
import sys
from discord.ext import commands
from datetime import datetime, timedelta

RATE_LIMIT_IN_SECONDS = 10

last_query_time = datetime.now() - timedelta(seconds=RATE_LIMIT_IN_SECONDS)
bot = commands.Bot(command_prefix="!", description="Pulls cryptocurrencies by name from CoinmarketCap")
currency_file = open("currency_list.json", "r")
currency_list = json.load(currency_file)

bad_word_file = open("bad_word_list.json", "r")
bad_word_list = json.load(bad_word_file)


def get_json_query(get_url, params):
	response = requests.get(get_url, params=params)
	result = response.json()

	return result


def get_price(ctx, arguments: str):
	global last_query_time # Global variable, yeah, yeah, I know

	arguments = arguments.split()
	symbol = arguments[0]
	currency = "usd"

	if len(arguments) == 2:
		currency = arguments[1].lower()

	symbol = symbol.upper()
	bot_reply = "Sorry, that symbol ({}) was not found".format(symbol)


	is_member = False
	if ctx is not None:
		members = ctx.message.server.members
		for member in members:
			if member.name.upper() == symbol:
				is_member = True
				break

	rate_limited = datetime.now() < (last_query_time + timedelta(seconds=RATE_LIMIT_IN_SECONDS))
	if (not rate_limited) and (symbol in currency_list):
		get_url = "https://api.coinmarketcap.com/v1/ticker/{}/".format(currency_list[symbol])
		result = get_json_query(get_url, {"convert" : currency})

		price_field = "price_{}".format(currency)
		price = float(result[0][price_field])

		if price_field in result[0]:
			last_query_time = datetime.now()
			bot_reply = "The current price of {} is {} {:.8f}".format(symbol, currency.upper(), price)
		else:
			bot_reply = "Sorry I couldn't make sense of that query"
	elif rate_limited:
		bot_reply = "You're checking too fast. Can only check for a price once every {} seconds".format(RATE_LIMIT_IN_SECONDS)
	elif is_member:
		bot_reply = "I'll give you 'bout tree fiddy"

	if symbol.lower() in bad_word_list:
		bot_reply = "Fine. No crypto prices for you. Jerk."

	return bot_reply


@bot.command(pass_context=True)
async def price(ctx, *, arguments: str):
	bot_reply = get_price(ctx, arguments)
	print(bot_reply)
	await bot.say(bot_reply)


if __name__ == "__main__":
	from app.private_settings import TOKEN
	bot.run(TOKEN)
