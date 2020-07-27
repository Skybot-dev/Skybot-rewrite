import discord
from discord.ext import commands
from utils.util import get_uuid_profileid
from utils.skypy import skypy, exceptions
from utils.skypy.constants import skill_icons
from utils.embed import Embed



class Player(commands.Cog):
    def __init__(self, bot):
        self.bot : commands.Bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        pass
    
    
    async def shortcut_error(self, ctx):
        embed = await Embed(self.bot, ctx.author, title="Error", description="You can only use this shortcut if you link a username to your Discord account.").set_requested_by_footer()
        await ctx.send(embed=embed)
        await ctx.invoke(self.bot.get_command("help show_command"), arg=self.skills)
        
        
        
    async def make_player(self, ctx, uname, profile):
        if uname and uname.lower() == "me":
            uname, rest = await get_uuid_profileid(self.bot, ctx.author)
            
        if not uname and not profile:
            uname, profile = await get_uuid_profileid(self.bot, ctx.author)
            if uname is None:
                return await self.shortcut_error(ctx)
            
        player = await skypy.Player(keys=self.bot.api_keys, uname=uname)
        
        if not profile:
            await player.set_profile_automatically()
        elif profile and profile.capitalize() in player.profiles.keys():
            await player.set_profile(player.profiles[profile.capitalize()])
        else:
            try:
                await player.set_profile(profile)
            except exceptions.DataError:
                return await Embed(self.bot, ctx.author, title="Error", description="Couldn't find the provided profile in your Skyblock account.").set_requested_by_footer()
        return player

    async def get_skills_embed(self, ctx, player):
        player.load_skills_slayers(False)
        
        if not player.enabled_api["skills"]:
            return await Embed(self.bot, ctx.author, title="Error", description="Your skills API is disabled. Please enable it and try again.").set_requested_by_footer()

        name = player.uname + "'s" if player.uname[-1] is not "s" else player.uname

        embed = Embed(self.bot, ctx.author, title=f"{name} Skills on {player.profile_name}", description=f"Average skill level: {player.skill_average}")
        await embed.set_requested_by_footer()
        for name, level in player.skills.items():
            embed.add_field(name=f"{skill_icons[name]} {name.capitalize()} Level", value=f"**LEVEL {level}**\n{player.skill_xp[name]:,}XP total\n{player.skills_needed_xp[name]:,}XP to next level")
        return embed
    
    async def get_slayer_embed(self, ctx, player : skypy.Player):
        player.load_skills_slayers(False)
        print(player.slayers)
        print(player.slayer_xp)
        print(player.total_slayer_xp)
        print(player.slayers_needed)
        if not player.enabled_api["skills"]:
            return await Embed(self.bot, ctx.author, title="Error", description="Your skills API is disabled. Please enable it and try again.").set_requested_by_footer()

    
    
    async def get_profiles_embed(self, ctx, uname):
        player = await skypy.Player(keys=self.bot.api_keys, uname=uname)
        
        name = player.uname + "'s" if player.uname[-1] is not "s" else player.uname
        
        embed = Embed(self.bot, ctx.author, title=f"{name} profiles")
        await embed.set_requested_by_footer()
        
        for number, profile in enumerate(player.profiles.items()):
            await player.set_profile(profile[1])
            uuids = list(player._api_data["members"].keys())
            unames = []
            for uuid in uuids:
                name, uuid = await skypy.fetch_uuid_uname(uuid)
                unames.append(name)
            embed.add_field(name=f"{number + 1}. {profile[0]}", value="- " + "\n- ".join(unames), inline=False)
            player._profile_set = False
        return embed
    
    
    @commands.command(name="skills", description="Shows you Skyblock skill levels and xp.", usage="[username] ([profile])", aliases=["skill", "sk"])
    async def skills(self, ctx, uname=None, profile=None): 
        player = await self.make_player(ctx, uname, profile)
        async with ctx.typing():
            embed = await self.get_skills_embed(ctx, player)
            await ctx.send(embed=embed)
            
    
    @commands.command(name="slayer", description="Shows you Slayer stats.", usage="[username] ([profile])", aliases = ["slay"])
    async def slayer(self, ctx, uname=None, profile=None):
        player = await self.make_player(ctx, uname, profile)
        async with ctx.typing():
            embed = await self.get_slayer_embed(ctx, player)
            await ctx.send(embed=embed)
         
            
    @commands.command(name="Profiles", description="Shows you all your available profiles on Skyblock.", usage="[Minecraft Username]")
    async def profiles(self, ctx, uname=None):
        if not uname:
            uname, profile = await get_uuid_profileid(self.bot, ctx.author)
            if uname is None:
                return await self.shortcut_error(ctx)
        async with ctx.typing():
            embed = await self.get_profiles_embed(ctx, uname)
            await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Player(bot))