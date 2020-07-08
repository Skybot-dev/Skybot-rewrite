import os
import discord
from loguru import logger
from discord.ext import commands


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot=bot


    @commands.Cog.listener()
    async def on_ready(self):
        pass

    @commands.command()
    async def reload(self, ctx : commands.Context):
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                try:
                    self.bot.reload_extension(f"cogs.{filename[:-3]}")
                    logger.info(f"reloaded cogs.{filename[:-3]}")
                except commands.ExtensionNotLoaded:
                    self.bot.load_extension(f"cogs.{filename[:-3]}")
                    logger.info(f"loaded cogs.{filename[:-3]}")
        await ctx.message.add_reaction("👌")
        


def setup(bot):
    bot.add_cog(Admin(bot))