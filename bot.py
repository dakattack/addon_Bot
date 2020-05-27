# bot.py
import os
import json
import discord
import urllib

from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

class MyClient(discord.Client):
	DBM_URL = "https://addons-ecs.forgesvc.net/api/v2/addon/3358"
	DBM_JSON = urllib.urlopen(DBM_URL)
	DBM_Parse = json.loads(DBM_JSON)
	print(DBM_Parse)
    async def on_ready(self):
        print('Logged on as {0}!'.format(self.user))

    async def on_message(self, message):
        print('Message from {0.author}: {0.content}'.format(message))

client = MyClient()

client.run(TOKEN)