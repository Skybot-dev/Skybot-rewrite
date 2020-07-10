import os
from loguru import logger

import discord
from discord.ext import commands

from database.init import init_client
from utils.util import get_config
from utils import logging




class Skybot(commands.AutoShardedBot):
    def __init__(self):
        super().__init__(self.get_prefix, case_insensitive=True)
        logging.init_logging()

        if get_config()["statuspage"]["enabled"]:
            self.statuspage = logging.init_statuspage()
        else:
            self.statuspage = None
        self.db_client = init_client(self.loop)
        if self.db_client: logger.info("Connected to Database.")

        self.admin_db = self.db_client["management"]
        self.users_db = self.db_client["users"]
        self.guilds_db = self.db_client["guilds"]

        self.remove_command("help")

        self.load_cogs()        
        

    async def get_prefix(self, message):
        if not message.guild:
            return commands.when_mentioned_or(get_config()["default_prefix"])(self, message)

        prefix = await self.guilds_db["prefixes"].find_one({"guild_id" : message.guild.id})
        if prefix is not None:
            return commands.when_mentioned_or(prefix["prefix"])(self, message)
        else:
            return commands.when_mentioned_or(get_config()["default_prefix"])(self, message)
     
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
        if self.statuspage:
            await logging.set_status(self.statuspage, logging.Componenets.CORE, logging.Status.OPERATIONAL)
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
            return await ctx.send("This command can't be used in a private chat.")
        if isinstance(exception, commands.CommandOnCooldown):
            return await ctx.send("This command is on cooldown, please wait " + str(round(exception.retry_after, 2)) + " more seconds!")
        logger.exception(exception)
        if self.statuspage:
            cog_name = ctx.cog.qualified_name
            components = dict(map(reversed, logging.Componenets.DICT.items()))
            await logging.create_incident(self.statuspage, str(exception), [components[cog_name.upper()]])  
        

if __name__ == "__main__":
    skybot = Skybot()
    try:
        skybot.run(get_config()["token"])
    except discord.LoginFailure:
        logger.exception("Improper token in config.json")
