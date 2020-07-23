import discord
import asyncio
from discord.ext import commands
from utils.skypy import skypy, exceptions
from utils.embed import Embed
from cogs.server_config import on_user_verified
from EZPaginator import Paginator


class Connections(commands.Cog):
    def __init__(self, bot):
        self.bot : commands.AutoShardedBot = bot
        self.connections = self.bot.users_db["connections"]
        skypy.enable_advanced_mode()

    @commands.Cog.listener()
    async def on_ready(self):
        pass

    @commands.command(name="verify",
                      description="Verify that you own the Minecraft account and that you play on Hypixel.",
                      usage="([username])")
    async def verify_direct(self, ctx, username=None):
        await ctx.invoke(self.verify, username=username)
    
    @commands.command(name="usersetup",
                      description="Set up your account details and preferences",)
    async def setupdirect(self, ctx):
        await ctx.invoke(self.setup)

    @commands.group(name="account",
                    description="Set up personal settings.",
                    aliases=["acc"],
                    usage="[setup/link/unlink/profile/verify]",
                    invoke_without_command=True)
    async def account(self, ctx):
        await ctx.invoke(self.bot.get_command("help show_command"), arg="account")

    @account.command()
    async def setup(self, ctx):
        if isinstance(ctx.channel, discord.abc.GuildChannel):
            msg = await ctx.send("Started Setup in DMs!")
        try:
            dm_msg = await ctx.author.send("**Welcome to the new friendship between you and me!**")
        except discord.Forbidden:
            return await msg.edit(content="Couldn't DM you. Make you sure you didn't block me.", delete_after=3)

        try:
            find_one = await self.connections.find_one({"id" : ctx.author.id})
            if not find_one:
                await ctx.author.send("Please tell me your Minecraft username.")
                user_msg = await self.bot.wait_for("message", check=lambda m : m.author == ctx.author and m.channel == dm_msg.channel, timeout=60)
                dm_ctx = await self.bot.get_context(user_msg)
                await dm_ctx.invoke(self.link, username=user_msg.content)
            else:
                await ctx.author.send("Oh nice you already have a username linked, we will skip this part then!")
            find_one = await self.connections.find_one({"id" : ctx.author.id})
            player = await skypy.Player(keys=self.bot.api_keys, uuid=find_one["uuid"])
            if not "profile_id" in find_one.keys():
                if len(player.profiles.keys()) < 2:
                    dm_ctx = await self.bot.get_context(dm_msg)
                    dm_ctx.author = ctx.author
                    if not await dm_ctx.invoke(self.profile, profile=list(player.profiles.keys())[0]):
                        await ctx.author.send("You only had one profile so that was set as your default.")
                else:
                    await ctx.author.send("Great! You now have your username linked to your Discord account and you will be able to use commands without providing your username each time.\nNext you should set a default Profile too. Please tell me the name of the profile. Your Profiles: " + ", ".join(player.profiles.keys()))
                    user_msg = await self.bot.wait_for("message", check=lambda m : m.author == ctx.author and m.channel == dm_msg.channel, timeout=60)
                    dm_ctx = await self.bot.get_context(user_msg)
                    await dm_ctx.invoke(self.profile, profile=user_msg.content)
                    find_one = await self.connections.find_one({"id" : ctx.author.id})
                    if not "profile_id" in find_one.keys():
                        return await dm_ctx.send("Couldn't set your default profile! Please retry.")
            else:
                await ctx.author.send("Well, you already have a default profile set too! Let's skip this step too then.")
            find_one = await self.connections.find_one({"id" : ctx.author.id})
            if not find_one["verified"]:
                dm_msg = await ctx.author.send("Wow look at your skill writing properties about yourself. Next up you should verify that you actually own this Minecraft account. Please link Hypixel with your discord account and confirm through reacting to this message.")
                dm_msg = await ctx.author.send("https://giant.gfycat.com/DentalTemptingLeonberger.mp4")
                await dm_msg.add_reaction("✅")
                user_msg = await self.bot.wait_for("reaction_add", check=lambda reaction, user: user == ctx.author and str(reaction.emoji) == "✅", timeout=60)
                dm_ctx = await self.bot.get_context(dm_msg)
                ctx.channel = dm_ctx.channel
                await ctx.invoke(self.verify, username=player.uname)
                find_one = await self.connections.find_one({"id" : ctx.author.id})
                if not find_one["verified"]:
                    return await dm_ctx.send("Couldn't verify! That was the last step in this setup, so just use the verify command next try.")
            else:
                dm_msg = await ctx.author.send("You are already verified.")
                dm_ctx = await self.bot.get_context(dm_msg)
            await ctx.author.send("Here's a summary of your information:")
            await dm_ctx.invoke(self.info, user=ctx.author)
        except asyncio.TimeoutError:
            return await ctx.author.send("Session closed! You took too long to respond. Please start a new session.")

    @account.command(name="link", description="Link your username to you Discord account.", usage="[username]")
    async def link(self, ctx, username):    
        mc_user = await skypy.Player(self.bot.api_keys, uname=username)
        user_db = await self.connections.find_one({"id" : ctx.author.id})
        uuid_dbs = self.connections.find({"uuid" : mc_user.uuid})

        # if uuid_db and uuid_db["id"] != ctx.author.id:
        #     return await ctx.send("This username is already linked to another Discord Account.")
        async for uuid_db in uuid_dbs:
            if uuid_db and uuid_db["id"] == ctx.author.id:
                return await ctx.send("You already have this Minecraft account linked to your Discord account.")

        if user_db:
            before = await skypy.fetch_uuid_uname(user_db["uuid"])
            await self.connections.update_one(user_db, {"$set" : {"uuid" : mc_user.uuid, "verified" : False}})
            return await ctx.send(f"Successfully Updated your link from `{before[0]}` to `{mc_user.uname}`.")
        
        await self.connections.insert_one({"id" : ctx.author.id, "uuid" : mc_user.uuid, "verified" : False})
        return await ctx.send(f"Successfully linked `{mc_user.uname}` to your Discord account.")


    @account.command(name="unlink", description="Unlink your username from you Discord account.", usage="")
    async def unlink(self, ctx):
        user_db = await self.connections.find_one({"id" : ctx.author.id})

        if user_db:
            await self.connections.delete_one(user_db)
            mc_user = await skypy.fetch_uuid_uname(user_db['uuid'])
            return await ctx.send(f"Successfully unlinked `{mc_user[0]}` from your Discord account.")
        return await ctx.send("You don't have a account linked.")

    @account.command(name="verify", description="Verify that you own the Minecraft account and that you play on Hypixel.", usage="([username])")
    async def verify(self, ctx : commands.Context, username=None):
        user_db = await self.connections.find_one({"id" : ctx.author.id})
        if username is None and user_db is None:
            return await ctx.send(f"You have no account linked. Use `{ctx.prefix}acc verify [username]`")

        if user_db:
            player = await skypy.Player(keys=self.bot.api_keys, uuid=user_db["uuid"])
            if hasattr(ctx.author, "nick")  and ctx.author.nick:
                name = ctx.author.nick + "#" + ctx.author.discriminator
            else:
                name = str(ctx.author)
            if player.discord == name:
                if user_db["verified"] == False:
                    await self.connections.update_one(user_db, {"$set" : {"verified" : True}})
                    await on_user_verified(ctx, self.bot, username)
                    return await ctx.send("Successfully verified!")
                await on_user_verified(ctx, self.bot, username)
                return await ctx.send("You are already verified.")
            return await ctx.send(f"Your link between Hypixel and Discord is incorrect.\nHypixel: {player.discord}\nDiscord: {name}")
        
        msg = await ctx.invoke(self.link, username=username)
        await ctx.reinvoke()

    @account.command(name="profile", description="Set your default profile.", usage="[profile]")
    async def profile(self, ctx, profile):
        user_db = user_db = await self.connections.find_one({"id" : ctx.author.id})
        if not user_db:
            return await ctx.send(f"Please link your username to your discord account first.\n`{ctx.prefix}account link [username]`")

        player :skypy.Player = await skypy.Player(keys=self.bot.api_keys, uuid=user_db["uuid"])
        profiles = player.profiles
        if not profile.capitalize() in profiles.keys():
            return await ctx.send("You have no profile with that name.\nYour Profiles: " + ", ".join(profiles.keys()))
        
        await self.connections.update_one(user_db, {"$set" : {"profile_id" : profiles[profile.capitalize()]}})
        await ctx.send(f"Set your default profile to `{profile.capitalize()}`")
        return False

    async def get_info_embed(self, ctx, user, user_db, linked=True):
        player : skypy.Player = await skypy.Player(keys=self.bot.api_keys, uuid=user_db["uuid"])

        if "profile_id" in user_db.keys() and user_db["profile_id"] in player.profiles.values():
            for k, v in player.profiles.items():
                if v == user_db["profile_id"]:
                    profile = k
                    break
        else:
            profile = None

        embed = Embed(title=str(user) + " <=> " + player.uname, bot=self.bot, user=ctx.author)
        await embed.set_requested_by_footer()
        scammer = bool(await self.bot.scammer_db["scammers"].find_one({"_id": user_db["uuid"]}))
        embed.add_field(name="General Information", value=f"Discord username: `{str(user)}`\nMc username: `{player.uname}`\nUUID: `{player.uuid}`\nLinked to Bot: `{linked}`", inline=False)
        embed.add_field(name="Advanced Information", value=f"Profile(s): `{', '.join(player.profiles.keys())}`\n\
        Default Profile: `{profile}`\nScammer: `{scammer}`\nVerified: `{user_db['verified']}`", inline=False)
        return embed

    @account.command(name="info", description="Shows you all the information about your account.", usage="([username])", )
    async def info(self, ctx, user=None):
        try:
            converter = commands.UserConverter()
            user = await converter.convert(ctx, user)
        except:
            pass
        if user is None:
            user = ctx.author

        if isinstance(user, discord.abc.User):
            user_db = await self.connections.find_one({"id" : user.id})

            if user_db:
                embed = await self.get_info_embed(ctx, user, user_db) 
                return await ctx.send(embed=embed)
            if user != ctx.author:
                return await ctx.send("This user is not linked to the bot.")
            return await ctx.send("You are not linked to the bot.")
        
        if isinstance(user, str):
            uname, uuid = await skypy.fetch_uuid_uname(user)
            dc_users = self.connections.find({"uuid" : uuid})
            dc_users = await dc_users.to_list(length=1000)

            if len(dc_users) > 0:
                embeds = []
                for dc_user in dc_users:
                    embed = await self.get_info_embed(ctx, self.bot.get_user(dc_user["id"]), dc_user)
                    embeds.append(embed)

                msg = await ctx.send(embed=embeds[0])
                if len(embeds) > 1:
                    paginator = Paginator(self.bot, msg, embeds=embeds, timeout=60, use_more=True, only=ctx.author)
                    await paginator.start()
                return
            return await ctx.send(embed=await self.get_info_embed(ctx, None, {"uuid" : uuid, "verified" : False}, linked=False))

        
        raise commands.BadArgument(message="Discord User or Minecraft username")


def setup(bot):
    bot.add_cog(Connections(bot))