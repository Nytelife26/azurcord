VERSION = "0.1"

DECK_SIZE_MINIMUM = 10
STARTING_HAND_SIZE = 6
PACK_PRICE = 1000
CHALLENGE_TIMEOUT = 30 #How long to wait for someone to accept a challenge
TURN_TIMEOUT = 300 #How long to wait for someone to do an action on their turn before they forfeit the match

DEFINITIONS = {
	"Oil Reserves:": "This is the total oil you have, when it hits 0 you lose the battle.",
	"Map Nodes:": "This lists the usable and destroyable battle points (Nodes) that can be added and removed from the Battleground (Map)",
	"sacrifice:": "Removes the top card of your deck from the game, to gain oil",
	"scuttle:": "Removes the top card of your deck from the game. You will not gain oil.",
	"Zeal:": "This is your fleets motivation, the better their zeal the quicker the battle and less oil used! Returned amount is equal to zeal ",
	"Supply Routes:": "The amount of Oil that can be channelled to your fleet after each full round.",
	"Despair:": "The higher your despair the harder your Ships will strive to save and return oil to your precious reserves.",
}

#don't touch
matches = {}
