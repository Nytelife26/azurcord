import discord
from discord.ext import commands
import asyncio, json, os, random
from .mechanics import *
from . import config

class Collecting():

    #Opening a pack
    @commands.command()
    async def openpack(self, ctx, *args):
        """OPEN A SHINY NEW PACK!"""
        try:
            if getPacks( ctx.author.id ) < 1:
                await ctx.send( "You don't have any packs to open :( Use =buy to get more!" )
                return
        except:
            await ctx.send( "You aren't registered yet. Use =register" )
            return
            
        #Grab all the cards
        normal, rare, elite, superrare, ultrarare, priority = [], [], [], [], [], []
        cardsReceived = []
        for card in cardList:
            if cardList[card].rarity == 'N':
                normal.append( cardList[card].name )
            elif cardList[card].rarity == 'R':
                rare.append( cardList[card].name )
            elif cardList[card].rarity == 'E':
                elite.append( cardList[card].name )
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
            stringToSay += ":star: Normal: " + cardsReceived[i] + "\n"
        for i in range( 2 ):
            cardsReceived.append( random.choice( rare ) )
            stringToSay += ":star: Rare: " + cardsReceived[i+5] + "\n"
        cardsReceived.append( random.choice( elite ) )
        stringToSay += ":star: :star: **Elite: " + cardsReceived[7] + "**\n"
        stringToSay += ":star: :star2: :star2: :star2: :star2: :star2: :star2: :star2: :star2: :star2: :star:"
        
        await ctx.send( stringToSay )
        
        #Set their data
        for card in cardsReceived:
            grantCard( ctx.author.id, card, 1 )
        grantPacks( ctx.author.id, -1 )
        
    #Buy packs
    @commands.command()
    async def buy( self, ctx, amt: int = 1 ):
        """Buy some packs! =buy <amount>"""
        #Just make sure they can
        if amt < 1:
            await ctx.send( "Invalid input." )
            return
        if getBal( ctx.author.id ) < amt * config.PACK_PRICE:
            await ctx.send( "Not enough money for " + str(amt) + " packs. They are currently $" + str(config.PACK_PRICE) + " each." )
            return
        #Data stuff, then printing
        grantPacks( ctx.author.id, amt )
        grantMoney( ctx.author.id, -1 * amt * config.PACK_PRICE )
        if amt == 1:
            await ctx.send( "Bought a pack! Open it with =openpack." )
        else:
            await ctx.send( "Bought " + str(amt) + " packs!!!! Open them with =openpack!!!!!!!" )
        
    #Checking your packs and $
    @commands.command()
    async def bal( self, ctx, *args ):
        """Get your current balance and amount of packs."""
        try:
            await ctx.send( "You currently have $" + str(getBal(ctx.author.id)) + " and "+str(getPacks(ctx.author.id))+" pack(s)." )
        except:
            await ctx.send( "You aren't registered. Use =register" )
        
    #Trading
    @commands.command()
    async def trade( self, ctx, target: discord.Member = None, *args ):
        """Trade with another user. =trade <@ user>"""
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
                with open('player_data/'+str(ctx.author.id)+'.txt', 'r') as json_file: 
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
