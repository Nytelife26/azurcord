import discord
from discord.ext import commands
import asyncio, json, os
from .mechanics import initData, getPlyData
initData()
from . import config

import pathlib
datapath = str(pathlib.Path(__file__).parent) + "/"

"""Extra commands that didn't need to be in the base file"""

defaultDeck1 = ["Minor Recharge", "Minor Recharge", "Killer's Aura", "Killer's Aura", "Snipe", "Snipe", "Hivemind", "Hivemind", "Hivemind", "Swing", "Swing", "Swing", "Minor Panic", "Minor Panic", "Minor Panic", "Swarmspark", "Swarmspark", "Swarmspark", "Inherited Cruelty", "Inherited Cruelty", "Inherited Cruelty", "Recursion", "Recursion", "Recursion", "Gluttonous Temptation", "Neuron Boost", "Neuron Boost", "Siphon Power", "Siphon Power", "Siphon Power", "Stimulation", "Stimulation", "Maul", "Backlash", "Collected Shot", "Double Tap", "Beg for Mercy", "Beg for Mercy", "Creativity", "Creativity"]
defaultDeck2 = ["Maul", "Snipe", "Snipe", "Swing", "Swing", "Swing", "Stimulation", "Stimulation", "Double Tap", "Minor Recharge", "Minor Recharge", "Neuron Boost", "Neuron Boost", "Minor Panic", "Minor Panic", "Minor Panic", "Beg for Mercy", "Beg for Mercy", "Fizzle", "Fizzle", "False Hope", "False Hope", "Shattered Mind", "Last Meal", "Last Meal", "Last Crumb", "Last Crumb", "Recursion", "Recursion", "Voracity", "Voracity", "Mind Swap", "Mind Swap", "Voracity", "Unwilling Sacrifice", "Unwilling Sacrifice", "Bloody Pentagram", "Bloody Pentagram", "Siphon Power", "Siphon Power", "Confusion", "Confusion"]

class InfoCommands():
	#Search card via skill
	@commands.command()
	async def search( self, ctx, *args ):
		"""Search for a card via its skill."""
		queryList = args
		stringToSay = ""
		i = 0
		for card in cardList:
			sayCard = True
			for query in queryList:
				if query.lower() not in cardList[card].skill.lower() and query.lower() not in cardList[card].name.lower():
					sayCard = False
			if sayCard == True:
				stringToSay += str(cardList[card]) + '\n'
				i+=1
				if i>=10:
					i=0
					await ctx.send( stringToSay )
					stringToSay = ""
		if not stringToSay == "":
			await ctx.send( stringToSay )
			
	#Search Node via skill
	@commands.command()
	async def nodesearch( self, ctx, *args ):
		"""Search for a Node via its skill."""
		queryList = args
		stringToSay = ""
		i = 0
		for node in nodeList:
			sayNode = True
			for query in queryList:
				if query.lower() not in nodeList[node].skill.lower() and query.lower() not in nodeList[node].name.lower():
					sayNode = False
			if sayNode == True:
				stringToSay += str(nodeList[node]) + '\n'
				i+=1
				if i>=10:
					i=0
					await ctx.send( stringToSay )
					stringToSay = ""
		if not stringToSay == "":
			await ctx.send( stringToSay )
		
	#Get Node information 
	@commands.command()	
	async def node( self, ctx, *args ):
		"""Query the bot for information on a Node."""
		try:
			query = ' '.join( args ).lower()
			if query.lower() in nodeList:
				await ctx.send( str( nodeList[query.lower()] ) )
			else:
				await ctx.send( "Node not found." )
		except Exception as e:
			print(e)
			
	@commands.command()
	async def library( self, ctx, *args ):
		"""See how many cards there are in the game."""
		commons, uncommons, rares = [], [], []
		for card in cardList:
			if cardList[card].rarity == 'C':
				commons.append( cardList[card].name )
			elif cardList[card].rarity == 'U':
				uncommons.append( cardList[card].name )
			elif cardList[card].rarity == 'R':
				rares.append( cardList[card].name )
		await ctx.send( str(len(commons)) + " Commons, " + str(len(uncommons)) + " Uncommons, and " + str(len(rares)) + " Rare cards exist.\nThere are " + str(len(commons)+len(uncommons)+len(rares)) + " cards in total, not counting Special cards." )
	
	#Get card information 
	@commands.command()	
	async def card( self, ctx, *args ):
		"""Query the bot for information on a card."""
		try:
			query = ' '.join( args ).lower()
			if query in cardList:
				await ctx.send( str( cardList[query.lower()] ) )
			else:
				await ctx.send( "Card not found." )
		except Exception as e:
			print(e)
			
	#Get game definition
	@commands.command()	
	async def define( self, ctx, *args ):
		"""Query the bot for the definition of a game term."""
		try:
			query = ' '.join( args )
			if query in config.DEFINITIONS.keys():
				await ctx.send( config.DEFINITIONS[query.lower()] )
			else:
				await ctx.send( "Term not found." )
		except Exception as e:
			print(e)
			
	#Show off a card
	@commands.command()
	async def showoff( self, ctx, *args  ):
		"""Show off a card. And don't try to lie!"""
		try:
			card = ' '.join( args )
			cardLower = card.lower()
		except:
			await ctx.send( "Incorrect syntax. =showoff <cardname>" )
		
		try:
			if cardLower in [x.lower() for x in getPlyData( ctx.author )['collection'].keys()]:
				await ctx.send( ctx.author.name + " has a shiny " + card + "!" )
			else:
				await ctx.send( ctx.author.name + " doesn't even have a " + card + ". What a loser!" )
		except:
			await ctx.send( "You need to be registered to show stuff off. =register" )
			
	#Credits
	@commands.command()
	async def credits( self, ctx, *args ):
		"""See who worked in this kick-butt project!"""
		await ctx.send( "[-------------=Credits=-------------]\n---[--------Version "+config.VERSION+"--------]---\n**Developer**: Rogonad & Nytelife26 \n**Design**: Rogonad & Nytelife26" )
		
	#Tutorial
	@commands.command()
	async def tutorial( self, ctx, *args ):
		"""Get a link to the beginner's guide."""
		await ctx.send( "Beginner's Guide:" )
			
	#Get an 'account'
	async def register( self, ctx ):
		"""Get an account before you can start playing"""
		playerID = ctx.author.id
        # TODO: Fix this bullshit
        # It sucks ass
        # Burn it in hell
        # Use JSON
        # and the proper config dir structures
		if os.path.isfile(datapath + 'player_data/'+str(playerID)+'.txt'):
			# await ctx.send( "You're already registered." )
			return # already registered, do nothing
		playerData = {
			"collection": {
				"Maul": 1,
				"Killer's Aura": 2,
				"Snipe": 2,
				"Gluttonous Temptation": 1,
				"Hivemind": 3,
				"Swing": 3,
				"Minor Panic": 3,
				"Swarmspark": 3,
				"Stimulation": 2,
				"Inherited Cruelty": 3,
				"Recursion": 2,
				"Double Tap": 1,
				"Neuron Boost": 2,
				"Siphon Power": 3,
				"Backlash": 1,
				"Creativity": 2,
				"Minor Recharge": 2,
				"Beg For Mercy": 2,
				"Collected Shot": 1,
				"Confusion": 2,
				"Mind Swap": 2,
				"Fizzle": 2,
				"Voracity": 3,
				"Unwilling Sacrifice": 2,
				"False Hope": 2,
				"Shattered Mind": 1,
				"Last Meal": 2,
				"Last Crumb": 2,
				"Bloody Pentagram": 2
			},
			"selectedDeck": 0,
			"money": 50,
			"packs": 4,
			"decks": [ defaultDeck1, defaultDeck2, [], [], [] ],
			"decknames": [ "Swarmers", "H/D Combo", "", "", "" ] #just cleaner than making "decks" a dict...
		}
	
		
		with open(datapath + 'player_data/'+str(playerID)+'.txt', 'w') as outfile:
			json.dump(playerData, outfile)
		
		# await ctx.send( "Registration successful!" )
