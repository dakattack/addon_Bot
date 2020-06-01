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

@client.event
async def on_ready():
	global conn
	global c
	connectDB()
	c.execute("CREATE TABLE IF NOT EXISTS addons(id INTEGER PRIMARY KEY, name TEXT, latestVersion INTEGER, latestDownload TEXT)")
	c.execute("CREATE TABLE IF NOT EXISTS channels(id INTEGER PRIMARY KEY)")
	c.execute("CREATE TABLE IF NOT EXISTS addons_channels(addon_id INTEGER, channel_id INTEGER, role TEXT, FOREIGN KEY(addon_id) REFERENCES addons(id), FOREIGN KEY(channel_id) REFERENCES channels(id))")
	closeDB()
	print('Logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
	global conn
	global c
	failureMessage = "Please enter a valid command."
	notFoundMessage = "Command not found."
	invalidIDMessage = "Please enter a valid addon ID."

	channel = message.channel
	channelID = message.channel.id
	ADDON = '!addon'
	HELP = 'help'
	ADD	= 'add'
	REMOVE = 'remove'
	LIST = 'list'
	POOP = 'poop'

	if message.author == client.user:
		return

	messageContentArray = messageContentSplit(message)
	feature = messageContentArray[0]

	if feature == ADDON:
		connectDB()
		command = messageContentArray[1]
		dbQuery = "SELECT * FROM channels WHERE id = " + str(channelID)
		c.execute(dbQuery)
		entry = c.fetchone()
		if entry is None:
			dbQuery = "INSERT INTO channels VALUES(" + str(channelID) + ")"
		c.execute(dbQuery)

		if command == LIST:
			addonList = "```Addons currently being tracked:\n"
			dbQuery = "SELECT * FROM addons_channels WHERE channel_id = " + str(channelID)
			c.execute(dbQuery)
			tracked = c.fetchall()
			for trackedAddon in tracked:
				addonID = str(trackedAddon[0])
				addonRole = str(trackedAddon[2])
				dbQuery = "SELECT * FROM addons WHERE id = " + str(addonID)
				c.execute(dbQuery)
				addon = c.fetchone()
				addonName = str(addon[1])
				addonNameTrunc = (addonName[:37] + '...') if len(addonName) > 37 else addonName.ljust(40)
				addonIDTrunc = (addonID[:10] + '...') if len(addonID) > 10 else addonID.ljust(13)
				addonInfo = "\t" + addonNameTrunc + "Project ID: " + addonIDTrunc + " Role: " + addonRole + "\n"
				addonList = addonList + addonInfo
			addonList = addonList + "```"
			await channel.send(addonList)

		elif command == HELP:
			await channel.send("\
			List of commands:\n\
			!addon add [id] [role]: Adds an addon with Project ID [id] to the tracker. When updates are available, it will tag @[role]. Default is 'here'.\n\
			!addon help: displays the list of commands.\n\
			!addon list: Shows all addons currently being tracked.\n\
			!addon remove [id]: Removes an addon from the tracker with Project ID [id]")

		elif command == POOP:
			await channel.send("Work is da poop, no more!")

		elif command == ADD:
			if(intCheck(messageContentArray[2]) is False):
				await channel.send(invalidIDMessage)
				return
			id = messageContentArray[2]
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
				latestDownload = addonDict["latestFiles"][latestClassic]["downloadUrl"]
				dbQuery = 'INSERT INTO addons VALUES(' + str(id) + ', "' + str(name) + '", ' + str(latestVersion) + ', "' + str(latestDownload) + '")'
				c.execute(dbQuery)
			dbQuery = "SELECT * FROM addons_channels WHERE addon_id = " + str(id) + " AND channel_id = " + str(channelID)
			c.execute(dbQuery)
			entry = c.fetchone()
			if entry is None:
				dbQuery = "SELECT * FROM addons WHERE id = " + str(id)
				c.execute(dbQuery)
				addon = c.fetchone()
				name = addon[1]
				try:
					roleName = messageContentArray[3]
				except IndexError:
					roleName = "NOROLE"
				roleList = message.guild.roles
				roleFound = False
				if roleName != "here" and roleName != "NOROLE":
					for roleTemp in roleList:
						if roleTemp.name == roleName:
							role = roleTemp
							dbQuery = 'INSERT INTO addons_channels VALUES(' + str(id) + ', ' + str(channelID) + ', "' + roleName + '")'
							roleFound = True
							successMessage = "Successfully added " + name + " to the list of tracked addons for " + role.mention
				if roleName == "here":
					dbQuery = 'INSERT INTO addons_channels VALUES(' + str(id) + ', ' + str(channelID) + ', "here")'
					roleFound = True
					successMessage = "Successfully added " + name + " to the list of tracked addons for @here"
				if(roleFound is False):
					dbQuery = 'INSERT INTO addons_channels VALUES(' + str(id) + ', ' + str(channelID) + ', "NOROLE")'
					successMessage = "Successfully added " + name + " to the list of tracked addons."
				c.execute(dbQuery)
				await channel.send(successMessage)
			else:
				repeatMessage = "Addon is already being tracked."
				await channel.send(repeatMessage)

		elif command == REMOVE:
			if(intCheck(messageContentArray[2]) is False):
				await channel.send(invalidIDMessage)
				return
			id = messageContentArray[2]
			dbQuery = "SELECT * FROM addons_channels WHERE addon_id = " + str(id) + " AND channel_id = " + str(channelID)
			c.execute(dbQuery)
			entry = c.fetchone()
			if entry is not None:
				dbQuery = "SELECT * FROM addons WHERE id = " + str(id)
				c.execute(dbQuery)
				addon = c.fetchone()
				addonName = str(addon[1])
				removeMessage = addonName + " was removed from the tracker."
				dbQuery = "DELETE FROM addons_channels WHERE addon_id = " + str(id) + " AND channel_id = " + str(channelID)
				c.execute(dbQuery)
				dbQuery = "SELECT * FROM addons_channels WHERE addon_id = " + str(id)
				c.execute(dbQuery)
				entry = c.fetchone()
				if entry is None:
					dbQuery = "DELETE FROM addons WHERE id = " + str(id)
					c.execute(dbQuery)
				await channel.send(removeMessage)
			else:
				await channel.send(invalidIDMessage)
		else:
			await channel.send(failureMessage)
		closeDB()

@tasks.loop(hours=2)
async def updateAlert():
	global conn
	global c
	connectDB()
	await client.wait_until_ready()
	dbQuery = "SELECT * FROM addons"
	c.execute(dbQuery)
	addons = c.fetchall()
	for addon in addons:
		print("Checking for updates...")
		id = str(addon[0])
		apiRequest = "https://addons-ecs.forgesvc.net/api/v2/addon/" + id
		with urllib.request.urlopen(apiRequest) as url:
			jsonFile = url.read()
			addonDict = json.loads(jsonFile)
		latestClassic = 0
		while addonDict["latestFiles"][latestClassic]["gameVersionFlavor"] != "wow_classic":
			latestClassic = latestClassic + 1
		if addonDict["latestFiles"][latestClassic]["id"] != addon[2]:
			latestVersion = str(addonDict["latestFiles"][latestClassic]["id"])
			latestDownload = str(addonDict["latestFiles"][latestClassic]["downloadUrl"])
			dbQuery = 'UPDATE addons SET latestVersion = ' + latestVersion +', latestDownload = "' + latestDownload + '" WHERE id = ' + id
			c.execute(dbQuery)
			conn.commit()
			updateMessage = "A new version of " + addonDict["name"] + " is available! Version: " + latestVersion + " Be sure to download it here: " +  latestDownload
			dbQuery = "SELECT * FROM addons_channels WHERE addon_id = " + id
			c.execute(dbQuery)
			channelsTracking = c.fetchall()
			for eachChannel in channelsTracking:
				channel = client.get_channel(eachChannel[1])
				role = eachChannel[2]
				if role != "NOROLE":
					await channel.send("@" + role + " " + updateMessage)
				elif role == "here":
					await channel.send("@here " + updateMessage)
				else:
					await channel.send(updateMessage)
	closeDB()

def connectDB():
	global conn
	global c
	conn = sqlite3.connect('addons.db')
	c = conn.cursor()

def closeDB():
	conn.commit()
	c.close()
	conn.close()

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
