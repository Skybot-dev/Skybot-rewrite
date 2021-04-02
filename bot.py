import os
from time import time
from loguru import logger
import traceback
import discord
from discord.ext import commands

from database.init import init_client
from utils.util import get_config, trelloinit
from utils.skypy import exceptions
from utils import logging
from itertools import cycle

from discord_slash import SlashCommand, SlashContext, manage_commands, SlashCommandOptionType

intents = discord.Intents.default()
intents.members = True


class Skybot(commands.AutoShardedBot):
    def __init__(self):
        super().__init__(self.get_prefix, case_insensitive=True, intents=intents)
        
        logging.init_logging()

        logger.info([z for z in self.intents])
        self.db_client = init_client(self.loop)
        if self.db_client: logger.info("Connected to Database.")
        self.config = get_config()
        self.custom_emojis = get_config("emojis")
        if self.config["trello"]["enabled"]:
            self.trello_client, self.trello_board = trelloinit(self.config)
        self.admin_db = self.db_client["management"]
        self.users_db = self.db_client["users"]
        if self.config["slothpixel_key"]:
            self.slothpixel_key_string = f'?key={self.config["slothpixel_key"]}'
        else:
            self.slothpixel_key_string = ''
        if self.config["stats_api"] == "default":
            self.stats_api = "http://hypixel-skybot.ddns.net:3000/stats"
        else:
            self.stats_api = self.config["stats_api"]
        self.guilds_db = self.db_client["guilds"]
        self.scammer_db = self.db_client["scammer"]
        self.status_list = cycle(self.config["status_list"])
        self.remove_command("help")
        
        self.api_keys = self.config["api_keys"]

        if not self.api_keys:
            logger.warning("PLEASE SET AT LEAST ON API KEY, ELSE THE BOT WON'T WORK.")

        self.events = []
        
        self.slash = SlashCommand(self, sync_commands=True)

        self.load_cogs()
        self.start_time = time()

    async def cache_guild_chunk(self, guild: discord.Guild):
        if not guild.chunked:
            await guild.chunk()
        return guild.members


    async def get_prefix(self, message):
        if not message.guild:
            return commands.when_mentioned_or(self.config["default_prefix"])(self, message)

        prefix = await self.guilds_db["prefixes"].find_one({"_id" : message.guild.id})
        if prefix is not None:
            return commands.when_mentioned_or(prefix["prefix"])(self, message)
        else:
            return commands.when_mentioned_or(self.config["default_prefix"])(self, message)

     
    def load_cogs(self):
        for file in os.listdir("cogs"):
            if file.endswith(".py"):
                name = file[:-3]
                try:
                    self.load_extension(f"cogs.{name}")
                    logger.info(f"Loaded cogs.{name}")
                except Exception as e:
                    logger.error(f"Skybot couldn't load: {name}.")
                    logger.exception(e)
        

    async def update_blacklist(self):
        self.blacklisted_users = {z["_id"]: z["reason"] async for z in self.users_db["blacklist"].find({})}

    async def not_blacklisted(self, ctx):
        if ctx.author.id in self.blacklisted_users:
            reason = f"for reason: `{self.blacklisted_users[ctx.author.id]}`" or ""
            await ctx.send(f"You have been blacklisted from using the bot {reason}.")
            return False
        else:
            return True

    async def on_ready(self):
        await self.update_blacklist()
        logger.info("Skybot ready.")
        self.add_check(self.not_blacklisted)

    async def process_commands(self, message):
        ctx = await self.get_context(message)
        if not ctx.command or (message.author.bot and ctx.command.name not in ("status")):
            return
        await self.invoke(ctx)


    async def on_message(self, message):
        if not self.is_ready() : return
        await self.process_commands(message)

    async def on_message_edit(self, before, after):
        await self.wait_until_ready()
        await self.process_commands(after)






    async def on_command_completion(self, ctx):
        if not ctx.command_failed and not ctx.command.parents:
            usagestats = self.admin_db["usagestats"]

            result = await usagestats.update_one({"name" : ctx.command.name}, {"$inc" : {"uses" : 1}})
            if result.modified_count == 0:
                await usagestats.insert_one({"name" : ctx.command.name, "uses" : 1})
            

    async def on_command_error(self, ctx : commands.Context, exception):
        if isinstance(exception, commands.CommandNotFound):
            return #await ctx.send("`Command not found`", delete_after=3)
        if isinstance(exception, commands.NoPrivateMessage):
            return await ctx.send("This command can't be used in a private chat.", delete_after=7)
        if isinstance(exception, commands.CommandOnCooldown):
            return await ctx.send("This command is on cooldown, please wait " + str(round(exception.retry_after, 2)) + " more seconds!", delete_after=7)
        if isinstance(exception, commands.MissingRequiredArgument):
            await ctx.send("You are Missing required arguments!", delete_after=7)
            return await ctx.invoke(self.get_command("help show_command"), arg=ctx.command)
        if isinstance(exception, commands.BadArgument):
            return await ctx.send(f"This is an invalid argument.\n`{exception}`")
        if isinstance(exception, commands.CheckFailure):
            return await ctx.send("It seems like you do not have permissions to run this.")
        if isinstance(exception, commands.TooManyArguments):
            return await ctx.send("You Provided too many arguments.")
        
        if isinstance(exception, commands.CommandInvokeError):
            if isinstance(exception.original, discord.Forbidden):
                try:
                    return await ctx.author.send(f"I couldn't respond in {ctx.channel.mention}, because I have no permissions to send messages there.")
                except discord.Forbidden:
                    pass
            if isinstance(exception.original, exceptions.NeverPlayedSkyblockError):
                return await ctx.send("This player never played Hypixel Skyblock.", delete_after=7)
            if isinstance(exception.original, exceptions.BadNameError):
                return await ctx.send("This username does not exist in Minecraft.", delete_after=7)
            if isinstance(exception.original, exceptions.ExternalAPIError):
                logger.exception(exception)
                return await ctx.send("There has been an error while requesting the data from the API! Please try again after waiting some time..", delete_after=12)
            if isinstance(exception.original, exceptions.SkyblockError):
                logger.exception(exception)
                return await ctx.send("An unknown error occurred. Please report this to the devs.")
        traceback_lines = traceback.format_exception(type(exception), exception, exception.__traceback__)
        logger.exception("".join(traceback_lines))
        logger.exception(exception)

    async def on_slash_command_error(self, ctx, exception):
        
        if isinstance(exception, exceptions.NeverPlayedSkyblockError):
            return await ctx.send(content="This player never played Hypixel Skyblock.")
        if isinstance(exception, exceptions.BadNameError):
            return await ctx.send(content="This username does not exist in Minecraft.")
        if isinstance(exception, exceptions.ExternalAPIError):
            logger.exception(exception)
            return await ctx.send(content="There has been an error while requesting the data from the API! Please try again after waiting some time..", delete_after=12)
        if isinstance(exception, exceptions.SkyblockError):
            logger.exception(exception)
            return await ctx.send(content="An unknown error occurred. Please report this to the devs.")
        traceback_lines = traceback.format_exception(type(exception), exception, exception.__traceback__)
        logger.exception("".join(traceback_lines))
        logger.exception(exception)


if __name__ == "__main__":
    skybot = Skybot()
    try:
        skybot.run(skybot.config["token"])
    except discord.LoginFailure:
        logger.exception("Improper token in config.json")
