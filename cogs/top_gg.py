import dbl
from loguru import logger
from discord.ext import commands


class TopGG(commands.Cog):
    """Handles interactions with the top.gg API"""

    def __init__(self, bot):
        self.bot = bot
        if self.bot.config["top_gg"]["enabled"]:
            self.token = self.bot.config["top_gg"]["token"] # set this to your DBL token
            self.dblpy = dbl.DBLClient(self.bot, self.token, autopost=True) # Autopost will post your guild count every 30 minutes

    async def on_guild_post():
        logger.debug("Server count posted successfully")
        
    @commands.Cog.listener()
    async def on_dbl_vote(self, data):
        logger.debug('Received an upvote')
        print(data)

def setup(bot):
    bot.add_cog(TopGG(bot))