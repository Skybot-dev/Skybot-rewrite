
import discord
from discord.ext import commands
from utils.util import get_uuid_profileid
from utils.skypy import skypy, exceptions
from utils.skypy.constants import skill_icons
from utils.embed import Embed
from EZPaginator import Paginator
from datetime import datetime
import aiohttp
import json

class Items(commands.Cog):
    def __init__(self, bot):
        self.bot : commands.Bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        pass

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
                flip = round(bazaar_results[result]['buy_summary'][0]['pricePerUnit'] / bazaar_results[result]['sell_summary'][0]['pricePerUnit']) / 100
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
            flip = round(bazaar_results[result]['buy_summary'][0]['pricePerUnit'] / bazaar_results[result]['sell_summary'][0]['pricePerUnit'] * 100, 1) - 100
            embeds.append(Embed(self.bot, ctx.author, title=f"Price of {result} at the Bazaar", description=f"Instant buy price: {round(bazaar_results[result]['buy_summary'][0]['pricePerUnit'])}\nInstant sell price: {round(bazaar_results[result]['sell_summary'][0]['pricePerUnit'])}\nProfit Margin: {flip}%").set_footer(text=f"page {len(results) + i + 1} of {len(results) + len(bazaar_results)}").set_thumbnail(url=url))
        msg = await ctx.send(embed=embeds[0])
        pages = Paginator(self.bot, msg, embeds=embeds, timeout=60, use_more=True, only=ctx.author)
        await pages.start()

def setup(bot):
    bot.add_cog(Items(bot))