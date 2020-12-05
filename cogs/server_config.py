import discord
from discord.ext import commands, tasks
from utils.skypy import skypy
from utils.embed import Embed
from utils.util import get_user_guilds, is_verified
import copy

skypy.enable_advanced_mode()

rankColors = {'MVP++': 0xFFAA00,
                'MVP+': 0x00FFFF,
                'MVP': 0x00FFFF,
                'VIP+': 0x00FF00,
                'VIP': 0x00FF00}

async def update_all_guilds(bot, user, name, uuid):
    user_guilds = await get_user_guilds(bot, user)
    for guild in user_guilds:
        await update_guild(bot, guild, user, name, uuid)
        

async def update_guild(bot, guild, user, name, uuid):
    #banscammers
    try:
        doc = await bot.guilds_db["banscammers"].find_one({"_id": guild.id})
        if doc and doc["on"] and await bot.scammer_db["scammer_list"].find_one({"_id": uuid}) and await is_verified(bot, user):
            await guild.ban(user, reason="verified as scammer")
            return
    except (KeyError, discord.Forbidden):
        pass
        # if isinstance(e, discord.Forbidden):
        #     await ctx.send(f"{ctx.guild.owner.mention}:\n{ctx.author.mention} just successfully verifed as a known scammer, but I do not have permission to ban them.")  
        
        
    #verifynick
    try:
        doc = await bot.guilds_db["verifynick"].find_one({"_id" : guild.id})
        if doc and doc["on"] and await is_verified(bot, user):
            nick = await get_nick(bot, user, doc["format"])
            guild : discord.Guild = guild
            member = guild.get_member(user.id)
            
            await member.edit(nick=nick)
    except discord.Forbidden:
        pass
    
    #verifyrole
    try:
        doc = await bot.guilds_db["verifyrole"].find_one({"_id" : guild.id})
        if doc and doc["on"] and await is_verified(bot, user):
            role = guild.get_role(doc["role"])
            if not role: return
            
            member = guild.get_member(user.id)
            if role not in member.roles:
                await member.add_roles(role)
            
    except discord.Forbidden:
        pass
    
    #rankroles
    member = guild.get_member(user.id)
    roles = [role for role in guild.roles if role.name in rankColors.keys()]
    if not roles: return
    doc = await bot.guilds_db["rankroles"].find_one({"_id" : guild.id})
    if doc and doc["on"]:
        try:
            await remove_rankroles(bot, roles, member)
            await add_rankroles(bot, roles, member)
        except (discord.Forbidden, discord.HTTPException):
            pass
    

async def on_user_verified(ctx, bot: commands.Bot, name):
    name, uuid = await skypy.fetch_uuid_uname(name)

    #remove unverified links
    uuid_dbs = bot.users_db["connections"].find({"uuid" : uuid})
    async for uuid_db in uuid_dbs:
        if uuid_db["id"] != ctx.author.id:
            user = bot.get_user(uuid_db["id"])
            if user:
                try:
                    on_user_unverified(ctx, bot, user)
                    await user.send(f"You have been unlinked from `{name}`, because someone verified that they own this Minecraft account.")
                except (discord.Forbidden, discord.HTTPException):
                    pass
            await bot.users_db["connections"].delete_one(uuid_db)
    await update_all_guilds(bot, ctx.author, name, uuid)
            
            
    
        
async def on_user_unverified(ctx, bot: commands.Bot, user):
    pass
    
async def on_banscammers_active(ctx, bot):
    for member in await bot.cache_guild_chunk(ctx.guild):
        user_doc = await bot.users_db["connections"].find_one({"id" : member.id})
        if not await is_verified(bot, user_doc): continue
        uuid = user_doc["uuid"]
        scammer_doc = await bot.scammer_db["scammer_list"].find_one({"_id" : uuid})
        if not scammer_doc: continue
        try:
            await member.ban(reason="In scammer database")
        except discord.Forbidden:
            pass
   
        
async def get_nick(bot, member, format):
    user_doc = await bot.users_db["connections"].find_one({"id" : member.id})
    if not await is_verified(bot, user_doc): return None
    player = await skypy.Player(keys=bot.api_keys, uuid=user_doc["uuid"])
    
    nick = format.replace("{ign}", player.uname).replace("{rank}", player.rank.replace("_PLUS", "+").replace("_", " ").upper())
    return nick

async def update_nicks(ctx, bot):
    doc = await bot.guilds_db["verifynick"].find_one({"_id" : ctx.guild.id})
    if not doc: return
    for member in await bot.cache_guild_chunk(ctx.guild):
        try:
            nick = await get_nick(bot, member, doc["format"])
            if hasattr(member, "nick") and member.nick == nick:
                continue
            await member.edit(nick=nick)
        except (discord.Forbidden, discord.HTTPException):
            pass


async def on_verifynick_change(ctx, bot, state):
    if state == "on":
        await update_nicks(ctx, bot)
    elif state == "off":
        for member in await bot.cache_guild_chunk(ctx.guild):
            try:
                if await is_verified(bot, member):
                    await member.edit(nick=None)
            except (discord.Forbidden, discord.HTTPException):
                pass
        
async def add_roles(ctx, bot):
    doc = await bot.guilds_db["verifyrole"].find_one({"_id" : ctx.guild.id})
    if not doc: return
    role = ctx.guild.get_role(doc["role"])
    for member in await bot.cache_guild_chunk(ctx.guild):
        try:
            if not await is_verified(bot, member): continue
            if role in member.roles: continue
            await member.add_roles(role)
        except (discord.Forbidden, discord.HTTPException):
            pass
        
async def remove_roles(ctx, bot):
    doc = await bot.guilds_db["verifyrole"].find_one({"_id" : ctx.guild.id})
    if not doc: return
    role = ctx.guild.get_role(doc["role"])
    for member in await bot.cache_guild_chunk(ctx.guild):
        try:
            if role not in member.roles: continue
            await member.remove_roles(role)
        except (discord.Forbidden, discord.HTTPException):
            pass

async def on_verifyrole_change(ctx, bot, state):
    if state == "on":
        await add_roles(ctx, bot)
    elif state == "off":
        await remove_roles(ctx, bot)

async def on_role_changed(ctx, bot, before, after):
    if before == after:
        return
    if before is None:
        before = after
    for member in await bot.cache_guild_chunk(ctx.guild):
        if not await is_verified(bot, member): continue
        try:
            if before and before in member.roles:
                await member.remove_roles(before)
                await member.add_roles(after)
            else:
                await member.add_roles(after)
        except (discord.Forbidden, discord.HTTPException):
            pass


async def add_rankroles(bot, roles, member):
    
    try:
        doc = await bot.users_db["connections"].find_one({"id" : member.id})
        if not await is_verified(bot, doc): return
        if not doc: return
        
        player = await skypy.Player(keys=bot.api_keys, uuid=doc["uuid"])
        rank = player.rank.replace("_PLUS", "+").replace("_", "").upper()

        for role in roles:
            if role.name == rank:
                await member.add_roles(role)
            
    except (discord.Forbidden, discord.HTTPException):
        return
        
async def remove_rankroles(bot, roles, member):
    try:
        for role in roles:
            for user_role in member.roles:
                if role == user_role:
                    await member.remove_roles(role)
    except (discord.Forbidden, discord.HTTPException): 
        return

async def on_rankroles_changed(ctx, bot, state, roles):
    if state == "on":
        for member in await bot.cache_guild_chunk(ctx.guild):
            await remove_rankroles(bot, roles, member)
            await add_rankroles(bot, roles, member)
    elif state == "off":
        for member in await bot.cache_guild_chunk(ctx.guild):
            await remove_rankroles(bot, roles, member)
            


class ServerConfig(commands.Cog, name="ServerConfig"):
    def __init__(self, bot):
        self.bot : commands.AutoShardedBot = bot
        self.config = self.bot.guilds_db
        self.settings = ["prefixes", "banscammers", "verifynick", "verifyrole", "rankroles", "eventchannel"]
        self.eventchannel_msgs = set()
        self.eventchannel_loop.start()
        

    @commands.Cog.listener()
    async def on_ready(self):
        pass

    def cog_unload(self):
        self.eventchannel_loop.cancel()
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        doc = await self.bot.users_db["connections"].find_one({"id" : member.id})
        if doc:
            name, uuid = await skypy.fetch_uuid_uname(doc["uuid"])
            await update_guild(self.bot, member.guild, member, name, uuid)
    
    async def on_eventchannel_changed(self, ctx, bot, msg_before, channel_before):
        if msg_before is None: return
        channel = bot.get_channel(channel_before)
        try:
            msg = await channel.fetch_message(msg_before)
            self.eventchannel_msgs.discard(msg)
            await msg.delete()
        except (discord.Forbidden, discord.HTTPException, discord.NotFound) as e:
            pass
    
    async def get_info(self, ctx : commands.Context, guild, setting : str):
        doc = await self.config[setting].find_one({"_id": guild.id})
        if doc:
            info = ""
            for k, v in doc.items():
                if k == "_id": continue
                try:
                    role = ctx.guild.get_role(v)
                    if role:
                        v = role.mention
                except AttributeError:
                    pass

                info += f"{k.capitalize()}: {v}\n"
        else:
            info = "No information found."
        return info
    
    # @commands.command(name="serversetup", description="Set up your auto server management.", usage="")
    # @commands.guild_only()
    # @commands.has_permissions(administrator=True)
    # async def server_setup(self, ctx):
    #     await ctx.send("**Welcome to the server setup!**")
    #     msg = await ctx.send("Please tell me all the settings you want to activate. Example: scammerchannel, verifynick, verifyrole")
    
    
    @commands.command(name="serverinfo", description="Shows information about your server.", usage="")
    @commands.guild_only()
    async def serverinfo(self, ctx, guild : discord.Guild=None):
        if not guild:
            guild = ctx.guild
        if not guild:
            return await ctx.send("Guild not found")
        embed = Embed(self.bot, ctx.author, title=guild.name)
        await embed.set_requested_by_footer()
        for setting in self.settings:
            info = await self.get_info(ctx, guild, setting)
            embed.add_field(name=setting.capitalize(), value=info)
        
        await ctx.send(embed=embed)
        
    
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    @commands.group(name="prefix", description="Set the prefix that the bot uses to detect commands.", aliases=["pre"], usage="[set/reset/get]", invoke_without_command=True)
    async def prefix(self, ctx : commands.Context):
        await ctx.invoke(self.bot.get_command("help show_command"), arg="prefix")

    @commands.has_guild_permissions(administrator=True)
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @commands.guild_only()
    @prefix.command()
    async def set(self, ctx, arg):
        prefixes_coll = self.config["prefixes"]
        guild_db = await prefixes_coll.find_one({"_id" : ctx.guild.id})
        if guild_db:
            await prefixes_coll.update_one(guild_db, {"$set" : {"prefix" : arg}})
            return await ctx.send(f"Your server's prefix has been set to `{arg}`")
        await prefixes_coll.insert_one({"_id" : ctx.guild.id, "prefix" : arg})
        return await ctx.send(f"Your server's prefix has been set to `{arg}`")

    @commands.has_guild_permissions(administrator=True)
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @commands.guild_only()
    @prefix.command()
    async def reset(self, ctx):
        result = await self.config["prefixes"].delete_one({"_id" : ctx.guild.id})
        if result.deleted_count > 0:
            return await ctx.send("Prefix has been reset to `" + self.bot.config["default_prefix"] + "`")
        return await ctx.send("Nothing changed. You haven't changed the prefix yet, use the `set` argument.")
        
    @commands.has_guild_permissions(administrator=True)
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @commands.guild_only()
    @prefix.command()
    async def get(self, ctx):
        prefix = await self.config["prefixes"].find_one({"_id" : ctx.guild.id})
        if prefix:
            return await ctx.send("My prefix here is `" + prefix["prefix"] + "`")
        return await ctx.send("My prefix here is `" + self.bot.config["default_prefix"] + "`")

    @commands.cooldown(1, 60, commands.BucketType.guild)
    @commands.command(name="scammerChannel", description="Set a scammer list channel for your server. Leave [channel] blank to remove the channel", usage="[channel]")
    @commands.has_guild_permissions(administrator=True)
    @commands.guild_only()
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
        
        
    async def set_setting(self, ctx : commands.Context, setting : str, on=None):
        doc = await self.config[setting].find_one({"_id": ctx.guild.id})
        if doc:
            await self.config[setting].update_one(doc, {"$set": {"on": on}})
            return True
        return False
    
    async def get_info_embed(self, ctx : commands.Context, setting : str):
        doc = await self.config[setting].find_one({"_id": ctx.guild.id})
        if doc:
            description = ""
            for k, v in doc.items():
                if k == "_id": continue
                try:
                    role = ctx.guild.get_role(v)
                    if role:
                        v = role.mention
                except AttributeError:
                    pass
                try:
                    channel = ctx.guild.get_channel(v)
                    if channel:
                        v = channel.mention
                except AttributeError:
                    pass

                description += f"{k.capitalize()}: {v}\n"
                
            embed = Embed(self.bot, ctx.author, title=setting.capitalize() + " info", description=description)
        else:
            embed = Embed(self.bot, ctx.author, title=setting.capitalize() + " info", description="On: False")
        await embed.set_requested_by_footer()
        return embed
  
    @commands.group(name="banscammers", description="Automatically ban users who successfully verify as a known scammer", aliases=["banscammer"], usage="[on/off/info]", invoke_without_command=True)
    @commands.has_guild_permissions(administrator=True)
    @commands.guild_only()
    async def banscammers(self, ctx):
        await ctx.invoke(self.bot.get_command("help show_command"), arg="banscammers")
        
    @commands.has_guild_permissions(administrator=True)
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @commands.guild_only()
    @banscammers.command(name="on", description="Turns on that a user that verified as a known scammer gets automatically banned.", usage="")
    async def banscammers_on(self, ctx):
        if not await self.set_setting(ctx, "banscammers", True):
            await self.config["banscammers"].insert_one({"_id": ctx.guild.id, "on": True})
        await ctx.send("Setting `banscammers` is now `On` in this server.")
        await on_banscammers_active(ctx, self.bot)
        
    @commands.has_guild_permissions(administrator=True)
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @commands.guild_only()
    @banscammers.command(name="off", description="Turns off that a user that verified as a known scammer gets automatically banned.", usage="")
    async def banscammers_off(self, ctx):
        if not await self.set_setting(ctx, "banscammers", False):
            await self.config["banscammers"].insert_one({"_id": ctx.guild.id, "on": False})
        await ctx.send("Setting `banscammers` is now `Off` in this server.")
    
    @commands.guild_only()
    @banscammers.command(name="info", description="Shows you if you have banscammers on or off.", usage="")
    async def banscammers_info(self, ctx):
        embed = await self.get_info_embed(ctx, "banscammers")
        await ctx.send(embed=embed)
        
  
    @commands.group(name="verifynick", description="Verified members get their nickname changed to their mc username.", usage="[on/off/info/format]", invoke_without_command=True)
    @commands.has_guild_permissions(administrator=True)
    @commands.guild_only()
    async def verifynick(self, ctx):
        await ctx.invoke(self.bot.get_command("help show_command"), arg="verifynick")
        

    @commands.has_guild_permissions(administrator=True)
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @commands.guild_only()
    @verifynick.command(name="on", description="Turns on that a members nickname gets changed to their IGN after they verify.", usage="")
    async def verifynick_on(self, ctx):
        if not await self.set_setting(ctx, "verifynick", True):
            await self.config["verifynick"].insert_one({"_id": ctx.guild.id, "on": True, "format" : "{ign}"})
        await ctx.send("Setting `verifynick` is now `On` in this server.")
        await on_verifynick_change(ctx, self.bot, "on")
    

    @commands.has_guild_permissions(administrator=True)
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @commands.guild_only()
    @verifynick.command(name="off", description="Turns off that a members nickname gets changed to their IGN after they verify.", usage="")
    async def verifynick_off(self, ctx):
        if not await self.set_setting(ctx, "verifynick", False):
            await self.config["verifynick"].insert_one({"_id": ctx.guild.id, "on": False, "format" : "{ign}"})
        await ctx.send("Setting `verifynick` is now `Off` in this server.")
        await on_verifynick_change(ctx, self.bot, "off")
    
    @commands.has_guild_permissions(administrator=True)
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @commands.guild_only()
    @verifynick.command(name="format", description="Set the format for your nickname change.\n{rank} = hypixel rank ; {ign} = minecraft username.\nExamples: '{ign} | {rank}' or 'IGN: {ign}'.", usage="[format]")
    async def verifynick_format(self, ctx, *, format : str):
        if len(format.replace("{ign}", "").replace("{rank}", "")) > 8:
            return await ctx.send("You have too many custom characters set. Please don't add more than 8.")
        doc = await self.config["verifynick"].find_one({"_id" : ctx.guild.id})
        if not doc:
            await ctx.invoke(self.verifynick_on)
            doc = await self.config["verifynick"].find_one({"_id" : ctx.guild.id})
            
        await self.config["verifynick"].update_one(doc, {"$set" : {"format" : format}})
        await ctx.send(f"Changed format of `verifynick` to `{format}`")
        await on_verifynick_change(ctx, self.bot, "on")

    @commands.guild_only()
    @verifynick.command(name="info", description="Shows you if you have verifynick on or off and the set format.", usage="")
    async def verifynick_info(self, ctx):
        embed = await self.get_info_embed(ctx, "verifynick")
        await ctx.send(embed=embed)


    @commands.group(name="verifyrole", description="Verified members get a set role.", usage="[on/off/info/set]", invoke_without_command=True)
    @commands.has_guild_permissions(administrator=True)
    @commands.guild_only()
    async def verifyrole(self, ctx):
        await ctx.invoke(self.bot.get_command("help show_command"), arg="verifyrole")
        
    @commands.has_guild_permissions(administrator=True)
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @commands.guild_only()
    @verifyrole.command(name="on", description="Turns on that a verified member gets the set role.", usage="")
    async def verifyrole_on(self, ctx):
        if not await self.set_setting(ctx, "verifyrole", True):
            await ctx.send("Please set a role first using the `set` argument.")
            return await ctx.invoke(self.bot.get_command("help show_command"), arg=self.verifyrole_set_role)
        await ctx.send("Setting `verifyrole` is now `On` in this server.")
        await on_verifyrole_change(ctx, self.bot, "on")
    
    @commands.has_guild_permissions(administrator=True)
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @commands.guild_only()
    @verifyrole.command(name="off", description="Turns off that a verified member gets the set role.", usage="")
    async def verifyrole_off(self, ctx):
        await self.set_setting(ctx, "verifyrole", False)
        await ctx.send("Setting `verifyrole` is now `Off` in this server.")
        await on_verifyrole_change(ctx, self.bot, "off")
    
    @commands.has_guild_permissions(administrator=True)
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @commands.guild_only()
    @verifyrole.command(name="set", description="", usage="[@role]")
    async def verifyrole_set_role(self, ctx, *, role : discord.Role):
        doc = await self.config["verifyrole"].find_one({"_id" : ctx.guild.id})
        if doc:
            await self.config["verifyrole"].update_one(doc, {"$set" : {"role" : role.id}})
        else:
            await self.config["verifyrole"].insert_one({"_id" : ctx.guild.id, "on" : True, "role" : role.id})
            
        await ctx.send(f"Changed role of `verifyrole` to {role.mention}")
        await ctx.invoke(self.verifyrole_on)
        if doc and "role" in doc.keys():
            await on_role_changed(ctx, self.bot, ctx.guild.get_role(doc["role"]), role)
        else:
            await on_role_changed(ctx, self.bot, None, role)
        
    @commands.guild_only()
    @verifyrole.command(name="info", description="Shows you if you have verifyrole on or off and the set role.", usage="")
    async def verifyrole_info(self, ctx):
        embed = await self.get_info_embed(ctx, "verifyrole")
        await ctx.send(embed=embed)
    

    @commands.group(name="rankroles", description="Give members their Hypixel ingame rank as a role.", usage="[on/off/info/setup]", invoke_without_command=True)
    @commands.has_guild_permissions(administrator=True)
    @commands.guild_only()
    async def rankroles(self, ctx):
        await ctx.invoke(self.bot.get_command("help show_command"), arg="rankroles")
        
    @commands.has_guild_permissions(administrator=True)
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @commands.guild_only()
    @rankroles.command(name="on", description="Turns on that members get their Hypixel ingame rank as a role.", usage="")
    async def rankroles_on(self, ctx):
        roles = [role for role in ctx.guild.roles if role.name in rankColors.keys()]
        if not roles:
            return await ctx.send("Please setup the rankroles first using the `setup` argument.")
        if not await self.set_setting(ctx, "rankroles", True):
            await self.config["rankroles"].insert_one({"_id": ctx.guild.id, "on": True})
        await ctx.send("Setting `rankroles` is now `On` in this server.")
        await on_rankroles_changed(ctx, self.bot, "on", roles)
    
    @commands.has_guild_permissions(administrator=True)
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @commands.guild_only()
    @rankroles.command(name="off", description="Turns off that members get their Hypixel ingame rank as a role.", usage="")
    async def rankroles_off(self, ctx):
        roles = [role for role in ctx.guild.roles if role.name in rankColors.keys()]
        if not await self.set_setting(ctx, "rankroles", False):
            await self.config["rankroles"].insert_one({"_id": ctx.guild.id, "on": False})
        await ctx.send("Setting `rankroles` is now `Off` in this server.")
        await on_rankroles_changed(ctx, self.bot, "off", roles)
    
    @commands.has_guild_permissions(administrator=True)
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @commands.guild_only()
    @rankroles.command(name="setup", description="", usage="")
    async def rankroles_setup(self, ctx):
        for rank, color in rankColors.items():
            try:
                if rank.lower() in [role.name.lower() for role in ctx.guild.roles]: 
                    await ctx.send("Roles already exist!")
                    return await ctx.invoke(self.rankroles_on)
                role = await ctx.guild.create_role(name=rank, color=discord.Colour(color))
                
            except discord.Forbidden:
                pass
        if role:
            await ctx.send("Successfully created the rankroles!")
            return await ctx.invoke(self.rankroles_on)
        return await ctx.send("Failed to create rankroles, please make sure I have enough permissions.")
    
    @commands.guild_only()
    @rankroles.command(name="info", description="Shows you if you have rankroles on or off.", usage="")
    async def rankroles_info(self, ctx):
        embed = await self.get_info_embed(ctx, "rankroles")
        await ctx.send(embed=embed)

    
    
    @commands.group(name="eventchannel", description="Shows all Skyblock Events in one channel.", usage="[on/off/set/info]", invoke_without_command=True)
    @commands.has_guild_permissions(administrator=True)
    @commands.guild_only()
    async def eventchannel(self, ctx):
        await ctx.invoke(self.bot.get_command("help show_command"), arg="eventchannel")
        
    @commands.has_guild_permissions(administrator=True)
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @commands.guild_only()
    @eventchannel.command(name="on", description="Turns on that the bot shows all Skyblock Events in the selected channel.", usage="")
    async def eventchannel_on(self, ctx):
        if not await self.set_setting(ctx, "eventchannel", True):
            await ctx.send("Please set a channel first using the `set` argument.")
            return await ctx.invoke(self.bot.get_command("help show_command"), arg=self.eventchannel_set_channel)
        await ctx.send("Setting `eventchannel` is now `On` in this server.")
        #await on_eventchannel_changed(ctx, self.bot, "on")
    
    @commands.has_guild_permissions(administrator=True)
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @commands.guild_only()
    @eventchannel.command(name="off", description="Turns off that the bot shows all Skyblock Events in the selected channel.", usage="")
    async def eventchannel_off(self, ctx):
        await self.set_setting(ctx, "eventchannel", False)
        await ctx.send("Setting `eventchannel` is now `Off` in this server.")
        #await on_eventchannel_changed(ctx, self.bot, "off")
    
    @commands.has_guild_permissions(administrator=True)
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @commands.guild_only()
    @eventchannel.command(name="set", description="Select the channel to show all Events in.", usage="")
    async def eventchannel_set_channel(self, ctx, channel : discord.TextChannel):
        doc = await self.config["eventchannel"].find_one({"_id" : ctx.guild.id})
        try:
            msg = await channel.send(embed=await self.get_event_embed())
        except discord.Forbidden:
            return await ctx.send("The bot needs permissions to send a message into that channel!")
        self.eventchannel_msgs.add(msg)
        if doc:
            await self.config["eventchannel"].update_one(doc, {"$set" : {"channel" : channel.id, "message" : msg.id}})
            await self.on_eventchannel_changed(ctx, self.bot, doc["message"], doc["channel"])
        else:
            await self.config["eventchannel"].insert_one({"_id" : ctx.guild.id, "on" : True, "channel" : channel.id, "message" : msg.id})
            await self.on_eventchannel_changed(ctx, self.bot, None, None)
        
          
        await ctx.send(f"Changed channel of `eventchannel` to {channel.mention}")
        await ctx.invoke(self.eventchannel_on)
        

    
    @commands.guild_only()
    @eventchannel.command(name="info", description="Shows you if you have eventchannel on or off and the selected channel.", usage="")
    async def eventchannel_info(self, ctx):
        embed = await self.get_info_embed(ctx, "eventchannel")
        await ctx.send(embed=embed)
    
    async def get_event_embed(self):
        embed = Embed(self.bot, None, title="Timed Events")
        await embed.set_patron_footer()
        
        for event in self.bot.events:
            event.update_without_api()
            embed.add_field(name=event.event_name, value=f"Event in:\n**{str(event.event_in)[:-7]}**")
        return embed
    

    @tasks.loop(seconds=8)
    async def eventchannel_loop(self):
        docs = self.config["eventchannel"].find({})
        embed = await self.get_event_embed()

        async for doc in docs:
            if not doc["on"] and doc["message"] in [msg.id for msg in self.eventchannel_msgs]:
                msgs = copy.copy(self.eventchannel_msgs)
                for msg in msgs:
                    if msg.id == doc["message"]:
                        self.eventchannel_msgs.remove(msg)
            if doc["on"] and doc["message"] not in [msg.id for msg in self.eventchannel_msgs]:
                channel = self.bot.get_channel(doc["channel"])
                if not channel: continue
                try:
                    msg = await channel.fetch_message(doc["message"])
                except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                    continue
                self.eventchannel_msgs.add(msg)
        msgs = copy.copy(self.eventchannel_msgs)
        for msg in msgs:
            try:
                await msg.edit(content=None, embed=embed)
            except discord.NotFound:
                self.eventchannel_msgs.remove(msg)

    @eventchannel_loop.before_loop
    async def before_eventchannel_loop(self):
        await self.bot.wait_until_ready()
        
    
    
    
def setup(bot):
    bot.add_cog(ServerConfig(bot))