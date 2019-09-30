#import mechanics
import time
import random
from .mechanics import *

class Card:
	#Set up the card object
	def __init__(self, name, cost, rarity, skill, targets, cardtype, ability):
		self.name = name
		self.cost = cost
		self.rarity = rarity
		self.func = ability
		self.targets = targets
		self.skill = skill
		self.cardtype = cardtype
		
	def __str__(self):
		return "**" + self.name + " (" + str(self.cost) + ")** *" + self.rarity + "* : " + self.skill
        
class Cardfetch:
	#Set up the card object
	def __init__(self, id, name, rarity, decs, subtype, faction, cost, quote, skills, skill, icon, skin):
		self.id = id
		self.name = name
		self.rarity = rarity
		self.decs = decs
		self.subtype = subtype
		self.faction = faction
		self.cost = cost
		self.quote = quote
		self.skills = skills
		self.skill = skill
		self.icon = icon
		self.skin = skin

	def __str__(self):
		return str(self.icon) + "\n**" + self.name + "**\n" + str(self.skill) + "\nRarity: " + self.rarity + "\nCost: " + str(self.cost)


class TCGame:

	def __init__(self, challenger, defender, wager):
		self.challenger = challenger
		self.defender = defender
		self.chalObj = None #object for challenger
		self.defObj = None #object for defender
		self.wager = wager
		self.startTime = time.time()
		self.gameMessage = None
		self.timedOut = False
		
	def __str__(self):
		return( self.challenger + " (HP: " + str(self.chalObj.lifeforce) + ") challenging " + self.defender + " (HP: " + str(self.defObj.lifeforce) + ")." )

class GameNode:
	#Set up the Node object
	def __init__(self, name, skill, ability, oneTimeAbility, energy, deathAbility, triggerType, triggerFunc):
		self.name = name
		self.func = ability #should trigger start of your turn
		self.spawnFunc = oneTimeAbility
		self.skill = skill
		self.energy = energy
		self.deathFunc = deathAbility
		self.triggerType = triggerType
		self.triggerFunc = triggerFunc
		
	def __str__(self):
		return "**" + self.name + " ("+str(self.energy)+")**: " + self.skill

class Player:

	def __init__(self, name, deck, hand, bot, ctx):
		self.name = name
		self.deck = deck #last element of deck is the top of the deck (next to draw)
		self.hand = hand
		self.bot = bot #so the bot can do its thing
		self.ctx = ctx #so the bot can do its thing
		self.energy = 2
		self.lifeforce = 50
		self.active = False
		self.nodes = []
		self.log = []
		self.maxNodes = 6
		self.eotEffects = []
		self.nodesToTrigger = [] #ugh. triggers all nodes later cause await is DUMB.
		self.sacrificed = False #if they already used 'sacrifice' this turn
		self.playedNode = False #if they already played a node this turn
		self.hunger = 10 #Rate of lifegain from sacrificing nodes (/10)
		self.desperation = 10 #Rate of lifegain from sacrificing (/10)
		self.opponent = None #just so we have this stored without needing dumb imports
		self.lastHandDM = None #for better hand DMing
		self.cardsThisTurn = 0 #spells played this turn
		"""Card-specific variables (TODO: Find a better alternative)"""
		self.mindSwap = False
		self.desperationBoost = 0 #reset desperation boost (subtract this at start of turn)
		self.opponentCantSpawnNodes = False
		
	#Custom function in case I end up wanting to do something with shuffling (e.g hooks)
	def shuffle(self):
		random.shuffle( self.deck )
		
	def addMaxNodes(self, amt):
		#set
		self.maxNodes += amt
		if self.maxNodes > 10:
			self.maxNodes = 10
		if self.maxNodes < 0:
			self.maxNodes = 0
		#kill excess nodes
		while len(self.nodes) > self.maxNodes:
			sacNode( ply, self.opponent, self.nodes[self.maxNodes] )
		
		
	def newTurn(self):
		self.eotEffects = []
		self.active = False
		self.playedNode = False
		if self.hunger < 0:
			self.hunger = 0
		if self.desperation < 0:
			self.desperation = 0
		self.cardsThisTurn = 0
		
	def newMyTurn(self):
		self.sacrificed = False
		self.active = True
		"""Card specific steps (TODO: Find a better alternative)"""
		if self.mindSwap: #Mind Swap
			self.desperation, self.opponent.desperation = self.opponent.desperation, self.desperation
			self.hunger, self.opponent.hunger = self.opponent.hunger, self.hunger
			self.mindSwap = False
		if not self.desperationBoost == 0:
			self.desperation -= self.desperationBoost
			self.desperationBoost = 0
		self.opponentCantSpawnNodes = False
		gameTrigger( "NEW_TURN", self, None )
		
	def drawCard(self):
		#sacrifice out
		if len(self.deck) <= 0:
			return False
		self.hand.append( self.deck.pop() )
		return True
		gameTrigger( "DRAW", self, None )
		
	def randomDiscard(self):
		if len(self.hand) > 0:
			discarded = self.hand.pop( random.randint(0,len(self.hand)-1) )
		gameTrigger( "DISCARD", self, discarded )
		
	def addNode(self, nodeName): #TODO: possibly move to mechanics.py for consistency with sacNode()
		if self.opponent.opponentCantSpawnNodes:
			return
		gameTrigger( "NODESPAWN", self, nodeName )
		if len(self.nodes) >= self.maxNodes:
			sacNode( self, self.opponent, self.maxNodes-1 )
		self.nodes.insert(0, nodeName)
		nodeETB( self, nodeName )
		
		
	def scuttle(self, amt): #sacrificing without oil gain
		burnedCards = []
		for i in range(amt):
			if len(self.deck) > 0:
				burnedCards.append( self.deck.pop() )
		gameTrigger( "SCUTTLE", self, burnedCards )
			
	def removeNode(self, nodeName, enerCost):
		for node in self.nodes:
			if nodeName.lower() == node:
				self.nodes.remove( nodeName )
				break
		self.energy = self.energy - enerCost
			
	def __str__(self):
		#return "[--"+self.name+"--]\nHP: "+str(self.lifeforce)+"\nEnergy: "+ str(self.energy) +"\nCards in hand: "+str(len(self.hand))+"\nCards in deck: "+str(len(self.deck))+"\nNodes: "+str(self.nodes)+"\nUseage "+str(self.hunger)+"\nDesperation: "+str(self.desperation)
		return ("[-- <:bofors_right:621656194867527730> <:bofors_right:621656194867527730> <:Azur:621651699215368202> **"+self.name.upper()+"** <:Crimson:621651747118514186> <:bofors_left:621656169882189855> <:bofors_left:621656169882189855> --]\n" +
			"<:oilup:621406394964508672> Oil Reserves: *"+str(self.lifeforce)+" ("+str(self.energy)+" zeal)*\n" +
			"<:deck:621650921792864258> Ships: *" + str(len(self.hand)) + " (+" + str(len(self.deck)) + " dock)*\n" +
			":map: Map Nodes: *" + str(self.nodes) + "*\n" + 
			"<:oilout:621647392726581258> Supply Routes: *" + str(self.hunger) + "*\n" + 
			"<:bully:619926326723215380> Despair: *" + str(self.desperation) + "*")
