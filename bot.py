import os
import json
import discord
import urllib.request
import sqlite3
from sqlite3 import Error

from dotenv import load_dotenv
from discord.ext import tasks, commands

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

client = discord.Client()

channel = 0

@client.event
async def on_ready():
	print('Logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
	global channel
	channel = client.get_channel(715301042530549813)
	if message.author == client.user:
       		return
	if message.content.startswith('!addon'):
		conn = sqlite3.connect('addons.db')
		c = conn.cursor()
		message = message.content
		message = message.split()
		id = message[1]
		command = "SELECT * FROM addons WHERE id = " + str(id)
		c.execute(command)
		entry = c.fetchone()
		if entry is None:
			apiRequest = "https://addons-ecs.forgesvc.net/api/v2/addon/" + id
			with urllib.request.urlopen(apiRequest) as url:
				jsonFile = url.read()
				addonDict = json.loads(jsonFile)
			latestClassic = 0
			while addonDict["latestFiles"][latestClassic]["gameVersionFlavor"] != "wow_classic":
				latestClassic = latestClassic + 1
			name = addonDict["name"]
			latestVersion = addonDict["latestFiles"][latestClassic]["id"]
			command = 'INSERT INTO addons VALUES(' + str(id) + ', "' + str(name) + '", ' + str(latestVersion) + ')'
			c.execute(command)
			conn.commit()
			c.close()
			conn.close()
			successMessage = "Successfully added " + addonDict["name"] + " to the list of tracked addons!"
			await channel.send(successMessage)
		else:
			failureMessage = "Addon is already being tracked."
			c.close()
			conn.close()
			await channel.send(failureMessage)
@tasks.loop(hours=2)
async def updateAlert():
	await client.wait_until_ready()
	global channel
	channel = client.get_channel(715301042530549813)
	conn = sqlite3.connect('addons.db')
	c = conn.cursor()
	c.execute("SELECT * FROM addons")
	row = c.fetchone()

	while row is not None:
		apiRequest = "https://addons-ecs.forgesvc.net/api/v2/addon/" + str(row[0])
		with urllib.request.urlopen(apiRequest) as url:
			jsonFile = url.read()
			addonDict = json.loads(jsonFile)
		latestClassic = 0
		while addonDict["latestFiles"][latestClassic]["gameVersionFlavor"] != "wow_classic":
			latestClassic = latestClassic + 1
		if addonDict["latestFiles"][latestClassic]["id"] != row[2]:
			command = "UPDATE addons SET latestVersion = " + str(addonDict["latestFiles"][latestClassic]["id"]) +" WHERE id = " + str(row[0])
			c.execute(command)
			conn.commit()
			updateMessage = "A new version of " + addonDict["name"] + " is available! Version: " + addonDict["latestFiles"][latestClassic]["displayName"] + " Be sure to download it here before raid: " +  addonDict["latestFiles"][latestClassic]["downloadUrl"]
			await channel.send(updateMessage)
		row = c.fetchone()

	c.close()
	conn.close()

updateAlert.start()
client.run(TOKEN)
