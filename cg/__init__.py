from .azur import Azur

# from .deckbuilding import Deckbuilding
# from .collecting import Collecting

def setup(bot):
    n = Azur(bot)
    bot.add_listener(n.listener, "on_message")
    bot.add_cog(n)