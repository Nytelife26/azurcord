from .cardList import *
import json, asyncio, math, time, random, os
from . import config
from redbot.core import bank
from redbot.core import Config
import pathlib
datapath = str(pathlib.Path(__file__).parent) + "/"

"""Extra functions that work better in their own file"""

def __init__(self, ctx, bet):
    self.bet = bet
    self.ctx = ctx
    self.player = ctx.author
    self.guild = ctx.guild
    
    
def initData():
    global cardList
    cardList = getCards() 
    global nodeList
    nodeList = getNodes()
    global shipList
    shipList = getShips()


#Retrieve account information
def getPlyData( ply ): #takes a discord user object, not game object
    try:
        with open(datapath + 'player_data/'+str(ply.id)+'.txt', 'r') as json_file: 
            return json.loads(json_file.read())
    except:
        return None
    
#Handling bot messages outside the bot files
async def mechMessage( bot, chn, msg ):
    await chn.send(msg)
        
#Handles a Node entering the field 
def nodeETB( ply, nodeName ):
    nodeObj = nodeList[ nodeName.lower() ]
    nodeObj.spawnFunc(ply,ply.opponent)
    ply.energy = ply.energy + nodeObj.energy
    
#Player sacrificed a node as part of an ability (for health)    
def sacNode( ply, enemy, index ): #Returns the node OBJECT, not the name.
    removedNode = nodeList[ply.nodes[index].lower()]
    removedNode.deathFunc( ply, enemy ) #gets rid of temp effects n stuff
    ply.nodes.remove( ply.nodes[index] )
    healthToGain = abs(round( 0.1 * ply.hunger * removedNode.energy ))
    if 'Feast' not in ply.nodes and 'Feast' not in enemy.nodes: #card...specific......
        ply.lifeforce += healthToGain
    ply.energy -= removedNode.energy
    gameTrigger( "SAC", ply, removedNode )
    return removedNode
    
#Player sacrificed a card for health
def sacCard( ply ):
    poppedCard = ply.deck.pop()
    cost = cardList[poppedCard.lower()].cost
    lifeToGain = abs(round( 0.1 * ply.desperation * cost ))
    ply.lifeforce += lifeToGain
    gameTrigger( "SACR", ply, None )
    return poppedCard, lifeToGain
    
#Player activated a node
async def activateNode( nodeName, activePlayerObj, opponentObj ):
    playedObject = nodeList[nodeName.lower()]
    await playedObject.func( activePlayerObj, opponentObj )
    
#Get player object from a discord ID string
def discordUserToPlayerObj( playerID ):
    #Returns the player object for the searched player ID
    for game in config.matches:
        if config.matches[game].challenger == playerID:
            return config.matches[game].chalObj
        elif config.matches[game].defender == playerID:
            return config.matches[game].defObj
        else:
            return None
            
#Get discord user object from a player object
def playerObjToDiscordID( playerObj ):
    #Returns the player object for the searched player ID
    for game in config.matches:
        if config.matches[game].chalObj == playerObj:
            return config.matches[game].challenger
        elif config.matches[game].defObj == playerObj:
            return config.matches[game].defender
        else:
            return None
            
#takes a TCGame object
def isGameRunning( match ):
    if match.challenger in config.matches.keys() or match.defender in config.matches.keys():
        return True
    else:
        return False
    
#Game ended. Takes the loser's discord ID
async def gameOver( loserID ): #get ONLY discord ID of LOSER
    loserObj = discordUserToPlayerObj( loserID )
    winnerID = playerObjToDiscordID( loserObj.opponent )
    bot = loserObj.bot
    ctx = loserObj.ctx
    loser = ctx.guild.get_member( loserID )
    winner = ctx.guild.get_member( winnerID )
    if winner.id in config.matches:
        matchWager = config.matches[winner.id].wager
        matchTime = config.matches[winner.id].startTime
        timedOut = config.matches[winner.id].timedOut
        del config.matches[winner.id]
    elif loser.id in config.matches:
        matchWager = config.matches[loser.id].wager
        matchTime = config.matches[loser.id].startTime
        timedOut = config.matches[loser.id].timedOut
        del config.matches[loser.id]
    secondsElapsed = time.time() - matchTime
    await mechMessage(bot, ctx.channel, "<:merit:621657933091962901> {} just lost to {} at Azur after {} seconds of play time!".format(loser.name, winner.name, secondsElapsed))
    if matchWager > 0:
        await mechMessage(bot, ctx.channel, "<:628267540744896512:> {} won the wager of {}".format(winner.name, matchWager))
        await bank.deposit_credits(winner, matchWager)
        await bank.withdraw_credits(loser, matchWager)
    #random money pickup chance
    if secondsElapsed > 127 and not timedOut:
        if random.randint(0,4)%2 == 1:
            givenMoney = random.randint( 15, 40 )
            await bank.deposit_credits(winner, givenMoney)
            await mechMessage(bot, winner, "You found $" + str(givenMoney) + " lying in your opponent's wrecked shipfus!")
        
#Give someone an amount of a card (takes their discord ID)
def grantCard( ply, card, amount ): 
    with open(datapath + 'player_data/'+str(ply)+'.txt', 'r') as json_file: 
        fileContents = json.loads(json_file.read())
        
    foundCard = False
    for cards in fileContents['collection']:
        if card.lower() == cards.lower():
            foundCard = True
            fileContents['collection'][cards] += int(amount)
    if foundCard == False:
        fileContents['collection'][cardList[card.lower()].name] = 1
            
    with open(datapath + 'player_data/'+str(ply)+'.txt', 'w') as outfile:
        json.dump(fileContents, outfile)
    
#Get someone's amount of packs (takes discord ID)   
def getPacks( ply ):
    with open(datapath + 'player_data/'+str(ply)+'.txt', 'r') as json_file:
        return json.loads(json_file.read())['packs']
    
#Grants someone some packs (takes discord ID)   
def grantPacks( ply, amount ):
    with open(datapath + 'player_data/'+str(ply)+'.txt', 'r') as json_file: 
        fileContents = json.loads(json_file.read())
        
    fileContents['packs'] += amount
            
    with open(datapath + 'player_data/'+str(ply)+'.txt', 'w') as outfile:
        json.dump(fileContents, outfile)

#Automates damage dealing
async def damage( playerObj, amt ):
    playerObj.lifeforce -= amt
    gameTrigger( "DAMAGE", playerObj, amt )
    if playerObj.lifeforce <= 0:
        await gameOver( playerObjToDiscordID( playerObj ) ) #no ids
        return
    
#Automates lifegain
async def heal( playerObj, amt ):
    playerObj.lifeforce += amt
    gameTrigger( "HEAL", playerObj, amt )
    if playerObj.lifeforce <= 0:
        await gameOver( playerObjToDiscordID( playerObj ) )
        return

def color_lookup(color):
    colors = {"Bilibili": 0xCCF2FF, "Eagle Union": 0x00BFFF, "Eastern Radiance": 0xEB99FF, "Iris Libre": 0xFFFF66, "Ironblood": 0xE60000, "KizunaAI": 0xFF66CC, "Neptunia": 0x9933FF, "North Union": 0xCCCCCC, "Royal Navy": 0x000099, "Sakura Empire": 0xFFCCE6, "Sardegna Empire": 0x006600, "Sirens": 0x00001A, "Universal": 0xFFCC00, "Utawarerumono": 0xCD5C5C, "Vichya Dominion": 0x9C3030}
    color = colors[color]
    return color
    
def faction_icon(faction):
    factions = {"Bilibili": "https://i.imgur.com/nRUg46F.png", "Eagle Union": "https://i.imgur.com/864D3yF.png", "Eastern Radiance": "https://i.imgur.com/UttBZhH.png", "Iris Libre": "https://i.imgur.com/CV7fIyO.png", "Ironblood": "https://i.imgur.com/HjrSesh.png", "KizunaAI": "https://i.imgur.com/r0kZKAN.png", "Neptunia": "https://i.imgur.com/JEJcnhR.png", "North Union": "https://i.imgur.com/UBMkkon.png", "Royal Navy": "https://i.imgur.com/2QPc06a.png", "Sakura Empire": "https://i.imgur.com/fU1qcEx.png", "Sardegna Empire": "https://i.imgur.com/nIaCV8q.png",  "Sirens": "https://i.imgur.com/TXNtsJh.png", "Universal": "https://i.imgur.com/w1t921Q.png", "Utawarerumono": "https://i.imgur.com/UPd42la.png", "Vichya Dominion": "https://i.imgur.com/ocvDvtz.png"}
    faction = factions[faction]
    return faction

def rarity_lookup(rare):
    rarity = {"N": "Normal", "R": "Rare", "E": "Elite", "SR": "Super Rare", "UR": "Ultra Rare", "PR": "Priority", "DC": "Decisive"}
    rare = rarity[rare]
    return rare

"""Handle triggers. 
dataPassed is the node destroyed/created, damage dealt/healed, etc
playerObj is the player who was affected. ONLY the opponent player's nodes will trigger.
Make sure to print out using the new mechMessage() so people know what was triggered.
Could also use this to log!
Possible triggers: "HEAL", "DAMAGE", "SCUTTLE", "SACR", "SAC", "NODESPAWN", "PLAYED_CARD"
All currently only trigger your opponent's Nodes. Eventually do this specific for each type.
"""
def gameTrigger( trigger, playerObj, dataPassed ):
    for node in playerObj.nodes:
        if nodeList[node.lower()].triggerType == trigger:
            playerObj.log.append( playerObj.name + "'s " + node + " was triggered." )
            playerObj.nodesToTrigger.append( [node.lower(), dataPassed, "friendly"] )
    for node in playerObj.opponent.nodes:
        if nodeList[node.lower()].triggerType == trigger:
            playerObj.log.append( playerObj.opponent.name + "'s " + node + " was triggered." )
            playerObj.opponent.nodesToTrigger.append( [node.lower(), dataPassed, "enemy"] )
    if trigger == "SCUTTLE":
        playerObj.log.append( playerObj.name + " scuttled: " + str(dataPassed) )
    elif trigger == "SAC":
        playerObj.log.append( playerObj.name + "'s " + dataPassed.name + " was destroyed or sacrificed." )
    elif trigger == "DISCARD":
        playerObj.log.append( playerObj.name + " lost " + dataPassed + "." )
    elif trigger == "DAMAGE":
        playerObj.log.append( playerObj.name + " took " + str(dataPassed) + " damage." )
    elif trigger == "HEAL":
        playerObj.log.append( playerObj.name + " Reserves changed by " + str(dataPassed) + "." )
