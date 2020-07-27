import os
from loguru import logger
import traceback
import discord
from discord.ext import commands

from database.init import init_client
from utils.util import get_config, trelloinit
from utils.skypy import exceptions
from utils import logging
import random
from itertools import cycle


class Skybot(commands.AutoShardedBot):
    def __init__(self):
        super().__init__(self.get_prefix, case_insensitive=True)
        logging.init_logging()

        self.db_client = init_client(self.loop)
        if self.db_client: logger.info("Connected to Database.")

        self.trello_board = trelloinit()
        self.config = get_config()
        self.admin_db = self.db_client["management"]
        self.users_db = self.db_client["users"]
        self.guilds_db = self.db_client["guilds"]
        self.scammer_db = self.db_client["scammer"]
        self.status_list = cycle(self.config["status_list"])
        self.remove_command("help")
        
        self.api_keys = self.config["api_keys"]

        if not self.api_keys:
            logger.warning("PLEASE SET AT LEAST ON API KEY, ELSE THE BOT WON'T WORK.")

        self.load_cogs()
        

    async def get_prefix(self, message):
        if not message.guild:
            return commands.when_mentioned_or(self.config["default_prefix"])(self, message)

        prefix = await self.guilds_db["prefixes"].find_one({"guild_id" : message.guild.id})
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
        


    async def on_ready(self):
        logger.info("Skybot ready.")






    async def on_message(self, message):

        if not self.is_ready() : return

        await self.process_commands(message)

    async def on_message_edit(self, before, after):
        await self.wait_until_ready()

        await self.process_commands(after)
        
    async def on_command_completion(self, ctx):
        if not ctx.command_failed:
            adminstats = self.admin_db["adminstats"]

            result = await adminstats.update_one({"name" : ctx.command.name}, {"$inc" : {"uses" : 1}})
            if result.modified_count == 0:
                await adminstats.insert_one({"name" : ctx.command.name, "uses" : 0})


    async def on_command_error(self, ctx : commands.Context, exception):
        if isinstance(exception, commands.CommandNotFound):
            return await ctx.send("`Command not found`", delete_after=3)
        if isinstance(exception, commands.NoPrivateMessage):
            return await ctx.send("This command can't be used in a private chat.", delete_after=7)
        if isinstance(exception, commands.CommandOnCooldown):
            return await ctx.send("This command is on cooldown, please wait " + str(round(exception.retry_after, 2)) + " more seconds!", delete_after=7)
        if isinstance(exception, commands.MissingRequiredArgument):
            await ctx.send("You are Missing required arguments!", delete_after=7)
            return await ctx.invoke(self.get_command("help show_command"), arg=ctx.command)
        if isinstance(exception, commands.BadArgument):
            return await ctx.send(f"This is an invalid argument. The argument needs to be: `{exception}`")
        if isinstance(exception, commands.CheckFailure):
            return await ctx.send("It seems like you are missing requirements to run this command.")

        if isinstance(exception, commands.CommandInvokeError):
            print(exception)
            if isinstance(exception.original, exceptions.NeverPlayedSkyblockError):
                return await ctx.send("This player never played Hypixel Skyblock.", delete_after=7)
            if isinstance(exception.original, exceptions.BadNameError):
                return await ctx.send("This username does not exist in Minecraft.", delete_after=7)

        traceback_lines = traceback.format_exception(type(exception), exception, exception.__traceback__)
        logger.exception("".join(traceback_lines))
        logger.exception(exception)

        

if __name__ == "__main__":
    skybot = Skybot()
    try:
        skybot.run(skybot.config["token"])
    except discord.LoginFailure:
        logger.exception("Improper token in config.json")
