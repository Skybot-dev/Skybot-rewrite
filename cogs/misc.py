import discord
from utils import logging
from utils.util import is_staff
from inspect import Parameter
from discord.ext import commands, tasks
from utils.embed import Embed
from utils.util import get_config
from bson.objectid import ObjectId
from EZPaginator import Paginator
import time
from datetime import datetime
from trello import TrelloClient
#from trello.trelloclient import TrelloClient
#import trello
class Misc(commands.Cog, name="Misc"):
    """Miscellaneous commands"""
    def __init__(self, bot):
        self.bot = bot 
        self.my_board = self.bot.trello_board
        self.my_lists = self.my_board.list_lists()
        self.stats.start()
    
    @commands.command(name="invite", description="invite the bot to your server")
    async def invite(self, ctx):
        embed = Embed(title="Invite the bot to your server", bot=self.bot, user=ctx.author)
        embed.add_field(name="--------------------------------", value=f"The bot already is on {len(self.bot.guilds)} Guilds!\n[Click Here to invite the Bot]({get_config()['bot_invite']})")
        await embed.set_made_with_love_footer()
        await ctx.send(embed=embed)

        
    @commands.group(invoke_without_command=True, name="suggestion", description="Handles suggestions for the bot", aliases=["suggest"], usage="[submit/view]")
    async def suggestion(self, ctx, arg=None):
        await ctx.invoke(self.bot.get_command("help show_command"), arg="suggestion")
    
    @suggestion.command()
    async def submit(self, ctx, *, answer:str):
        embed = Embed(description=answer, bot=self.bot, user=ctx.author).set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
        supportConfig = get_config()["support_guild"]            
        suggestionChannel = self.bot.get_guild(supportConfig["ID"]).get_channel(supportConfig["suggest_channel"])
        msg = await suggestionChannel.send(embed=embed)
        await msg.add_reaction(u"\u2705")
        await msg.add_reaction(u"\u274E")
        await ctx.send(f"Suggestion logged. Join the support server with `{ctx.prefix}support` to see it.")
        await ctx.message.delete()
        card = self.my_lists[0].add_card(answer)
        suggestion_doc = await self.bot.admin_db["suggestions"].insert_one({"status": "submitted", "user": ctx.author.id, "content": answer, "message": msg.id, "datetime": time.time(), "card": card.id})
        await msg.edit(embed=msg.embeds[0].set_footer(text=f"ID: {str(suggestion_doc.inserted_id)}"))
    
    async def view_suggestion(self, ctx, id:str):
        suggestion_doc = await self.bot.admin_db["suggestions"].find_one({"_id": ObjectId(id)})
        if not suggestion_doc:
            return await ctx.send("Could not find a suggestion with that ID")
        supportConfig = get_config()["support_guild"]      
        msg = await (self.bot.get_guild(supportConfig["ID"]).get_channel(supportConfig["suggest_channel"])).fetch_message(suggestion_doc["message"])
        user = self.bot.get_user(suggestion_doc["user"])
        embed = discord.Embed(description=suggestion_doc["content"], color=discord.Color.gold()).set_author(name=user, icon_url=user.avatar_url)
        upvotes = [z.count for z in msg.reactions if str(z.emoji) == '✅']
        downvotes = [z.count for z in msg.reactions if str(z.emoji) == '❎']
        embed.add_field(name=f"Status: {suggestion_doc['status']}", value=f"{upvotes[0]} ✅\n \n{downvotes[0]} ❎", inline=False)
        embed.add_field(name="More", value=f"[trello page](https://trello.com/b/2yBAtx82/skybot-rewrite) | [GitHub repository](https://github.com/Skybot-dev/Skybot-rewrite)", inline=False)
        embed.timestamp = datetime.fromtimestamp(suggestion_doc["datetime"])
        return embed
    
    @suggestion.command()
    async def view(self, ctx, id:str):
        await ctx.send(embed=await self.view_suggestion(ctx, id))
    
    @suggestion.command(name="list")
    @commands.check(is_staff)
    async def slist(self, ctx):
        # try:
        embeds = []
        async for i in self.bot.admin_db["suggestions"].find({}):
            #embeds.append(await self.view_suggestion(ctx, str(i["_id"])))
            embeds.append(await self.view_suggestion(ctx, str(i["_id"])))
        msg = await ctx.send(embed=embeds[0])
        pages = Paginator(self.bot, msg, embeds=embeds, timeout=60, use_more=True, only=ctx.author)
        await pages.start()
        # except Exception as e:
        #     await ctx.send(e)
    
    @suggestion.command()
    @commands.check(is_staff)
    async def move(self, ctx, id:str, *, section:str):
        suggestion_doc = await self.bot.admin_db["suggestions"].find_one({"_id": ObjectId(id)})
        if not suggestion_doc:
            return await ctx.send("Could not find a suggestion with that ID")    
        card =  self.client.get_card(suggestion_doc["card"])
        List = [z for z in self.my_board.all_lists() if z.name.lower() == section.lower()]
        if not List:
            return await ctx.send("Could not find that category")
        card.change_list(List[0].id)
        await self.bot.admin_db["suggestions"].update_one({"_id": ObjectId(id)}, {"$set": {"status": section}})
        await ctx.send(f"Moved card `{card.name}` to List `{List[0].name}`")
    
    @suggestion.command()
    @commands.check(is_staff)
    async def clear(self, ctx):
        await self.bot.admin_db["suggestions"].delete_many({})
        await ctx.send("cleard all suggestions")
    
    @suggestion.command()
    @commands.check(is_staff)
    async def delete(self, ctx, id:str):
        suggestion_doc = await self.bot.admin_db["suggestions"].find_one_and_delete({"_id": ObjectId(id)})
        if not suggestion_doc:
            return await ctx.send("Could not find a suggestion with that ID")    
        card =  self.client.get_card(suggestion_doc["card"])
        card.delete()
        await ctx.send(f"successfully deleted suggestion `{id}`")
    
    
    @commands.group(invoke_without_command=True, name="changelog", description="bot changelogs", aliases=["update", "updates", "changelogs"])
    async def changelog(self, ctx):
        await ctx.invoke(self.bot.get_command("help show_command"), arg="changelog")
    
    async def changelog_embed(self, ctx, json_doc):
        embed = Embed(title=f"Changelogs for {json_doc['type']} `{json_doc['version']}`", description=json_doc["description"], bot=self.bot, user=ctx.author)
        embed.add_field(name="Bugs/plans", value=json_doc["bugs"], inline=False)
        embed.timestamp = datetime.fromtimestamp(json_doc["date"])
        await embed.set_made_with_love_footer()
        return embed
    
    @changelog.command(name="latest")
    async def latest(self, ctx):
        update = await self.bot.admin_db["changelog"].find_one({"latest": True})
        if not update:
            return await ctx.send("could not find any changelogs")
        await ctx.send(embed=(await self.changelog_embed(ctx, update)))
    
    @changelog.command()
    @commands.check(is_staff)
    async def add(self, ctx, Type, version, description, bugs):
        await self.bot.admin_db["changelog"].update_one({"latest": True}, {"$set": {"latest": False}})
        json_data = {"type": Type, "version": version, "bugs": bugs, "description": description, "date": time.time(), "latest": True}
        await self.bot.admin_db["changelog"].insert_one(json_data)
        await ctx.send(embed=(await self.changelog_embed(ctx, json_data)))
    
    @changelog.command()
    async def version(self, ctx, v:str):
        v = v.replace('v', '')
        update = await self.bot.admin_db["changelog"].find_one({"version": v})
        if not update:
            return await ctx.send("Could not find that version")
        await ctx.send(embed=(await self.changelog_embed(ctx, update)))
    
    @changelog.command()
    @commands.check(is_staff)
    async def clear(self, ctx):
        await self.bot.admin_db["changelog"].delete_many({})
        await ctx.send("deleted all changelogs")
    
    @changelog.command()
    async def list(self, ctx):
        Embeds = []
        Embeds.append(Embed(title="Bot changelogs", bot=self.bot, user=ctx.author))
        count = 0
        async for change in self.bot.admin_db["changelog"].find({}):
            if not count % 7 and count != 0:
                Embeds.append([Embed(title="Bot changelogs", bot=self.bot, user=ctx.author)])
            #print(Embeds[len(Embeds) - 1])
            Embeds[len(Embeds) - 1].add_field(name=f"{change['type']} {change['version']}", value=datetime.fromtimestamp(change['date']).strftime("%m/%d/%y"))
            count += 1
        print(count)
        if not count == 0:
            msg = await ctx.send(embed=Embeds[0])
            if count > 0:
                pages = Paginator(self.bot, msg, embeds=Embeds, timeout=60, use_more=True, only=ctx.author)
                await pages.start()
        else:
            return await ctx.send("Could not find any changelogs")
    
    
    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        config = get_config()
        logguild = self.bot.get_guild(config["support_guild"]["ID"])
        logchannel = logguild.get_channel(config["support_guild"]["log_channel"])
        #msg = await logchannel.fetch_message(config["support_guild"]["stats"]["message"])
        embed = discord.Embed(title="Guild add", description=f"NAME: {guild.name} \nID: {guild.id} \nMembers: {len(guild.members)}", color=0x00FF00)
        await logchannel.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        config = get_config()
        logguild = self.bot.get_guild(config["support_guild"]["ID"])
        logchannel = logguild.get_channel(config["support_guild"]["log_channel"])
        embed = discord.Embed(title="Guild remove", description=f"NAME: {guild.name} \nID: {guild.id} \nMembers: {len(guild.members)}", color=0xff0000)
        await logchannel.send(embed=embed)
    
    
    @tasks.loop(minutes=5)
    async def stats(self):
        config = get_config()["support_guild"]
        guild = self.bot.get_guild(config["ID"])
        config = config["stats"]
        channel = guild.get_channel(config["channel"])
        message = await channel.fetch_message(config["message"])
        
        guilds = self.bot.guilds
        
        members = 0
        for guild in guilds:
            members += len(guild.members)
                
        guild_members = []
        for guild in guilds:
            guild_members.append(len(guild.members))
        guilds_sorted = sorted(guild_members, reverse=True)[:10]
        guilds_sorted_str = [str(guild) for guild in guilds_sorted]
        final_list = "\n".join(guilds_sorted_str)
        embed = Embed(title="Statistics", bot=self.bot, user=None)
        embed.add_field(name="Servers:", value=len(guilds), inline=False)
        embed.add_field(name="Members:", value=members, inline=False)
        embed.add_field(name="Top 10 Member count:", value=final_list, inline=False)
        await embed.set_made_with_love_footer()
        await message.edit(embed=embed)
    
    @stats.before_loop
    async def before_stats(self):
        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(Misc(bot))