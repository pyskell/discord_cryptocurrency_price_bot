import requests
import json
import sys
from enum import Enum
from discord.ext import commands
from datetime import datetime, timedelta

RATE_LIMIT_IN_SECONDS = 10

last_query_time = datetime.now() - timedelta(seconds=RATE_LIMIT_IN_SECONDS)
bot = commands.Bot(command_prefix="!", description="Pulls cryptocurrencies by name from CoinmarketCap")
currency_file = open("currency_list.json", "r")
currency_list = json.load(currency_file)

bad_word_file = open("bad_word_list.json", "r")
bad_word_list = json.load(bad_word_file)


class Failure(Enum):
	RATELIMIT = 1
	INVALIDQUERY = 2
	NOTFOUND = 3
	RUDEQUERY = 4


def failure_to_bot_reply(failure, command_name):
	bot_reply = "I literally have no response to that. Contact my creator. Something has gone wrong."

	if failure == Failure.RATELIMIT:
		bot_reply = "You're checking too fast. Can only check for a price once every {} seconds".format(RATE_LIMIT_IN_SECONDS)	
	if failure == Failure.INVALIDQUERY:
		bot_reply = "Sorry I couldn't make sense of that query"
	if failure == Failure.NOTFOUND:
		bot_reply = "Sorry, that symbol was not found"		
	if failure == Failure.RUDEQUERY:
		bot_reply = "Fine. No crypto {}s for you. Jerk.".format(command_name)

	return bot_reply


def get_json_query(get_url, params):
	response = requests.get(get_url, params=params)
	result = response.json()

	return result


def get_ticker(symbol, currency):
	global last_query_time # Global variable, yeah, yeah, I know
	rate_limited = datetime.now() < (last_query_time + timedelta(seconds=RATE_LIMIT_IN_SECONDS))

	if rate_limited:
		return Failure.RATELIMIT

	if symbol.lower() in bad_word_list:
		return Failure.RUDEQUERY

	symbol = symbol.upper()
	if symbol not in currency_list:
		return Failure.NOTFOUND

	get_url = "https://api.coinmarketcap.com/v1/ticker/{}/".format(currency_list[symbol])
	ticker = get_json_query(get_url, {"convert" : currency})	

	return ticker


def parse_ticker_query(arguments):
	arguments = arguments.split()
	symbol = arguments[0]
	currency = "usd"

	if len(arguments) == 2:
		currency = arguments[1].lower()

	symbol = symbol.upper()

	return symbol, currency


def get_price_response(ctx, arguments: str):
	ticker_query = parse_ticker_query(arguments)
	symbol = ticker_query[0]
	currency = ticker_query[1]

	is_member = False
	if ctx is not None:
		members = ctx.message.server.members
		for member in members:
			if member.name.upper() == symbol:
				is_member = True
				break

	if is_member:
		return "I'll give you 'bout tree fiddy"

	bot_reply = failure_to_bot_reply(Failure.NOTFOUND, "price")
	result = get_ticker(symbol, currency)
	if type(result) is not Failure:
		field = "price_{}".format(currency)

		if field in result[0]:
			price = float(result[0][field])

			if price > 1.0:
				price = round(price, 2)
			else:
				price = round(price, 8)

			last_query_time = datetime.now()
			bot_reply = "The current price of {} is {} {:,}".format(symbol, currency.upper(), price)
		else:
			bot_reply = failure_to_bot_reply(Failure.INVALIDQUERY, "price")
	else:
		bot_reply = failure_to_bot_reply(result, "price")

	return bot_reply


@bot.command(pass_context=True)
async def price(ctx, *, arguments: str):
	bot_reply = get_price_response(ctx, arguments)
	print(bot_reply)
	await bot.say(bot_reply)


# TODO: Further deal with the largely duplicate code here.
def get_volume_response(ctx, arguments: str):
	ticker_query = parse_ticker_query(arguments)
	symbol = ticker_query[0]
	currency = ticker_query[1]

	bot_reply = failure_to_bot_reply(Failure.NOTFOUND, "volume")

	result = get_ticker(symbol, currency)
	if type(result) is not Failure:
		field = "24h_volume_{}".format(currency)

		if field in result[0]:
			volume = float(result[0][field])
			last_query_time = datetime.now()
			bot_reply = "The current volume of {} is {} {:,}".format(symbol, currency.upper(), volume)
		else:
			bot_reply = failure_to_bot_reply(Failure.INVALIDQUERY, "volume")
	else:
		bot_reply = failure_to_bot_reply(result, "volume")

	return bot_reply


@bot.command(pass_context=True)
async def volume(ctx, *, arguments: str):
	bot_reply = get_volume_response(ctx, arguments)
	print(bot_reply)
	await bot.say(bot_reply)


if __name__ == "__main__":
	from app.private_settings import TOKEN
	bot.run(TOKEN)
