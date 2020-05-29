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
	failureMessage = "Please enter a valid addon ID"
	notFoundMessage = "Addon with that ID was not found."
	channel = client.get_channel(715301042530549813)
	if message.author == client.user:
       		return
	if message.content.startswith('!addon'):
		conn = sqlite3.connect('addons.db')
		c = conn.cursor()
		message = message.content
		message = message.split()
		id = message[1]
		if intCheck(id):
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
				try:
					role = message[2]
				except IndexError:
					role = "here"
				command = 'INSERT INTO addons VALUES(' + str(id) + ', "' + str(name) + '", ' + str(latestVersion) + ', ' + role + ')'
				c.execute(command)
				conn.commit()
				c.close()
				conn.close()
				successMessage = "Successfully added " + addonDict["name"] + " to the list of tracked addons for @" + role
				await channel.send(successMessage)
			else:
				alreadyExists = entry[1] + " is already being tracked."
				c.close()
				conn.close()
				await channel.send(alreadyExists)
		else:
			await channel.send(failureMessage)
	if message.content.startswith('!addonremove'):
		conn = sqlite3.connect('addons.db')
		c = conn.cursor()
		message = message.content
		message = message.split()
		id = message[1]
		if intCheck(id):
			command = "SELECT FROM addons WHERE id = " + str(id)
			c.execute(command)
			entry = c.fetchone()
			if entry is not None:
				removeMessage = entry[1] + " was removed from the tracker"
				command = "DELETE FROM addons WHERE id = " + str(id)
				c.execute(command)
				conn.commit()
			else:
				await channel.send(notFoundMessage)
			c.close()
			conn.close()
			await channel.send(removeMessage)
		else:
			await channel.send(failureMessage)
	if message.content.startswith('!addonhelp'):
		await channel.send("List of commands: ")
		await channel.send("!addon [id] [role] Adds an addon with Project ID [id] to the tracker. When updates are available, it will tag @[role]. Default is @here")
		await channel.send("!addonremove [id] Removes an addon from the tracker with Project ID [id]")	
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
	
def intCheck(input):
	try:
		int(input)
		return True
	except ValueError:
		return False

updateAlert.start()
client.run(TOKEN)
