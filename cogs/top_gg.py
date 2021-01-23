import dbl
import discord
from loguru import logger
from discord.ext import commands, tasks


class TopGG(commands.Cog):
    """Handles interactions with the top.gg API"""

    def __init__(self, bot):
        self.bot = bot
        self.config = self.bot.config["top_gg"]
        if self.config["enabled"]:
            self.token = self.config["token"] # set this to your DBL token
            self.dblpy = dbl.DBLClient(self.bot, self.token, autopost=True) # Autopost will post your guild count every 30 minutes
        self.check_votes.start()
        
    def cog_unload(self):
        self.check_votes.cancel()

    async def on_guild_post():
        logger.debug("Server count posted successfully")
        
    # @commands.Cog.listener()
    # async def on_dbl_vote(self, data):
    #     logger.debug('Received an upvote')
    #     print(data)
    
    @tasks.loop(hours=1)
    async def check_votes(self):
        if not self.config["enabled"]: return
        
        support_guild = self.bot.get_guild(self.bot.config["support_guild"]["ID"])
        role = support_guild.get_role(self.config["voter_role"])
        if not role: return
        
        upvotes = await self.dblpy.get_bot_upvotes()
        for upvote in upvotes:
            if upvote["id"] in [member.id for member in support_guild.members]:
                member = support_guild.get_member(upvote["id"])
                if role.id not in [role.id for role in member.roles]:
                    await member.add_roles(role, reason="Voted!")
            else:
                member = support_guild.get_member(upvote["id"])
                if member and role.id in [role.id for role in member.roles]:
                    await member.remove_roles(role, reason="No Voter Anymore!")
            
        

def setup(bot):
    bot.add_cog(TopGG(bot))