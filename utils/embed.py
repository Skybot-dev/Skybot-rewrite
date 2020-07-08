import discord
from datetime import datetime
from discord.ext import commands


class Embed(discord.Embed):
    def __init__(self, bot : commands.AutoShardedBot, user : discord.User, **kwargs):
        self.bot = bot
        self.user = user
        self.timestamp = datetime.utcnow()
        super().__init__(color=discord.Color.gold(), **kwargs)
        
    async def set_requested_by_footer(self):
        return super().set_footer(text="Requested by " + str(self.user), icon_url=self.user.avatar_url)

    async def set_made_with_love_footer(self):
        return super().set_footer(text="Made with 💖", icon_url=self.bot.user.avatar_url)
