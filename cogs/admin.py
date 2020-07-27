import os
import time
import copy
import discord
from loguru import logger
from utils.util import is_staff, get_config
from discord.ext import commands, tasks


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot=bot
        self.cycleStatus.start()

    @commands.Cog.listener()
    async def on_ready(self):
        pass

    @commands.check(is_staff)
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

    @commands.command()
    @commands.check(is_staff)
    async def reload_config(self, ctx):
        self.bot.config = get_config()
        return await ctx.send(f"`config reloaded by` {ctx.author.mention}")
    
    @commands.check(is_staff)
    @commands.command()
    async def timeit(self, ctx, *, command: str):
        msg = copy.copy(ctx.message)
        msg.content = ctx.prefix + command

        new_ctx = await self.bot.get_context(msg, cls=commands.Context)

        start = time.time()
        await new_ctx.reinvoke()
        end = time.time()

        await ctx.send(f'**{ctx.prefix}{new_ctx.command.qualified_name}** took **{end - start:.2f}s** to run')

    @tasks.loop(minutes=20)
    async def cycleStatus(self):
        choice = next(self.bot.status_list)
        if choice["type"] == "playing":
            await self.bot.change_presence(activity=discord.Game(name=choice["content"]))
        elif choice["type"] == "watching":
            await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=choice["content"]))
        elif choice["type"] == "listening":
            await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="a song"))
        print(f"set status to {str(choice)}")


def setup(bot):
    bot.add_cog(Admin(bot))