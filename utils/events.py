from discord.ext import commands
from utils.skypy.skypy import TimedEvent

class EventConverter(commands.Converter):
    async def convert(self, ctx : commands.Context, argument):
        for url in TimedEvent.urls:
            if argument.lower() in url:
                return TimedEvent(url)
        
        raise commands.BadArgument("Event not found. Events: " + ", ".join([event.event_name for event in ctx.bot.events]))