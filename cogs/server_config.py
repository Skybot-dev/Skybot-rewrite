import discord
from utils import logging
from inspect import Parameter
from discord.ext import commands
from utils.util import get_config


async def on_user_verified(ctx):
    print("User verified")
    #TODO make this do stuff lel


class ServerConfig(commands.Cog):
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


def setup(bot):
    bot.add_cog(ServerConfig(bot))