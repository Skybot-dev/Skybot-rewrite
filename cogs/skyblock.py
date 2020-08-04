import discord
import asyncio
import aiohttp
from discord.ext import commands, tasks
from utils.events import EventConverter
from utils.embed import Embed
from utils.skypy.skypy import TimedEvent
from datetime import timedelta
import time
from EZPaginator import Paginator


class Skyblock(commands.Cog):
    def __init__(self, bot):
        self.bot : commands.Bot = bot

        self.reminders = bot.users_db["reminders"]
        self.fetch_event_data.start()
        self.reminder_loop.start()


    def cog_unload(self):
        self.fetch_event_data.cancel()
        self.reminder_loop.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        pass

    def get_event(self, event):
        event_urls = [event.event_url for event in self.bot.events]
        if event.event_url in event_urls:
            event = self.bot.events[event_urls.index(event.event_url)]
        return event

    def get_times(self, event):
        if event.event_in.microseconds:
            event_in = str(event.event_in)[:-7]
        else:
            event_in = str(event.event_in)
        if event.event_on.microsecond:
            event_on = str(event.event_on)[:-7]
        else:
            event_on = str(event.event_on)
        return event_in, event_on

    async def update_event(self, ctx, msg, event : TimedEvent, seconds=10):
        event = self.get_event(event)
        while seconds > 0:
            event.update_without_api()
            embed = await self.get_event_embed(ctx, event)
            await msg.edit(embed=embed)
            seconds -= 1
            await asyncio.sleep(1)

    async def update_events(self, ctx, msg, events, seconds=10):
        while seconds > 0:
            new_events = []
            for event in events:
                event.update_without_api()
                new_events.append(event)
            events = new_events

            embed = await self.get_events_embed(ctx, events)
            await msg.edit(embed=embed)
            seconds -= 1
            await asyncio.sleep(1)


    async def get_event_embed(self, ctx, event):
        event = self.get_event(event)

        if not event.event_name and not event.event_in:
            try:
                await event.set_data()
            except:
                await asyncio.sleep(2)
                await event.set_data()

        event_in, event_on = self.get_times(event)

        embed = Embed(self.bot, ctx.author, title=event.event_name)
        await embed.set_requested_by_footer()
        embed.set_thumbnail(url=TimedEvent.icons[event.event_url])
        embed.add_field(name=f"{event.event_name} in:", value=event_in, inline=False)
        
        embed.add_field(name=f"{event.event_name} on (utc+0):", value=event_on, inline=False)
        return embed

    async def get_events_embed(self, ctx, events):
        embed = Embed(self.bot, ctx.author, title="All Timed Events", description="'on:' is utc+0")
        await embed.set_made_with_love_footer()
        for event in events:
            event_in, event_on = self.get_times(event)
            embed.add_field(name=event.event_name, value=f"In: {event_in}\nOn: {event_on}", inline=False)
        return embed


    @commands.command(name="event", description="Shows you when a Skyblock event is. Give no argument to get all times.", usage="([event])", aliases=["whenisnext", "win"])
    async def event(self, ctx, arg : EventConverter=None):
        if arg == None:
            events = []
            for event_url in TimedEvent.urls:
                events.append(self.get_event(TimedEvent(event_url)))
            embed = await self.get_events_embed(ctx, events)
            msg = await ctx.send(embed=embed)
            await self.update_events(ctx, msg, events)
            return

        embed = await self.get_event_embed(ctx, arg)
        msg = await ctx.send(embed=embed)
        await self.update_event(ctx, msg, arg)


    @commands.command(name="price", description="get the average price of a skyblock item", aliases=['p'], usage="[item]")
    async def price(self, ctx, *, name:str):
        await ctx.trigger_typing()
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.slothpixel.me/api/skyblock/items") as resp:
                item_data = await resp.json()
        names = {item_data[z]["name"].lower(): z for z in item_data}
        results = {}
        bazaar_results = {}
        matches = {z: y for (z, y) in names.items() if name in z}
        async with aiohttp.ClientSession() as session:
            for i, item in enumerate(matches):
                if i < 5:
                    async with session.get(f"https://api.slothpixel.me/api/skyblock/auctions/{matches[item]}{self.bot.slothpixel_key_string}") as resp:
                        if not (await resp.json())["average_price"]:
                            pass
                        else:
                            results[item] = await resp.json()
                    async with session.get(f"https://api.slothpixel.me/api/skyblock/bazaar/{matches[item]}") as resp:
                        r = await resp.json()
                        if "error" not in r:
                            bazaar_results[item] = r
        if len(matches) < 5:
            string = f"showing all {len(results) + len(bazaar_results)} results"
        else:
            string = f"showing {len(results) + len(bazaar_results)} of {len(matches)} results."
        embed = Embed(self.bot, ctx.author, title=f"Price search for {name}", description=f"{string}\nAuction Items: {len(results)}\nBazaar Items: {len(bazaar_results)}")
        embeds = [embed]
        if not (results or bazaar_results):
            return await ctx.send(embed=discord.Embed(title=":x: Item not found!", description="No price could be found for that search on the auction house or bazaar", color=discord.Color.red()))
        if len(results) + len(bazaar_results) == 1:
            if results:
                result = list(results.keys())[0]
                return await ctx.send(embed=Embed(self.bot, ctx.author, title=f"Price of {result} on auction", description=f"Average Price: {results[result]['average_price']}\nPrice range: {results[result]['min_price']} - {results[result]['max_price']}"))
            else:
                result = list(bazaar_results.keys())[0]
                flip = round((bazaar_results[result]['buy_summary'][0]['pricePerUnit'] / bazaar_results[result]['sell_summary'][0]['pricePerUnit']) * 100) - 100
                await ctx.send(embed=Embed(self.bot, ctx.author, title=f"Price of {result} at the Bazaar", description=f"Instant buy price: {round(bazaar_results[result]['buy_summary'][0]['pricePerUnit'])}\nInstant sell price: {round(bazaar_results[result]['sell_summary'][0]['pricePerUnit'])}\nProfit Margin: {flip}%"))
        for i, result in enumerate(results):
            if "texture" in item_data[names[result]]:
                url = f"https://sky.lea.moe/head/{item_data[names[result]]['texture']}"
            else:
                url = ''
            embeds.append(Embed(self.bot, ctx.author, title=f"Price of {result} on auction", description=f"Average Price: {results[result]['average_price']}\nPrice range: {results[result]['min_price']} - {results[result]['max_price']}").set_footer(text=f"page {i + 1} of {len(results) + len(bazaar_results)}").set_thumbnail(url=url))
        for i, result in enumerate(bazaar_results):
            if "texture" in item_data[names[result]]:
                url = f"https://sky.lea.moe/head/{item_data[names[result]]['texture']}"
            else:
                url = ''
                flip = round((bazaar_results[result]['buy_summary'][0]['pricePerUnit'] / bazaar_results[result]['sell_summary'][0]['pricePerUnit']) * 100) - 100
            embeds.append(Embed(self.bot, ctx.author, title=f"Price of {result} at the Bazaar", description=f"Instant buy price: {round(bazaar_results[result]['buy_summary'][0]['pricePerUnit'])}\nInstant sell price: {round(bazaar_results[result]['sell_summary'][0]['pricePerUnit'])}\nProfit Margin: {flip}%").set_footer(text=f"page {len(results) + i + 1} of {len(results) + len(bazaar_results)}").set_thumbnail(url=url))
        msg = await ctx.send(embed=embeds[0])
        pages = Paginator(self.bot, msg, embeds=embeds, timeout=60, use_more=True, only=ctx.author)
        await pages.start()

    @commands.group(name="reminder", description="Set a reminder for an event. The bot will message you 5 minutes before it.", usage="[set/remove/list]", invoke_without_command=True)
    async def reminder(self, ctx):
        await ctx.invoke(self.bot.get_command("help show_command"), arg="reminder")

    @reminder.command(name="set")
    async def set_reminder(self, ctx, event : EventConverter):
        event : TimedEvent = self.get_event(event)
        if not event.estimate:
            await event.set_data()
        docs = self.reminders.find({"id" : ctx.author.id})
        async for doc in docs:
            if doc["event"] == event.event_url:
                return await ctx.send("You already have an reminder set for this event.")
        await self.reminders.insert_one({"id" : ctx.author.id, "event" : event.event_url})
        event_in = str(event.event_in - timedelta(minutes=5))[:-7] if event.event_in.microseconds else event.event_in
        
        await ctx.send(f"Successfully created a reminder for {event.event_name}. You will be reminded 5 minutes before the event, so in: {event_in}")
            

    @reminder.command(name="remove")
    async def remove_reminder(self, ctx, event : EventConverter):
        event : TimedEvent = self.get_event(event)
        docs = self.reminders.find({"id" : ctx.author.id})
        async for doc in docs:
            if doc["event"] == event.event_url:
                await self.reminders.delete_one(doc)
                return await ctx.send(f"Removed the reminder for {event.event_name}.")
        await ctx.send(f"You have no reminder set for the {event.event_name}")

    @reminder.command(name="list")
    async def list_reminder(self, ctx, user: discord.abc.User=None):
        if not user:
            user = ctx.author

        embed = Embed(self.bot, ctx.author, title=f"{str(user)} reminders")
        await embed.set_made_with_love_footer()
        docs = self.reminders.find({"id" : user.id})
        async for doc in docs:
            event = self.get_event(TimedEvent(doc["event"]))
            event_in = str(event.event_in - timedelta(minutes=5))[:-7] if event.event_in.microseconds else event.event_in
            embed.add_field(name=f"Reminder for {event.event_name}", value=f"Will be reminded in {event_in}")
        if len(embed.fields) > 0:
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"{str(user)} has no reminders set.")


    @tasks.loop(seconds=10)
    async def reminder_loop(self):
        docs = self.reminders.find({})
        async for doc in docs:
            event = self.get_event(TimedEvent(doc["event"]))
            if not event.event_in:
                return
            event_in = event.event_in - timedelta(minutes=5) 
            if event_in.total_seconds() < time.time():
                try:
                    user = self.bot.get_user(doc["id"])
                    await user.send(f"This is a reminder for {event.event_name}. The event will be in 5 minutes, so get yourself ready. The reminder has been removed.")
                    await self.reminders.delete_one(doc)
                except:
                    pass


    @tasks.loop(minutes=1)
    async def fetch_event_data(self):
        if self.bot.events and len(self.bot.events) == len(TimedEvent.urls):
            for event in self.bot.events:
                await event.set_data()
        else:
            for event in TimedEvent.urls:
                event = TimedEvent(event)
                await event.set_data()
                if event not in self.bot.events:
                    self.bot.events.append(event)

    @fetch_event_data.before_loop
    async def before_fetch_event_data(self):
        await self.bot.wait_until_ready()

    @reminder_loop.before_loop
    async def before_reminder_loop(self):
        await self.bot.wait_until_ready()

def setup(bot):
    bot.add_cog(Skyblock(bot))