import discord
from redbot.core import Config, bank, commands, errors
from redbot.core.bot import Red
from redbot.core.i18n import Translator, cog_i18n
from discord.utils import get
import asyncio
import os, sys, random
from . import classes
from . import mechanics
from . import config
from .cardformat import Waifer
from .cardList import Ship
import json
import calendar
import logging
import random
from enum import Enum
from typing import cast, Iterable, List, Optional, Union
import pathlib
import aiohttp
from fuzzywuzzy import fuzz, process

datapath = str(pathlib.Path(__file__).parent) + "/"

_ = Translator("Azur", __file__)

#config.matches = {}

# info commands
from .mechanics import initData, getPlyData
initData()

defaultDeck1 = ["Abukuma", "Abukuma", "Ayanami - Witch in Ambush", "Ayanami - Witch in Ambush", "Ayanami - Witch in Ambush", "Brooklyn", "Brooklyn", "Brooklyn", "Bullin MKII", "Bullin MKII", "Bullin MKII", "Akagi chan", "Akagi chan", "Deutschland", "Formidable", "Deutschland", "Formidable", "Formidable", "Graf Zeppelin", "Graf Zeppelin", "Graf Zeppelin", "Graf Zeppelin", "Jamaica - Dark Bolt", "Jamaica - Dark Bolt", "Musketeer", "Musketeer", "Musketeer", "Nachi", "Nachi", "Nachi", "Nicholas - Niconurse", "Nicholas - Niconurse", "Nicholas - Niconurse", "Prince of Wales - Windsor Sun", "Prince of Wales - Windsor Sun", "San Juan", "San Juan", "Vestal", "Vampire", "Universal Bullin"]
defaultDeck2 = ["Akagi chan", "Akagi chan", "Akagi chan", "Ayanami - Witch in Ambush", "Abukuma", "Abukuma", "Ayanami - Witch in Ambush", "Ayanami - Witch in Ambush", "Brooklyn", "Brooklyn", "Brooklyn", "Bullin MKII", "Bullin MKII", "Bullin MKII", "Deutschland", "Formidable", "Deutschland", "Formidable", "Graf Zeppelin", "Graf Zeppelin", "Graf Zeppelin", "Graf Zeppelin", "Jamaica - Dark Bolt", "Jamaica - Dark Bolt", "Musketeer", "Musketeer", "Nachi", "Nachi", "Nachi", "Nicholas - Niconurse", "Nicholas - Niconurse", "Nicholas - Niconurse", "Prince of Wales - Windsor Sun", "Prince of Wales - Windsor Sun", "San Juan", "San Juan", "Universal Bullin", "Universal Bullin", "Vampire", "Vampire", "Vestal", "Vestal"]

@cog_i18n(_)
class Azur(Waifer, commands.Cog):
    """Azur lane Gatcha v1"""
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        
        
    #Send hand function
    async def sendHand(self, player, playerObj, ctx ): #delete last hand
        if not playerObj.lastHandDM == None:
            await playerObj.lastHandDM.delete()

    #send hand
        stringSend = ""
        for cards in playerObj.hand:
            stringSend += str( mechanics.shipList[cards.lower()] ) + "\n"
        playerObj.lastHandDM = await player.send("[-----Hand-----]\n" + stringSend + "\n\n" )

    #print and reset player logs, then activate all triggered abilities
    async def printLogs(self, match, ctx ):
        playerOneObj = match.chalObj
        playerTwoObj = match.defObj
        #trigger stuff
        if len(playerOneObj.nodesToTrigger) > 0:
            for triggered in playerOneObj.nodesToTrigger:
                await mechanics.nodeList[triggered[0]].triggerFunc( playerOneObj, playerTwoObj, triggered[1], triggered[2] ) or []
            playerOneObj.nodesToTrigger = []
            
        strToSend = ""
        for logs in playerOneObj.log:
            strToSend += logs + '\n'
        if len(playerOneObj.log) > 0:
            await ctx.send(strToSend)
        playerOneObj.log = []

        #trigger stuff
        if len(playerTwoObj.nodesToTrigger) > 0:
            for triggered in playerTwoObj.nodesToTrigger:
                await mechanics.nodeList[triggered[0]].triggerFunc( playerTwoObj, playerOneObj, triggered[1], triggered[2] ) or []
            playerTwoObj.nodesToTrigger = []

        strToSend = ""
        for logs in playerTwoObj.log:
            strToSend += logs + '\n'
        if len(playerTwoObj.log) > 0:
            await ctx.send(strToSend)
        playerTwoObj.log = []

    #Active player played a card
    async def playCard(self, match, activePlayer, activePlayerObj, opponent, opponentObj, cardName, targets, ctx ):
        playedObject = mechanics.cardList[cardName.lower()]

        #Pay health if possible
        if activePlayerObj.lifeforce <= playedObject.cost:
            await ctx.send("You don't have enough oil to play that card!" )
            return
        else:
            activePlayerObj.lifeforce -= playedObject.cost #doesn't use damage function cause it shouldn't trigger as damage
            
        if activePlayerObj.lifeforce <= 0:
            await mechanics.gameOver( activePlayer.id )
            return
            
        #Remove card from hand
        for card in activePlayerObj.hand:
            if card.lower() == cardName:
                activePlayerObj.hand.remove( card )
                break
            
        #Play the card (assuming already got proper targets)
        if targets is None:
            targets = -2
        await playedObject.func( activePlayerObj, opponentObj, targets ) #or [] #the or [] does something undefined but makes it work.
        #TODO: figure out why 'or []' works LMAO
        await ctx.send(activePlayer.name + " played " + str(playedObject) + "\n\n" )
        mechanics.gameTrigger( "PLAYED_CARD", activePlayerObj, playedObject.name )

        #check if game still exists
        if not mechanics.isGameRunning( match ):
            return
                
        #Send hand & messages
        activePlayerObj.cardsThisTurn += 1
        await self.sendHand( activePlayer, activePlayerObj, ctx )

        await self.printLogs( match, ctx )
        if match.gameMessage != None:
            await match.gameMessage.delete()
        match.gameMessage = await ctx.send(str(activePlayerObj)+"\n\n"+str(opponentObj)+"\nCommands: play, concede, pass, info, scuttle" )
        return True

    async def getTarget(self, playedObject, activePlayerObj, activePlayer, otherPlayerObj, ctx ):
        targetEmojis = ['0⃣','1⃣','2⃣','3⃣','4⃣','5⃣','6⃣','7⃣','8⃣','9⃣', '🔟']
        if playedObject.targets == None:
            return -2
        elif playedObject.targets == "ENEMY_NODE":
            #React to self up to amount of enemy nodes (if none, then continue big loop)
            if len(otherPlayerObj.nodes) == 0:
                await ctx.send("No nodes to target." )
                return -1 #if False, continue
                
            msg = await ctx.send("React! Which of your opponent's Nodes do you want to attack?" )
            for i in range( len(otherPlayerObj.nodes) ):
                await msg.add_reaction(targetEmojis[i+1])
                
            def check(r, user):
                return all([user == activePlayer, r.message.id == msg.id, r.emoji in targetEmojis])
                
            #Wait for reaction from that list
            res, usr = await self.bot.wait_for('reaction_add', check=check)
            thisTarget = targetEmojis.index(str(res.emoji))-1
            return thisTarget
        elif playedObject.targets == "FRIENDLY_NODE":
            #React to self up to amount of friendly nodes (if none, then continue big loop)
            if len(activePlayerObj.nodes) == 0:
                await ctx.send("No nodes to target." )
                return -1
                
            msg = await ctx.send("React! Which of your Nodes will you target?" )
            for i in range( len(activePlayerObj.nodes) ):
                await msg.add_reaction(targetEmojis[i+1])
                
            #Wait for reaction from that list
            res, usr = await self.bot.wait_for('reaction_add', check=check)
            thisTarget = targetEmojis.index(str(res.emoji))-1
            return thisTarget
            
        elif playedObject.targets == "PLAYER":
            msg = await ctx.send("React! Target who? (1 - yourself, 2 - opponent)." )
            for i in range( 2 ):
                await msg.add_reaction(targetEmojis[i+1])
            res, usr = await self.bot.wait_for('reaction_add', check=check)
            thisTarget = targetEmojis.index(str(res.emoji))-1
            return thisTarget
        
    #New round in a match started
    async def startRound(self, match, activePlayer, activePlayerObj, otherPlayer, otherPlayerObj, ctx ):
        #check if game still exists
        if not mechanics.isGameRunning( match ):
            return
        #check if sacrificed out when drawing a card (maybe condense this chunk somehow)
        if not activePlayerObj.drawCard():
            await ctx.send(activePlayer.name + " scuttled out!" )
            await mechanics.gameOver( activePlayer.id )
            return

        #Energy costs (oooh actual phase orders are showing c:)
        await mechanics.heal( activePlayerObj, activePlayerObj.energy )

        #check if game still exists
        if not mechanics.isGameRunning( match ):
            return

        #Activate all of active player's nodes/initialize turn-based vars
        if len(activePlayerObj.nodes) > 0:
            for thisNode in activePlayerObj.nodes.copy():
                await mechanics.activateNode( thisNode, activePlayerObj, otherPlayerObj )
            await ctx.send(activePlayerObj.name + " Abilities activated for the start of this turn." )
        activePlayerObj.newTurn()
        otherPlayerObj.newTurn()
        activePlayerObj.newMyTurn()
            
        #check if game still exists
        if not mechanics.isGameRunning( match ):
            return
            
        #Send the info
        await ctx.send(activePlayer.name + "'s turn." )
        if not match.gameMessage == None:
            await match.gameMessage.delete()
        await self.printLogs( match, ctx )
        match.gameMessage = await ctx.send(str(activePlayerObj)+"\n\n"+str(otherPlayerObj)+"\nCommands: play, concede, pass, info, scuttle" )

        await self.sendHand( activePlayer, activePlayerObj, ctx )

        #Make sure it's a game command
        def check(msg):
            return msg.author == activePlayer and msg.channel == ctx.channel and (msg.content.lower().startswith('play') or msg.content.lower().startswith('concede') or msg.content.lower().startswith('pass') or msg.content.lower().startswith('info') or msg.content.lower().startswith('scuttle'))

        #Wait for active player's command.
        while True:
        #check if game still exists
            if not mechanics.isGameRunning( match ):
                ctx.send("test")
                return
        #Act within 500 seconds or game is lost
            try:
                messageOriginal = await self.bot.wait_for('message', check=check, timeout=config.TURN_TIMEOUT )
                message = messageOriginal.content.lower().split(' ',1)
            except (AttributeError, asyncio.TimeoutError):
                await ctx.send("Game timed out!")
                match.timedOut = True
                await mechanics.gameOver( activePlayer.id )
                break
            
            if message[0] == 'info':
                if not match.gameMessage == None:
                    await match.gameMessage.delete()
                match.gameMessage = await ctx.send(str(activePlayerObj)+"\n\n"+str(otherPlayerObj)+"\nCommands: play, concede, pass, info, scuttle" )
                continue
            elif message[0] == 'play': #The big one
            
            #Ensure it's in hand
                try:
                    arg = message[1]
                except IndexError:
                    await ctx.send("No card specified.")
                    continue
                    
                if not any(arg in x.lower() for x in activePlayerObj.hand):
                    await ctx.send("Played an invalid card." )
                    continue
                    
                #Get proper targets
                playedObject = mechanics.cardList[arg.lower()]
                thisTarget = await self.getTarget( playedObject, activePlayerObj, activePlayer, otherPlayerObj, ctx )
                if thisTarget == -1:
                    continue
                
                #Check if node generator (for 1 per turn limit)
                if playedObject.cardtype == "NodeGen":
                    if activePlayerObj.playedNode:
                        await ctx.send("You already spawned a Node this turn." )
                        continue
                    else:
                        activePlayerObj.playedNode = True
                await self.playCard( match, activePlayer, activePlayerObj, otherPlayer, otherPlayerObj, arg, thisTarget, ctx )
                continue
            elif message[0] == 'pass':
                await self.startRound( match, otherPlayer, otherPlayerObj, activePlayer, activePlayerObj, ctx )
                break
                return
            elif message[0] == 'scuttle':
                if activePlayerObj.sacrificed == True:
                    await ctx.send("You already scuttled a ship this turn." )
                    continue
                elif len(activePlayerObj.deck) <= 0:
                    await ctx.send("You have no ships to scuttle." )
                    continue
                else:
                    activePlayerObj.sacrificed = True
                    poppedCard, lifeToGain = mechanics.sacCard( activePlayerObj )
                    await ctx.send(activePlayerObj.name + " scuttled " + poppedCard + " for " + str(lifeToGain) + " Oil Reserves." )
                    continue
            elif message[0] == 'concede':
                await ctx.send(activePlayer.name + " conceded." )
                await mechanics.gameOver( activePlayer.id )
                return

    #Challenge someone and initialize the fight
    @commands.command()
    async def challenge(self, ctx, target:discord.Member, wager:int=0):
        """Challenge a player to Azur! `,,challenge <@user> <wager>`"""

        challengerID = ctx.author.id

        #Make sure neither player is in a game currently
        if challengerID in config.matches or target.id in config.matches:
            await ctx.send( "A player is already in a match." )
            return
            
        #Dont challenge yourself man
        if ctx.author == target:
            await ctx.send( "You can't challenge yourself, ya muppet")
            return

        #Have challenged guy accept
        await ctx.send(target.mention + ", you have been challenged to a battle in Azur{}! Type 'accept' to accept.".format(" with a wager of {}".format(wager) if wager > 0 else ""))
        
        def check(m):
            return m.author == target and m.content.lower() == "accept"
        
        try:
            message = await self.bot.wait_for('message', check=check, timeout=config.CHALLENGE_TIMEOUT )
        except asyncio.TimeoutError:
            await ctx.send(ctx.author.name + ", your challenge was declined! Forever alone :c")
            return

        #check again here for duplicate accepts
        if challengerID in config.matches or target.id in config.matches:
            await ctx.send( "Player is already in a game." )
            return

        #Get player data
        challengerDeck = mechanics.getPlyData( ctx.author )
        defenderDeck = mechanics.getPlyData( target )
        if defenderDeck is None or challengerDeck is None:
            await ctx.send("A player isn't registered! Both of you, type any message to be autoregistered.")
            return
        challengerDeck = challengerDeck['decks'][challengerDeck['selectedDeck']]
        defenderDeck = defenderDeck['decks'][defenderDeck['selectedDeck']]
        if len(challengerDeck) < config.DECK_SIZE_MINIMUM or len(defenderDeck) < config.DECK_SIZE_MINIMUM:
            await ctx.send( "A player doesn't have at least "+str(config.DECK_SIZE_MINIMUM)+" cards in their deck!!!" )
            return
            
        #Wager stuff
        if wager > 0:
            if await bank.can_spend(ctx.author, wager) or await bank.can_spend(target.id, wager):
                await ctx.send( "Wager set to ${}!".format(wager))
            else:
                await ctx.send( "A player doesn't have enough money for this wager!" )
                return

        #Initialize game
        #TODO: [challenger] -> [ctx.author]
        config.matches[challengerID] = classes.TCGame( challengerID, target.id, wager )
        config.matches[challengerID].chalObj = classes.Player( ctx.author.name, challengerDeck, [], self.bot, ctx )
        config.matches[challengerID].defObj = classes.Player( target.name, defenderDeck, [], self.bot, ctx )
        config.matches[challengerID].chalObj.shuffle()
        config.matches[challengerID].defObj.shuffle()
        for i in range(config.STARTING_HAND_SIZE):
            config.matches[challengerID].chalObj.drawCard()
            config.matches[challengerID].defObj.drawCard()
        config.matches[challengerID].chalObj.opponent = config.matches[challengerID].defObj
        config.matches[challengerID].defObj.opponent = config.matches[challengerID].chalObj
        print('A match has started. ' + str(ctx.author.name) + ' vs ' + str(target.name) + '!')

        #Start round 
        if random.randint(0,1) == 0:
            config.matches[challengerID].chalObj.active = True
            config.matches[challengerID].defObj.energy += 1
            await self.startRound( config.matches[challengerID], ctx.author, config.matches[challengerID].chalObj, target, config.matches[challengerID].defObj, ctx )
        else:
            config.matches[challengerID].defObj.active = True
            config.matches[challengerID].chalObj.energy += 1
            await self.startRound( config.matches[challengerID], target, config.matches[challengerID].defObj, ctx.author, config.matches[challengerID].chalObj, ctx )

        # debug tool to check all loaded nodes and cards:
        # print("[-=-Loaded Cards-=-]\n")
        # for cards in mechanics.cardList:
            # print(cards)
        # print("\n[-=-Loaded Nodes-=-]\n")
        # for nodes in mechanics.nodeList:
            # print(nodes)
    
    async def listener(self, message):
        if not message.author.bot:
            await self.register(message)
    
    # info commands
    
    #Search card via skill
    @commands.command()
    async def cardsearch( self, ctx, *args ):
        """Search for a card via its skill."""
        queryList = args
        stringToSay = ""
        i = 0
        for card in mechanics.shipList:
            sayCard = True
            for query in queryList:
                if query.lower() not in mechanics.shipList[card].name.lower():
                    sayCard = False
            if sayCard == True:
                stringToSay += str(mechanics.shipList[card]) + '\n'
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
        for node in mechanics.nodeList:
            sayNode = True
            for query in queryList:
                if query.lower() not in mechanics.nodeList[node].skill.lower() and query.lower() not in mechanics.nodeList[node].name.lower():
                    sayNode = False
            if sayNode == True:
                stringToSay += str(mechanics.nodeList[node]) + '\n'
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
            if query.lower() in mechanics.nodeList:
                await ctx.send( str( mechanics.nodeList[query.lower()] ) )
            else:
                await ctx.send( "Node not found." )
        except Exception as e:
            print(e)
            
    @commands.command()
    async def library( self, ctx, *args ):
        """See how many cards there are in the game."""
        normal, rare, elite, superrare, ultrarare, priority = [], [], [], [], [], []
        for card in mechanics.cardList:
            if mechanics.cardList[card].rarity == 'N':
                normal.append( mechanics.cardList[card].name )
            elif mechanics.cardList[card].rarity == 'R':
                rare.append( mechanics.cardList[card].name )
            elif mechanics.cardList[card].rarity == 'E':
                elite.append( mechanics.cardList[card].name )
            elif mechanics.cardList[card].rarity == 'SR':
                superrare.append( mechanics.cardList[card].name )
            elif mechanics.cardList[card].rarity == 'UR':
                ultrarare.append( mechanics.cardList[card].name )
            elif mechanics.cardList[card].rarity == 'PR':
                priority.append( mechanics.cardList[card].name )
        await ctx.send( str(len(normal)) + " Normal, " + str(len(rare)) + " Rare, " + str(len(elite)) + " Elite, " + str(len(superrare)) + " Super Rare, " + str(len(ultrarare)) + " Ultra Rare, and " + str(len(priority)) + " Priority cards that currently exist.\nThere are " + str(len(normal)+len(rare)+len(elite)+len(superrare)+len(ultrarare)+len(priority)) + " cards in total, not counting unique cards." )
    
    #Get card information 
    @commands.command() 
    async def card( self, ctx, *args ):
        """Query Miot for information on a card."""
        try:
            query = ' '.join( args ).lower()
            if query in mechanics.cardList:
                await ctx.send( str( mechanics.cardList[query.lower()] ) )
            else:
                await ctx.send( "Card not found." )
        except Exception as e:
            print(e)

    #Get shipfu information 
    @commands.command() 
    async def ship( self, ctx, *args ):
        """Ship Query"""
        try:
            query = ' '.join( args ).lower()
            if query in mechanics.shipList:
                card = mechanics.shipList[query.lower()]
                color = mechanics.color_lookup(card.faction)
                rare = mechanics.rarity_lookup(card.rarity)
                faction = mechanics.faction_icon(card.faction)
                icon = card.icon
                name = "{}  ~**{}**~".format(card.id, card.name)
                forwiki = (card.name).split()[0]
                aquote = "*Quote:~*"
                details = (
                    "Rarity: **{}**\nClass: {}\nSkills: {}\nCost: {}\n\n".format(rare, card.subtype, card.skills, card.cost)
                )
                more_details = "{} \n\n[Wiki Link](https://azurlane.koumakan.jp/{})\n\nAzur Skill: {}".format(card.quote, forwiki, card.more)
                embed = discord.Embed(colour=color)
                embed.set_author(name=card.faction, icon_url=faction)
                embed.set_thumbnail(url=icon)
                embed.add_field(name=name, value=details)
                embed.add_field(name=aquote, value=more_details)
                embed.set_footer(text=card.desc)
                await ctx.send(embed=embed)
            else:
                await ctx.send( "No Shipfu found!" )
        except Exception as e:
            print(e)

    @commands.command() 
    async def waif( self, ctx, *args):
        """Shipfu Searching at it's finest"""

        channel = ctx.channel
        queryList = args
        vs = []
        for ship in mechanics.shipList:
            valid = False
            for query in queryList:
                if query.lower() in ship.lower():
                    valid = True
            if valid == True:
                vs.append(ship)
        
        if len(vs) > 1:
            # menu goes here I guess
            emotes = ['0⃣','1⃣','2⃣','3⃣','4⃣','5⃣','6⃣','7⃣','8⃣','9⃣', '🔟']
            toSend = "**__Ships found:__**"
            for x in vs:
                toSend += "\n{}. *{}*".format(emotes[vs.index(x)+1], x.title())
            msg = await ctx.send(toSend)
            
            for i in range(len(vs)):
                await msg.add_reaction(emotes[i+1])
            def check(r, user):
                return all([user == ctx.author, r.message.id == msg.id, r.emoji in emotes])
            res, usr = await self.bot.wait_for('reaction_add', check=check)
            selship = vs[emotes.index(str(res.emoji))-1]
        elif len(vs) == 1:
            selship = vs[0]
        else:
            await ctx.send("No ships found!")
            return
            
        fship = mechanics.shipList[selship]
        async with channel.typing():
            await self.draw_profile(ctx, fship)
            await channel.send(file=discord.File(datapath + 'data/temp/ship_profile.png'), content='**{}**'.format(fship.name))
            ## try:
                # os.remove(datapath + 'temp/ship.png')
            #except Exception as e:
                #print(e)
            # except:
                # pass
        #except Exception as e:
            #print(e)
        # except:
            # await ctx.send( "Oh ship... I can't find her!")

    #Get game definition
    @commands.command() 
    async def define( self, ctx, *args ):
        """Query Mio for the definition of a game term."""
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
            await ctx.send( "Incorrect syntax. ,,showoff <cardname>" )
        
        try:
            if cardLower in [x.lower() for x in getPlyData( ctx.author )['collection'].keys()]:
                await ctx.send( ctx.author.name + " has a shiny " + card + "!" )
            else:
                await ctx.send( "But " + ctx.author.name + " you dont have a " + card + "!" )
        except:
            await ctx.send( "You need to be registered to show stuff off. ,,register" )

    @commands.command()
    async def openpack(self, ctx, *args):
        """OPEN A SHINY NEW PACK!"""
        try:
            if mechanics.getPacks(ctx.author) < 1:
                await ctx.send( "You don't have any packs to open :( Use ,,buypack to get more!" )
                return
        except:
            await ctx.send( "You aren't registered yet. Use ,,register")
            return
            
        #Grab all the cards
        normal, rare, elite, superrare, ultrarare, priority = [], [], [], [], [], []
        for card in mechanics.cardList:
            if mechanics.cardList[card].rarity == 'N':
                normal.append( mechanics.cardList[card].name )
            elif mechanics.cardList[card].rarity == 'R':
                rare.append( mechanics.cardList[card].name )
            elif mechanics.cardList[card].rarity == 'E':
                elite.append( mechanics.cardList[card].name )
            elif mechanics.cardList[card].rarity == 'SR':
                superrare.append( mechanics.cardList[card].name )
            elif mechanics.cardList[card].rarity == 'UR':
                ultrarare.append( mechanics.cardList[card].name )
            elif mechanics.cardList[card].rarity == 'PR':
                priority.append( mechanics.cardList[card].name )

        stringToSay = ( ":star: :star2: :star2: :star2: :star2: :star2: :star2: :star2: :star2: :star2: :star:\n:star: :confetti_ball:           You got new cards!           :confetti_ball: :star:\n" )
        
        #Pick the cards, build the string
        for i in range( 5 ):
            #TODO: can't get 5+ of the same card
            cardsReceived.append( random.choice( normal ) )
            stringToSay += ":star: :star: Normal: " + cardsReceived[i] + "\n"
        for i in range( 2 ):
            cardsReceived.append( random.choice( rare ) )
            stringToSay += ":star: :star: :star: Rare: " + cardsReceived[i+5] + "\n"
        cardsReceived.append( random.choice( elite ) )
        stringToSay += ":star: :star: :star: :star: Elite: " + cardsReceived[7] + "\n"
        #cardsReceived.append( random.choice( superrare ) )
        #stringToSay += ":star: :star: :star: :star: :star: **Super Rare: " + cardsReceived[9] + "**\n"
        #cardsReceived.append( random.choice( ultrarare ) )
        #stringToSay += ":star: :star: :star: :star: :star: :star: **Ultra Rare: " + cardsReceived[13] + "**\n"
        #cardsReceived.append( random.choice( priority ) )
        #stringToSay += ":star: :star: :star: :star: :star: :star: **Priority: " + cardsReceived[19] + "**\n"
        stringToSay += ":star: :star2: :star2: :star2: :star2: :star2: :star2: :star2: :star2: :star2: :star:"
        
        await ctx.send( stringToSay )
        
        #Set their data
        for card in cardsReceived:
            grantCard( ctx.author, card, 1 )
        grantPacks( ctx.author, -1 )
        
    #Buy packs
    @commands.command()
    async def buypack( self, ctx, amt: int = 1 ):
        """Buy some packs! ,,buypack <amount>"""
        #Just make sure they can
        if amt < 1:
            await ctx.send("Invalid input." )
            return
        if not await bank.can_spend(ctx.author, amt * config.PACK_PRICE):
            await ctx.send("Not enough money for {amt} packs. They are currently ${pkpr} each, coming to a total of ${totalcost}, whereas you have ${bal}.".format(
                           amt=amt,
                           pkpr=config.PACK_PRICE,
                           totalcost=amt*config.PACK_PRICE,
                           bal=await bank.get_balance(ctx.author)
            ))
            return
        #Data stuff, then printing
        grantPacks( ctx.author, amt )
        grantMoney( ctx.author, -1 * amt * config.PACK_PRICE )
        if amt == 1:
            await ctx.send( "Bought a pack! Open it with =openpack." )
        else:
            await ctx.send( "Bought " + str(amt) + " packs!!!! Open them with =openpack!!!!!!!" )
        
    #Checking your packs and $
    @commands.command()
    async def bal( self, ctx, *args ):
        """Get your current balance and amount of packs."""
        try:
            await ctx.send( "You currently have $" + str(getBal(ctx.author)) + " and "+str(mechanics.getPacks(ctx.author))+" pack(s)." )
        except:
            await ctx.send( "You aren't registered. Use =register" )
        
    #Trading
    @commands.command()
    async def cardtrade( self, ctx, target: discord.Member = None, *args ):
        """Trade with another user. ,,trade <@ user>"""
        if target == None:
            await ctx.send( "You must pick someone to trade with! Syntax: =trade <@ user>" )
            return
        if ctx.author == target:
            await ctx.send( "Why would you trade with yourself? :confounded:" )
            return
        trader, tradee = [], []
        await ctx.send( "Type 'quit' at any time to quit the trade menu." )
        await ctx.send( "What are you offering? Syntax: <amount>x <card> or $<money amount>. For example:\n2x Voracity\n$20" )
        message = await self.bot.wait_for_message( author=ctx.author, timeout=90 )
        if message.content.lower().startswith('quit'):
            await ctx.send( "Quit the trade menu." )
            return
        
        #Setting up data for trader's offerings
        messageList = message.content.split( '\n' )
        for idx,line in enumerate(messageList):
            messageList[idx] = line.split( 'x ' )
            
        #has data check + data retrieval
        try:
            playerData = getPlyData(ctx.author)
        except:
            await ctx.send( "You aren't registered yet. Type =register" )
            return
            
        #Go through the cards and validate, then add to trade
        for cardEntry in messageList: #for each [2, "caltrops"], for example
            cardPair = None
            #formatting and data getting
            if cardEntry[0][0] == '$':
                with open('player_data/'+str(ctx.author)+'.txt', 'r') as json_file: 
                    traderMoney = json.loads(json_file.read())['money']
                if traderMoney < int(cardEntry[0][1:]) or int(cardEntry[0][1:]) < 0:
                    await ctx.send( "You don't have enough money." )
                    return
                trader.append( cardEntry[0][1:] )
            else:   
                try:
                    for item in playerData['collection'].items():
                        if cardEntry[1].lower() == item[0].lower():
                            cardPair = item
                except:
                    await ctx.send( "Invalid format!" )
                    return
                    
                if cardPair == None:
                    await ctx.send( cardEntry[1] + " isn't in your collection." )
                    return
                if cardPair[1] < int(cardEntry[0]):
                    await ctx.send( "You don't have that many "+cardEntry[1]+" in your collection." )
                    return
                
                trader.append(cardEntry)
        
        await ctx.send( "What do you want in return? (same syntax)" )
        message = await self.bot.wait_for_message( author=ctx.author, timeout=90 )
        if message.content.lower().startswith('quit'):
            await ctx.send( "Quit the trade menu." )
            return
        
        #Setting up data for trader's offerings
        messageList = message.content.split( '\n' )
        for idx,line in enumerate(messageList):
            messageList[idx] = line.split( 'x ' )
            
        #has data check + data retrieval
        try:
            playerData = getPlyData(target)
        except:
            await ctx.send( "Target isn't registered yet." )
            return
            
        #Go through cards and validate, then add to trade
        for cardEntry in messageList: #for each [2, "caltrops"], for example
            cardPair = None
            #formatting and data getting
            if cardEntry[0][0] == '$':
                with open('player_data/'+str(target.id)+'.txt', 'r') as json_file: 
                    tradeeMoney = json.loads(json_file.read())['money']
                if tradeeMoney < int(cardEntry[0][1:]) or int(cardEntry[0][1:]) < 0:
                    await ctx.send( "He or she doesn't have enough money." )
                    return
                tradee.append( cardEntry[0][1:] )
            else:   
                try:
                    for item in playerData['collection'].items():
                        if cardEntry[1].lower() == item[0].lower():
                            cardPair = item
                except:
                    await ctx.send( "Invalid format!" )
                    return
                    
                if cardPair == None:
                    await ctx.send( cardEntry[1] + " isn't in your collection." )
                    return
                if cardPair[1] < int(cardEntry[0]):
                    await ctx.send( "You don't have that many "+cardEntry[1]+" in your collection." )
                    return
                
                tradee.append(cardEntry)
        #wow that was a lot. let's get the other user's approval then do the trade now.
        print(str(trader) + " | " + str(tradee))
        def check(msg):
            print('checking')
            return msg.content.lower().startswith('yes') or msg.content.lower().startswith('no')
        await ctx.send(  target.name + ": Do you accept the above trade? ('yes' or 'no')" )
        message = await self.bot.wait_for_message( author=target, check=check, timeout=30 )
        if message.content.lower().startswith('no'):
            await ctx.send( "Trade request denied." )
            return
        #Complete the trade
        elif message.content.lower().startswith('yes'):
            #give trader the tradee's stuff
            for item in tradee:
                if isinstance( item, str ):
                    grantMoney( ctx.author.id, int(item) )
                    grantMoney( target.id, -1*int(item) )
                else:
                    grantCard( target.id, item[1], -1*int(item[0]) )
                    grantCard( ctx.author.id, item[1], item[0] )
            #give tradee the trader's stuff
            for item in trader:
                if isinstance( item, str ):
                    grantMoney( ctx.author.id, -1*int(item) )
                    grantMoney( target.id, int(item) )
                else:
                    grantCard( target.id, item[1], item[0] )
                    grantCard( ctx.author.id, item[1], -1*int(item[0]) )
            await ctx.send( "Trade complete!" )

    async def register( self, ctx ):
        playerID = ctx.author.id
        if os.path.isfile(datapath + 'player_data/'+str(playerID)+'.txt'):
            return # already registered, do nothing
        playerData = {
            "collection": {
                "Abukuma": 1,
                "Bullin MKII": 2,
                "Akagi chan": 1,
                "Ayanami Witch in Ambush": 2,
                "Brooklyn": 1
            },
            "selectedDeck": 0,
            "packs": 4,
            "decks": [ defaultDeck1, defaultDeck2, [], [], [] ],
            "decknames": [ "Swarmers", "H/D Combo", "", "", "" ] #just cleaner than making "decks" a dict...
        }

        with open(datapath + 'player_data/'+str(playerID)+'.txt', 'w') as outfile:
            json.dump(playerData, outfile)
        
    def cog_unload(self):
        self.bot.remove_listener(self.listener)

    __del__ = cog_unload