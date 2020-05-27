# bot.py
import os
import json
import discord
import urllib.request

from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

class MyClient(discord.Client):
	DBM_URL = "https://addons-ecs.forgesvc.net/api/v2/addon/3358"
	with urllib.request.urlopen(DBM_URL) as url:
		DBM_JSON = url.read()
		DBM_Parse = json.loads(DBM_JSON)
	print(DBM_Parse)
	async def on_ready(self):
		print('Logged on as {0}!'.format(self.user))

	async def on_message(self, message):
		print('Message from {0.author}: {0.content}'.format(message))

client = MyClient()

client.run(TOKEN)
