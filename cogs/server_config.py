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
        self.config = self.bot.guilds_db["settings"]

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
        
        
    @commands.group(name="verifynick", description="Verified members get their nickname changed to their mc username.", usage="[on/off/info/format]", invoke_without_subcommand=True)
    @commands.has_guild_permissions(administrator=True)
    async def verifynick(self, ctx):
        await ctx.invoke(self.bot.get_command("help show_command"), arg="verifynick")
        
    @verifynick.command(name="on", description="Turns on that a members nickname gets changed to their IGN after they verify.", usage="")
    async def on(self, ctx):
        pass
    
    @verifynick.command(name="off", description="Turns off that a members nickname gets changed to their IGN after they verify.", usage="")
    async def off(self, ctx):
        pass
    
    @verifynick.command(name="format", description="Set the format for your nickname change.\n{user} = discord username ; {ign} = minecraft username.\nExamples: '{ign} | {user}' or 'IGN: {ign}'.", usage="[format]")
    async def format_nick(self, ctx, *, format):
        pass
    
    @verifynick.command(name="info", description="Shows you if you have verifynick on or off and the set format.", usage="")
    async def info(self, ctx):
        pass
    
    
    @commands.group(name="verifyrole", description="Verified members get a set role.", usage="[on/off/info/set]", invoke_without_subcommand=True)
    @commands.has_guild_permissions(administrator=True)
    async def verifyrole(self, ctx):
        await ctx.invoke(self.bot.get_command("help show_command"), arg="verifyrole")
        
    @verifyrole.command(name="on", description="Turns on that a verified member gets the set role.", usage="([@role])")
    async def on(self, ctx):
        pass
    
    @verifyrole.command(name="off", description="Turns off that a verified member gets the set role.", usage="")
    async def off(self, ctx):
        pass
    
    @verifyrole.command(name="set", description="", usage="[@role]")
    async def set_role(self, ctx, *, role : discord.Role):
        pass
    
    @verifyrole.command(name="info", description="Shows you if you have verifyrole on or off and the set role.", usage="")
    async def info(self, ctx):
        pass
    
    
    @commands.group(name="rankroles", description="Give members their Hypixel ingame rank as a role.", usage="[on/off/info/setup]", invoke_without_subcommand=True)
    @commands.has_guild_permissions(administrator=True)
    async def rankroles(self, ctx):
        await ctx.invoke(self.bot.get_command("help show_command"), arg="rankroles")
        
    @verifyrole.command(name="on", description="Turns on that members get their Hypixel ingame rank as a role.", usage="")
    async def on(self, ctx):
        pass
    
    @verifyrole.command(name="off", description="Turns off that members get their Hypixel ingame rank as a role.", usage="")
    async def off(self, ctx):
        pass
    
    @verifyrole.command(name="setup", description="", usage="")
    async def setup_rankroles(self, ctx):
        pass
    
    @verifyrole.command(name="info", description="Shows you if you have rankroles on or off.", usage="")
    async def info(self, ctx):
        pass

def setup(bot):
    bot.add_cog(ServerConfig(bot))