import os
import random, math
from . import mechanics

#This file retrieves all cards and nodes for the main game to use

import pathlib
datapath = str(pathlib.Path(__file__).parent) + "/"

cardsDB = {}
nodesDB = {}
shipsDB = {}

class Card:
	#Set up the card object
	def __init__(self, name, rarity, cost, skill, targets, cardtype, ability):
		self.name = name
		self.rarity = rarity
		self.cost = cost
		self.skill = skill
		self.targets = targets
		self.cardtype = cardtype
		self.func = ability


	def __str__(self):
		return "**~ " + self.name + " ~** | Rarity: **" + self.rarity + "** | Cost: **" + str(self.cost) + "**\n " + str(self.skill)
		# return str(self.icon) + "\n**" + self.name + "**\n" + str(self.skill) + "\nRarity: " + self.rarity + "\nCost: " + str(self.cost)


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


class Ship:
	#Set up the ship object
	def __init__(self, id, id2 ,name, skinname, color, rarity, desc, subtype, faction, cost, quote, skills, skill, icon, skin, more, more2):
		self.id = id
		self.id2 = id2
		self.name = name
		self.skinname = skinname
		self.color = color
		self.rarity = rarity
		self.desc = desc
		self.subtype = subtype
		self.faction = faction
		self.cost = cost
		self.quote = quote
		self.skills = skills
		self.skill = skill
		self.icon = icon
		self.skin = skin
		self.more = more
		self.more2 = more2

	def __str__(self):
		return "**~ " + self.name + " ~** | Rarity: **" + self.rarity + "** | Cost: **" + str(self.cost) + "**\n " + str(self.more)
		#return str(self.id) + self.name + self.rarity + self.desc + self.subtype + self.faction + str(self.cost) + self.quote + self.skills + self.icon + self.skin

def getCards():
    for filename in os.listdir(datapath + 'cards'):
        exec(open(datapath + 'cards/'+filename).read())
    return cardsDB

def getNodes():
    for filename in os.listdir(datapath + 'nodes'):
        exec(open(datapath + 'nodes/'+filename).read())
    return nodesDB

def getShips():
    for filename in os.listdir(datapath + 'cards'):
        exec(open(datapath + 'cards/'+filename).read())
    return shipsDB

def addCard(name, cost, rarity, skill, targets, cardtype, ability):
    cardsDB[name.lower()] = Card(name, cost, rarity, skill, targets, cardtype, ability)

def addNode(name, skill, ability, oneTimeAbility, energy, deathFunc, triggerType, triggerFunc):
    nodesDB[name.lower()] = GameNode(name, skill, ability, oneTimeAbility, energy, deathFunc, triggerType, triggerFunc)

def addShip(id, id2, name, skinname, color, rarity, desc, subtype, faction, cost, quote, skills, skill, icon, skin, more, more2):
    shipsDB[name.lower()] = Ship(id, id2 ,name, skinname, color, rarity, desc, subtype, faction, cost, quote, skills, skill, icon, skin, more, more2)
