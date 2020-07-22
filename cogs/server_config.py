import discord
from utils import logging
from inspect import Parameter
from discord.ext import commands


async def on_user_verified(ctx):
    print("User verified")
    #TODO make this do stuff lel


class ServerConfig(commands.Cog, name="ServerConfig"):
    def __init__(self, bot):
        self.bot : commands.AutoShardedBot = bot
        


    @commands.Cog.listener()
    async def on_ready(self):
        pass

    def cog_unload(self):
        pass

    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    @commands.cooldown(3, 5, commands.BucketType.user)
    @commands.group(name="prefix", description="Set the prefix that triggers the bot.", aliases=["pre"], usage="[set/reset/get]")
    async def prefix(self, ctx : commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.invoke(self.bot.get_command("help show_command"), arg="prefix")

    @prefix.command()
    async def set(self, ctx, arg):
        prefixes_coll = self.bot.guilds_db["prefixes"]
        guild_db = await prefixes_coll.find_one({"guild_id" : ctx.guild.id})
        if guild_db:
            await prefixes_coll.update_one(guild_db, {"$set" : {"prefix" : arg}})
            return await ctx.send(f"Your server's prefix has been set to `{arg}`")
        await prefixes_coll.insert_one({"guild_id" : ctx.guild.id, "prefix" : arg})
        return await ctx.send(f"Your server's prefix has been set to `{arg}`")

    @prefix.command()
    async def reset(self, ctx):
        result = await self.bot.guilds_db["prefixes"].delete_one({"guild_id" : ctx.guild.id})
        if result.deleted_count > 0:
            return await ctx.send("Prefix has been reset to `" + self.bot.config["default_prefix"] + "`")
        return await ctx.send("Nothing changed. You haven't changed the prefix yet, use the `set` argument.")
        
    @prefix.command()
    async def get(self, ctx):
        prefix = await self.bot.guilds_db["prefixes"].find_one({"guild_id" : ctx.guild.id})
        if prefix:
            return await ctx.send("My prefix here is `" + prefix["prefix"] + "`")
        return await ctx.send("My prefix here is `" + self.bot.config["default_prefix"] + "`")


    @commands.command(name="scammerChannel", description="Set a scammer list channel for your server. Leave [channel] blank to remove the channel", usage="[channel]")
    @commands.has_guild_permissions(administrator=True)
    async def scammerChannel(self, ctx, channel:discord.TextChannel=None):
        guild = await self.bot.scammer_db["channels"].find_one({"_id": ctx.guild.id})
        if channel:
            if guild:
                await self.bot.scammer_db["channels"].update_one({guild, {"$set": {"list_channel": channel.id}}})
            else:
                await self.bot.scammer_db["channels"].insert_one({"_id": ctx.guild.id, "list_channel": channel.id})
            return await ctx.send(f"Set the scammer list channel to {channel.mention}")
        else:
            if guild:
                await self.bot.scammer_db["channels"].delete_one(guild)
            return await ctx.send("Removed the scammer list channel")

def setup(bot):
    bot.add_cog(ServerConfig(bot))