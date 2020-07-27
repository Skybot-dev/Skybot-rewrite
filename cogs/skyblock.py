import discord
from discord.ext import commands


class Skyblock(commands.Cog):
    def __init__(self, bot):
        self.bot=bot


    @commands.Cog.listener()
    async def on_ready(self):
        pass


def setup(bot):
    bot.add_cog(Skyblock(bot))