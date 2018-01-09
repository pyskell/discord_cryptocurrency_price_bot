import requests
import json

ticker_url = "https://api.coinmarketcap.com/v1/ticker/"
response = requests.get(ticker_url, params={"limit" : 0})
ticker = response.json()

currency_dict = {}

for item in ticker:
    currency_dict[item["symbol"]] = item["id"]

with open('currency_list.json', 'w') as file:
    json.dump(currency_dict, file)