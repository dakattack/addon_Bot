import os
import json
import discord
import urllib.request

from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

class addon_Bot(discord.Client):
	async def on_ready(self):
		DBM_URL = "https://addons-ecs.forgesvc.net/api/v2/addon/3358"
		with urllib.request.urlopen(DBM_URL) as url:
			DBM_JSON = url.read()
			DBM_Parse = json.loads(DBM_JSON)
		latestClassic = 0
		while DBM_Parse["latestFiles"][latestClassic]["gameVersionFlavor"] != "wow_classic":
			latestClassic = latestClassic + 1
		print('Logged on as {0}!'.format(self.user))
		message = "A new version of DBM is available! Version: " + DBM_Parse["latestFiles"][latestClassic]["displayName"] + " Be sure to download it here before raid: " +  DBM_Parse["latestFiles"][latestClassic]["downloadUrl"]
		channel = client.get_channel(715301042530549813)
		await channel.send(message)

client = addon_Bot()

client.run(TOKEN)
