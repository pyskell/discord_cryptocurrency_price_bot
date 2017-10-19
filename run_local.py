import bot
import json
import sys

if __name__ == "__main__":
	command = sys.argv[1]
	arguments = " ".join(sys.argv[2:])

	bot_reply = "Invalid command"
	if command == "!price":
		bot_reply = bot.get_price_response(None, arguments)
	if command == "!volume":
		bot_reply = bot.get_volume_response(None, arguments)
	
	print(bot_reply)