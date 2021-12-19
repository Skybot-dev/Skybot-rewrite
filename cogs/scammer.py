import discord
from utils.util import is_staff
from utils.skypy.skypy import fetch_uuid_uname, Player
from utils.skypy import skypy
from discord.ext import commands
from utils.embed import Embed
from bson.objectid import ObjectId
from datetime import datetime
import aiohttp
import asyncio

class scammer(commands.Cog, name="Scammer"):
    """Miscellaneous commands"""
    def __init__(self, bot):
        self.bot = bot
    
    @commands.group(invoke_without_command=True, name="scammer", description="commands for the scammer list.", aliases=["scam"], usage="[check/report]")
    async def scammer(self, ctx):
        await ctx.invoke(self.bot.get_command("help show_command"), arg="scammer")

    @scammer.command()
    @commands.check(is_staff)
    async def blacklist(self, ctx, id:int, *, reason:str=None):
        if not await self.bot.scammer_db["users"].find_one({"_id": id}):
            await self.bot.scammer_db["users"].insert_one({"_id": id, "blacklist": True, "reason": reason})
        else:
            await self.bot.scammer_db["users"].update_one({"_id": id}, {"$set": {"blacklist": True, "reason": reason}})
        await ctx.send(f"successfully blacklisted user `{id}` from submitting scammer reports for reason: `{reason}`")
        await self.bot.get_guild(self.bot.config["support_guild"]["ID"]).get_channel(self.bot.config["support_guild"]["log_channel"]).send(embed=discord.Embed(title="report blacklist", description=f"<@{id}> ({id}) blacklisted by {ctx.author.mention} for reason: {reason}", color=discord.Color.red()))
    @scammer.command()
    @commands.check(is_staff)
    async def whitelist(self, ctx, id:int, *, reason:str=None):
        if not await self.bot.scammer_db["users"].find_one({"_id": id}):
            await self.bot.scammer_db["users"].insert_one({"_id": id, "blacklist": False, "reason": reason})
        else:
            await self.bot.scammer_db["users"].update_one({"_id": id}, {"$set": {"blacklist": False, "reason": reason}})
        await ctx.send(f"successfully whitelisted user `{id}` for submitting scammer reports")
        await self.bot.get_guild(self.bot.config["support_guild"]["ID"]).get_channel(self.bot.config["support_guild"]["log_channel"]).send(embed=discord.Embed(title="report whitelist", description=f"<@{id}> ({id}) whitelisted by {ctx.author.mention} for reason: {reason}", color=discord.Color.green()))

    @scammer.command(name="report", description="Report a Minecraft user for scamming. Must have photographic evidence ready")
    async def report(self, ctx):
        embeds = []
        config = self.bot.config
        blacklisted = await self.bot.scammer_db["users"].find_one({"_id": ctx.author.id})
        if blacklisted:
            if blacklisted["blacklist"]:
                await ctx.author.send(f"You have been blacklisted from submitting reports for reason: `{blacklisted['reason']}`")
                return
        report_guild = self.bot.get_guild(config["support_guild"]["ID"])
        report_channel = report_guild.get_channel(config["support_guild"]["report_channel"])
        if not isinstance(ctx.channel, discord.channel.DMChannel):
            await ctx.send("report started in DM", delete_after=5)
            await ctx.message.delete()
        try:
            report_start = await ctx.author.send("You have started a report. Please respond with the IGN of the player whom you are reporting. To cancel, respond with `cancel`")
        except discord.Forbidden:
            await ctx.send("Please allow direct messages from server members then try again")
            return
        def check(m):
            return m.channel == report_start.channel and m.author == ctx.author
        try:
            player_msg = await self.bot.wait_for('message', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await ctx.author.send("Report timed out")
            return
        if player_msg.content.lower() == "cancel":
            await ctx.author.send("report cancelled")
            return
        else:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get("https://api.mojang.com/users/profiles/minecraft/"+player_msg.content) as resp:
                        player = await resp.json()
                uuid = player["id"]
            except aiohttp.ContentTypeError:
                await ctx.author.send("Couldn't find this user. They may have been nicked or deleted their account. Report cancelled")
                return
    
            x = await self.bot.scammer_db["scammer_list"].find_one({"_id": uuid})
            if x:
                return await ctx.author.send("This user is already on the scammer list!")
            await ctx.author.send("Please *briefly* describe what happened, not in detail (eg. `scammed AOTD` or `coopscammed 15 mil`)")
            try:
                quick_reason = await self.bot.wait_for('message', timeout=120.0, check=check)
            except asyncio.TimeoutError:
                await ctx.author.send("Report timed out")
                return
            report_embed = discord.Embed(title=f"{str(player_msg.content)}\n{ctx.author.id}", color=0x00ffff)
            report_embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
            report_embed.add_field(name="Reason:", value=str(quick_reason.content), inline=False)
            await ctx.author.send("Please now describe in detail what happened, and make sure to give the events in the correct order")
            try:
                descriptive_reason = await self.bot.wait_for('message', timeout=300.0, check=check)
            except asyncio.TimeoutError:
                await ctx.author.send("Report timed out")
                return
            report_embed.add_field(name="description:", value=str(descriptive_reason.content), inline=False)
            await ctx.author.send("Please send any photographic evidence that you have. This could be in-game screenshots or links to video proof. You can submit up to 5 pieces of proof and type `done` if you need fewer.")
            embeds.append(report_embed)

        for i in range(1, 6):
            try:
                proof = await self.bot.wait_for('message', timeout=300.0, check=check)
            except asyncio.TimeoutError:
                await ctx.author.send("Report timed out")
                return
            if proof.content.lower() == "done" or i == 5:
                if i == 1:
                    return await ctx.author.send("You must include evidence for a report. Report cancelled.")
                await ctx.author.send(
                    "Do you wish for the report to be anonymous? Anonymous reports will still have the same data saved, but your name will not be publically credited for reporting the scammer. Full credit is given to non-anonymous reports. `Y/N` (replying with anything but 'no' or 'n' will result in an anonymous report)")
                try:
                    anon = await self.bot.wait_for('message', timeout=300, check=check)
                except asyncio.TimeoutError:
                    await ctx.author.send("Report timed out")
                anonymous = anon.content.lower() not in ("n", "no")
                await ctx.author.send(
                    "We want to remind you that we cannot accept reports that don't have any proof. Some examples that count as proof: Minecraft- and/or Desktop Screenshots, video recordings (like Shadowplay, if you don't have an NVIDIA GPU use OBS for recordings) on YouTube, not a cropped screenshot that just shows someone left the party. These can be taken out of context very easily. Oh, and please stop filing unnecessary reports! **__WE WILL REJECT EVERY REPORT WITHOUT ANY PROOF! WE BLACKLIST USERS THAT MAKE FAKE REPORTS AND/OR TROLL REPORTS__**\n**TLDR;**\nProvide good proof when reporting someone via !scammer\nDon't file troll reports\n\nTo submit this request reply `send`")
                try:
                    confirmation = await self.bot.wait_for('message', timeout=30.0, check=check)
                    if confirmation.content.lower() == "send":
                        if not isinstance(ctx.channel, discord.channel.DMChannel):
                            report = await self.bot.scammer_db["reports"].insert_one(
                                {"name": str(player_msg.content), "uuid": uuid, "reason": quick_reason.content,
                                 "status": "pending", "reporter": str(ctx.author), "reporter_id": ctx.author.id,
                                 "guild": ctx.guild.id, "anonymous": anonymous})
                        else:
                            report = await self.bot.scammer_db["reports"].insert_one(
                                {"name": str(player_msg.content), "uuid": uuid, "reason": quick_reason.content,
                                 "status": "pending", "reporter": str(ctx.author), "reporter_id": ctx.author.id,
                                 "anonymous": anonymous})
                        report_id = str(report.inserted_id)
                        report_embed.description = f"ID: {report_id}\n"
                        for embed in embeds:
                            await report_channel.send(embed=embed)
                        await report_channel.send("-------------------------")
                        await ctx.author.send(
                            f"Your report has been sent. You will be told whether your report has been confirmed or not.")
                        return
                    else:
                        await ctx.author.send("Report cancelled")
                        return
                except asyncio.TimeoutError:
                    await ctx.author.send("Report timed out")
                    return
            embed = discord.Embed(title=f"Evidence {i}:", color=0x0000ff)
            if not proof.attachments:
                embed.description = proof.content
            else:
                evurl = proof.attachments[0].url
                embed.set_image(url=evurl)
            embeds.append(embed)

    @scammer.command(name="check", description="check a Minecraft username against our scammer list", usage="[username]")
    async def check(self, ctx, username:str):
        name, uuid = await fetch_uuid_uname(username)
        if not uuid:
            return await ctx.send("Could not find that username")
        scammer = await self.bot.scammer_db["scammer_list"].find_one({"_id": uuid})
        if not scammer:
            embed = Embed(title="Safe", description="This user is not in our database as a scammer. Proceed with caution", bot=self.bot, user=ctx.author)
            embed.color = 0x00FF00
            await embed.set_requested_by_footer()
            return await ctx.send(embed=embed)
        if scammer["report_id"] and not scammer["anonymous"]:
            report = await self.bot.scammer_db["reports"].find_one({"_id": scammer["report_id"]})
            if not report["anonymous"]:
                footer_text = f"reported by {report['reporter']}, confirmed by {scammer['mod']}"
            else:
                footer_text = f"reported anonymously, confirmed by {scammer['mod']}"
        else:
            footer_text = f"added by {scammer['mod']}"
        embed = discord.Embed(title="SCAMMER", description=scammer["reason"], color=0xff0000).set_footer(text=footer_text)
        await ctx.send(embed=embed)
    
    @scammer.command()
    @commands.check(is_staff)
    async def add(self, ctx, username, *, reason:str):
        name, uuid = await fetch_uuid_uname(username)
        if not uuid:
            return await ctx.send("Could not find that username")
        scammer = await self.bot.scammer_db["scammer_list"].find_one({"_id": uuid})
        if scammer:
            return await ctx.send("Already on the scammer list")
        player = await skypy.Player(self.bot.api_keys, uuid=uuid)
        discordname = player.discord
        await self.bot.scammer_db["scammer_list"].insert_one({"_id":uuid, "reason":reason, "mod":str(ctx.author), "report_id":None, "checks": 0, "anonymous": False})
        scammer_embed = discord.Embed(title=username, description=reason, color=discord.Embed.Empty).add_field(name="discord:", value=discordname, inline=False).set_footer(text=f"added by {str(ctx.author)}")
        await ctx.send(f"added {username} to the scammer list for reason: {reason}")
        guilds = self.bot.scammer_db["channels"].find({})
        async for guild in guilds:
            if "list_channel" not in guild:
                pass
            else:
                channel = guild["list_channel"]
                await self.bot.get_guild(guild["_id"]).get_channel(channel).send(embed=scammer_embed)
                await asyncio.sleep(0.5)

    @scammer.command()
    @commands.check(is_staff)
    async def confirmReport(self, ctx, reportid:str, user:str=None, *, reason:str=None):
        report = await self.bot.scammer_db["reports"].find_one({"_id": ObjectId(reportid)})
        report_id = ObjectId(reportid)
        if not report:
            await ctx.send("Invalid report ID")
            return
        else:
            if not user:
                user = report["name"]
                uuid = report["uuid"]
            else:
                name, uuid = await fetch_uuid_uname(user)
                if not uuid:
                    return await ctx.send("Could not find that user")
            player = await Player(self.bot.api_keys, uuid=uuid)
            existing_scammer = await self.bot.scammer_db["scammer_list"].find_one({"_id": uuid})
            if not existing_scammer:
                discord_username = player.discord
                await self.bot.scammer_db["reports"].update_one({"_id": report_id}, {"$set": {"status": "Confirmed", "mod": str(ctx.author)}})
                reporter_id = report["reporter_id"]
                report_reason = report["reason"]
                reportuser = self.bot.get_user(reporter_id)
                try:
                    await reportuser.send(f"You report [`ID: {reportid}`] has been processed and the scammer has been added to the list. Thanks for helping out the community!")
                except discord.Forbidden:
                    pass
                reporter = report["reporter"]
                if not reason:
                    scammer_embed = discord.Embed(title=user, description=report_reason, color=discord.Embed.Empty)
                    await self.bot.scammer_db["scammer_list"].insert_one({"_id":uuid, "reason":report_reason, "mod":str(ctx.author), "report_id":report_id, "checks": 0, "anonymous": report["anonymous"]})
                else:
                    scammer_embed = discord.Embed(title=user, description=reason, color=discord.Embed.Empty)
                    await self.bot.scammer_db["scammer_list"].insert_one({"_id":report["uuid"], "reason":reason, "mod":str(ctx.author), "report_id":report_id, "checks": 0, "anonymous": report["anonymous"]})
                scammer_embed.add_field(name="discord:", value=discord_username, inline=False)
                if report["anonymous"]:
                    pub_reporter = "anonymously"
                else:
                    pub_reporter = f"by {reporter}"
                scammer_embed.set_footer(text=f"reported {pub_reporter}, confirmed by {str(ctx.author)}")
                config = self.bot.config["support_guild"]
                logguild = self.bot.get_guild(config["ID"])
                logchannel = logguild.get_channel(config["log_channel"])
                logembed = discord.Embed(title="Report confirmed", color=0x0000ff)
                logembed.add_field(name=user, value=reason, inline=False)
                logembed.add_field(name=reportid, value=reporter)
                logembed.add_field(name="mod", value=str(ctx.author))
                await logchannel.send(embed=logembed)
                await ctx.message.delete()
                await ctx.send("Report confirmed", delete_after=3)
                guilds = self.bot.scammer_db["channels"].find({})
                async for guild in guilds:
                    if "list_channel" not in guild:
                        pass
                    else:
                        try:
                            channel = guild["list_channel"]
                            server = self.bot.get_guild(guild["_id"])
                            send_channel = server.get_channel(channel)
                            await send_channel.send(embed=scammer_embed)
                        except:
                            await self.bot.scammer_db["channels"].delete_one(guild)
            else:
                await ctx.send("This user is already on the scammer list")
                await ctx.message.delete()

    @scammer.command()
    @commands.check(is_staff)
    async def rejectReport(self, ctx, reportid:str, *, reason:str=None):
        report = await self.bot.scammer_db["reports"].find_one({"_id": ObjectId(reportid)})
        report_id = ObjectId(reportid)
        if not report:
            await ctx.send("Invalid report ID")
            return
        else:
            if report["status"] == "confirmed":
                await ctx.send("This report has already been confirmed")
                await ctx.message.delete()
                return
            elif report["status"] == "rejected":
                await ctx.send("This report has already been rejected")
                await ctx.message.delete()
                return
            else:
                reporter = self.bot.get_user(report['reporter_id'])
                try:
                    if not reason:
                        await reporter.send(f'Unfortunately, upon reviewal of your report `[ID: {reportid}]`, the moderators decided to reject it. You may resubmit with different content.')
                    else:
                        await reporter.send(f'Unfortunately, upon reviewal of your report `[ID: {reportid}]`, the moderators decided to reject it, for reason: "{reason}". You may resubmit with different content')
                except discord.Forbidden:
                    pass
            await self.bot.scammer_db["reports"].update_one({"_id": report_id}, {"$set": {"status": "rejected", "mod": str(ctx.author)}})
            config = self.bot.config["support_guild"]
            logguild = self.bot.get_guild(config["ID"])
            logchannel = logguild.get_channel(config["log_channel"])
            logembed = discord.Embed(title="report rejected", color=0x0000ff)
            logembed.add_field(name=report["name"], value=reason, inline=False)
            logembed.add_field(name=reportid, value=reporter)
            logembed.add_field(name="mod", value=str(ctx.author))
            await logchannel.send(embed=logembed)
            await ctx.message.delete()


    @scammer.command(name="CheckReport", description="Check the status of a player report by the ID given when the report was submitted", usage="[ID]")
    async def CheckReport(self, ctx, report_id:str):
        report = await self.bot.scammer_db["reports"].find_one({"_id": ObjectId(report_id)})
        if not report:
            await ctx.send("This report doesn't exist")
        else:
            embed = discord.Embed()
            embed.set_author(name=report_id)
            if report["status"] == "pending":
                embed.description = "**Status:** pending"
                embed.color = 0xffa500
            elif report["status"] == "confirmed":
                embed.description = "**Status:** confirmed"
                embed.set_footer(text=f"confirmed by {report['mod']}")
                embed.color = 0x00FF00
            elif report["status"] == "rejected":
                embed.description = "**Status:**"" rejected"
                embed.set_footer(text=f"rejected by {report['mod']}")
                embed.color = 0xff0000
            embed.add_field(name=f"**Reporter:** {report['reporter']}", value=f"__Against:__ {report['name']}\n__Reason:__ {report['reason']}")
            await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(scammer(bot))
    
