import os
import time
import copy
import discord
from loguru import logger
from utils.util import is_staff, get_config
from discord.ext import commands, tasks
from utils.embed import Embed
from pymongo.errors import DuplicateKeyError
class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot: skybot = bot
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
    
    
    @commands.command(name="usagestats", aliases = ["ustats"])
    @commands.check(is_staff)
    async def usagestats(self, ctx, arg=None):
        usagestats = self.bot.admin_db["usagestats"]
        if arg and arg.lower() == "reset":
            async for cmd in usagestats.find({}):
                await usagestats.update_one(cmd, {"$set" : {"uses" : 0}})

            doc = await usagestats.find_one({"name" : "last_reset"})
            if doc and "date" in doc.keys():
                await usagestats.update_one({"name" : "last_reset"}, {"$currentDate" : {"date" : False}})
            else:
                await usagestats.insert_one({"name" : "last_reset", "date" : 0})
                await usagestats.update_one({"name" : "last_reset"}, {"$currentDate" : {"date" : False}})
            return await ctx.send("Reset usage stats.")
        
        embed = Embed(self.bot, ctx.author, title="Command Usage Stats")
        await embed.set_requested_by_footer()
        async for cmd in usagestats.find({}):
            if cmd["name"] != "last_reset":
                embed.add_field(name=cmd["name"].capitalize(), value="Uses: " + str(cmd["uses"]))
            else:
                embed.add_field(name="Last reset", value=str(cmd["date"])[:-7])
        await ctx.send(embed=embed)
        
    
    @commands.command()
    @commands.check(is_staff)
    async def blacklist(self, ctx, action:str="add", user: int=None, *, reason:str=None):
        if action.lower() == "add":
            try:
                await self.bot.users_db["blacklist"].insert_one({"_id": user, "reason": reason})
                await ctx.send(f"successfully added `{user}` to the blacklist for reason: `{reason}`")
            except DuplicateKeyError:
                return await ctx.send("user already blacklisted")
        elif action.lower() == "remove":
            await self.bot.users_db["blacklist"].delete_one({"_id": user})
            await ctx.send(f"successfully removed `{user}` from the blacklist for reason: `{reason}`")
        else:
            raise commands.BadArgument()
        await self.bot.update_blacklist()

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

    @tasks.loop(minutes=1)
    async def cycleStatus(self):
        choice = next(self.bot.status_list)
        if choice["type"] == "playing":
            await self.bot.change_presence(activity=discord.Game(name=choice["content"]))
        elif choice["type"] == "watching":
            await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=choice["content"]))
        elif choice["type"] == "listening":
            await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="a song"))
        logger.debug(f"set status to {str(choice)}")

    @cycleStatus.before_loop
    async def before_cycleStatus(self):
        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(Admin(bot))