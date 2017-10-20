import requests
import json
import sys
from collections import OrderedDict
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


def failure_to_bot_reply(failure):
	bot_reply = "I literally have no response to that. Contact my creator. Something has gone wrong."

	if failure == Failure.RATELIMIT:
		bot_reply = "You're checking too fast. Can only check for a price once every {} seconds".format(RATE_LIMIT_IN_SECONDS)	
	if failure == Failure.INVALIDQUERY:
		bot_reply = "Sorry I couldn't make sense of that query"
	if failure == Failure.NOTFOUND:
		bot_reply = "Sorry, that symbol was not found"		
	if failure == Failure.RUDEQUERY:
		bot_reply = "Fine. No ticker for you. Jerk."

	return bot_reply


def get_ticker_endpoint(symbol, currency):
	global last_query_time # Global variable, yeah, yeah, I know
	rate_limited = datetime.now() < (last_query_time + timedelta(seconds=RATE_LIMIT_IN_SECONDS))

	if rate_limited:
		return Failure.RATELIMIT

	if symbol.lower() in bad_word_list or currency.lower() in bad_word_list:
		return Failure.RUDEQUERY

	symbol = symbol.upper()
	if symbol not in currency_list:
		return Failure.NOTFOUND

	get_url = "https://api.coinmarketcap.com/v1/ticker/{}/".format(currency_list[symbol])
	response = requests.get(get_url, params={"convert" : currency})
	ticker = response.json()

	return ticker


def parse_arguments(arguments):

	if len(arguments) == 0:
		return None, None

	arguments = arguments.split()
	symbol = arguments[0]
	currency = "usd"

	if len(arguments) == 2:
		currency = arguments[1].lower()

	symbol = symbol.upper()

	return symbol, currency


def get_price_reply(ctx, arguments):
	bot_reply = failure_to_bot_reply(Failure.NOTFOUND)

	symbol, currency = parse_arguments(arguments)
	if (symbol is None) or (currency is None):
		return bot_reply

	is_member = False
	if ctx is not None:
		members = ctx.message.server.members
		for member in members:
			if member.name.upper() == symbol:
				is_member = True
				break

	if is_member:
		return "I'll give you 'bout tree fiddy"

	fields = OrderedDict([("Volume" , "price_{}".format(currency))])
	bot_reply = get_ticker_reply(arguments, fields)

	return bot_reply


@bot.command(pass_context=True)
async def price(ctx, *, arguments: str):
	bot_reply = get_price_reply(ctx, arguments)
	print(bot_reply)
	await bot.say(bot_reply)


def get_volume_reply(arguments):
	_, currency = parse_arguments(arguments)
	fields = OrderedDict([("Volume" , "24h_volume_{}".format(currency))])
	bot_reply = get_ticker_reply(arguments, fields)

	return bot_reply


@bot.command()
async def volume(*, arguments: str):
	bot_reply = get_volume_reply(arguments)
	print(bot_reply)
	await bot.say(bot_reply)


def get_ticker_reply(arguments, fields=None):
	bot_reply = failure_to_bot_reply(Failure.NOTFOUND)
	
	symbol, currency = parse_arguments(arguments)
	if (symbol is None) or (currency is None):
		return bot_reply

	result = get_ticker_endpoint(symbol, currency)
	if fields is None:
		fields = OrderedDict([("Price" , "price_{}".format(currency)),
					("Volume" , "24h_volume_{}".format(currency)),
					("% Change (1h)" , "percent_change_1h"),
					("% Change (24h)" , "percent_change_24h"),
					("% Change (7d)" , "percent_change_7d")
				])

	if type(result) is not Failure:
		reply = []
		for key in fields:
			field = fields[key]
			if field in result[0]:
				value = float(result[0][field])
				if "percent_change" in field:
					reply.append("{}: {:+}%".format(key, value))
				else:
					reply.append("{}: {:,}".format(key, value))
		bot_reply = "{} (in {}) - ".format(symbol, currency.upper()) + " | ".join(reply)
		last_query_time = datetime.now()
	else:
		bot_reply = failure_to_bot_reply(result)

	return bot_reply


@bot.command()
async def ticker(*, arguments: str):
	bot_reply = get_ticker_reply(arguments)
	print(bot_reply)
	await bot.say(bot_reply)


if __name__ == "__main__":
	from app.private_settings import TOKEN
	bot.run(TOKEN)
