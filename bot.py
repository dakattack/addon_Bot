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
	ADDON	= '!addon'
	HELP	= '!help'
	ADD	= 'add'
	REMOVE	= 'remove'
	LIST	= 'list'

	if message.author == client.user:
			return
	
	messageContentArray = messageContentSplit(message)
	feature = messageContentArray[0]

	if feature == ADDON:
		command = messageContentArray[1]
		id = messageContentArray[2]

		if intCheck(id):
			if command == ADD:
				connectDB()
				dbQuery = "SELECT * FROM addons WHERE id = " + str(id)
				c.execute(dbQuery)
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
						roleName = messageContentArray[3]
					except IndexError:
						roleName = "here"
					dbQuery = 'INSERT INTO addons VALUES(' + str(id) + ', "' + str(name) + '", ' + str(latestVersion) + ', "' + str(roleName) + '")'
					c.execute(dbQuery)
					conn.commit()
					c.close()
					conn.close()
					roleList = message.guild.roles
					for roleTemp in roleList:
						if roleTemp.name == roleName:
							role = roleTemp
							successMessage = "Successfully added " + addonDict["name"] + " to the list of tracked addons for " + role.mention
						else:
							successMessage = "Successfully added " + addonDict["name"] + " to the list of tracked addons for @here"
					await channel.send(successMessage)
				else:
					alreadyExists = entry[1] + " is already being tracked."
					c.close()
					conn.close()
					await channel.send(alreadyExists)

			elif command == REMOVE:
				connectDB()
				dbQuery = "SELECT * FROM addons WHERE id = " + str(id)
				c.execute(dbQuery)
				entry = c.fetchone()
				if entry is not None:
					removeMessage = entry[1] + " was removed from the tracker"
					dbQuery = "DELETE FROM addons WHERE id = " + str(id)
					c.execute(dbQuery)
					conn.commit()
				else:
					await channel.send(notFoundMessage)
				c.close()
				conn.close()
				await channel.send(removeMessage)

			elif command == LIST:
				await channel.send("Addons currently being tracked:")
				connectDB()
				dbQuery = "SELECT * FROM addons"
				c.execute(dbQuery)
				entry = c.fetchone()
				while entry is not None:
					addonInfo = str(entry[1]) + " Project ID: " + str(entry[0]) + " Role: " + str(entry[3])
					await channel.send(addonInfo)
					entry = c.fetchone()

			else:
				await channel.send(failureMessage)

		else:
			await channel.send(failureMessage)

	elif feature == HELP:
		await channel.send("List of commands:")
		await channel.send("!addon add [id] [role]: Adds an addon with Project ID [id] to the tracker. When updates are available, it will tag @[role]. Default is 'here'")
		await channel.send("!addon remove [id]: Removes an addon from the tracker with Project ID [id]")    
		await channel.send("!addon list: Shows all addons currently being tracked.")

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
			dbQuery = "UPDATE addons SET latestVersion = " + str(addonDict["latestFiles"][latestClassic]["id"]) +" WHERE id = " + str(row[0])
			c.execute(dbQuery)
			conn.commit()
			updateMessage = "A new version of " + addonDict["name"] + " is available! Version: " + addonDict["latestFiles"][latestClassic]["displayName"] + " Be sure to download it here before raid: " +  addonDict["latestFiles"][latestClassic]["downloadUrl"]
			await channel.send(updateMessage)
		row = c.fetchone()

	c.close()
	conn.close()

def connectDB():
	conn = sqlite3.connect('addons.db')
	c = conn.cursor()

def messageContentSplit(message):
	messageContent = message.content
	messageContentArray = messageContent.split()
	return messageContentArray

def intCheck(input):
	try:
		int(input)
		return True
	except ValueError:
		return False

updateAlert.start()
client.run(TOKEN)
