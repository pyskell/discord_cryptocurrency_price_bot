import bot
import json
import sys

if __name__ == "__main__":
	if sys.argv[1] == "!price":
		bot_reply = bot.get_price(None, " ".join(sys.argv[2:]))
		print(bot_reply)
