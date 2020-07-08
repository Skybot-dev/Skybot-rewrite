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
        self.statuspage = logging.init_statuspage()
        logger.info("Connecting to Database...")
        self.db_client = init_client(self.loop)
        if self.db_client: logger.info("Connected to Database.")
        self.admin_db = self.db_client["admin"]
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
        await logging.set_status(self.statuspage, logging.Componenets.CORE, logging.Status.OPERATIONAL)
        logger.info("Skybot ready.")

    
    async def on_command_error(self, ctx, exception):
        if isinstance(exception, commands.NoPrivateMessage):
            return await ctx.send("This command can't be used in a private chat.")
        if isinstance(exception, commands.CommandOnCooldown):
            return await ctx.send("this command is on cooldown, please wait " + str(exception.retry_after) + " more seconds!")
        
            
        #await logging.create_incident(self.statuspage, str(exception), logging.Componenets.CORE)  
        

if __name__ == "__main__":
    skybot = Skybot()
    try:
        skybot.run(get_config()["token"])
    except discord.LoginFailure:
        logger.exception("Improper token in config.json")
