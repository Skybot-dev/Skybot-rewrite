from bot import Skybot
import discord
from discord.ext import commands
from discord_slash import SlashContext, SlashCommandOptionType, cog_ext, manage_commands
from cogs.player import Player
from utils.embed import Embed
from utils.expander import Expander
from utils.util import get_uuid_profileid, has_is_staff, is_staff
from utils.skypy import skypy, exceptions
from EZPaginator import Paginator


class SlashCmds(commands.Cog):
    def __init__(self, bot):
        self.bot : Skybot = bot
        
    async def shortcut_error(self, ctx):
        embed = await Embed(self.bot, ctx.author, title="Error", description="You can only use this shortcut if you link a username to your Discord account.").set_requested_by_footer()
        await ctx.send(embeds=[embed])
        # await ctx.invoke(self.bot.get_command("help show_command"), arg=ctx.command.name)
    
    async def profile_not_found_error(self, ctx : commands.Context, player):
        embed = await Embed(self.bot, ctx.author, title="Error", description="Couldn't find the provided profile in your Skyblock account. Your profiles: " + ", ".join(player.profiles.keys())).set_requested_by_footer()
        await ctx.send(embeds=[embed])
        
    async def get_uname(self, ctx, uname):
        if not uname:
            uname, profile = await get_uuid_profileid(self.bot, ctx.author)
            if uname is None:
                return await self.shortcut_error(ctx)
        return uname
        
    async def make_player(self, ctx, uname, profile):
        if uname and uname.lower() == "me":
            uname, rest = await get_uuid_profileid(self.bot, ctx.author)

        if not uname and not profile:
            uname, profile = await get_uuid_profileid(self.bot, ctx.author)
            if uname is None:
                await self.shortcut_error(ctx)
                return None
        
        uname, uuid = await skypy.fetch_uuid_uname(uname)
        
        if not uname: 
            raise exceptions.BadNameError(uname)
        player = await skypy.Player(keys=self.bot.api_keys, uname=uname)

        if not profile:
            await player.set_profile_automatically()
        elif profile and profile.capitalize() in player.profiles.keys():
            await player.set_profile(player.profiles[profile.capitalize()])
        else:
            try:
                await player.set_profile(profile)
            except exceptions.DataError:
                await self.profile_not_found_error(ctx, player)
                return None
        return player
        
    def format_name(self, name):
        return name + "'s" if name[-1] != "s" else name
    
    profiles = [
                manage_commands.create_choice("apple", "Apple"),
                manage_commands.create_choice("banana", "Banana"),
                manage_commands.create_choice("blueberry", "Blueberry"),
                manage_commands.create_choice("coconut", "Coconut"),
                manage_commands.create_choice("cucumber", "Cucumber"),
                manage_commands.create_choice("grapes", "Grapes"),
                manage_commands.create_choice("kiwi", "Kiwi"),
                manage_commands.create_choice("lemon", "Lemon"),
                manage_commands.create_choice("lime", "Lime"),
                manage_commands.create_choice("mango", "Mango")
                ]
    
    
    @cog_ext.cog_slash(name="dungeons", description="Shows you Catacomb stats.", options=[manage_commands.create_option("username", "Minecraft username/Discord user if linked.", SlashCommandOptionType.STRING, False), 
                                                                                                                                      manage_commands.create_option("profile", "Profile name (There are more profile names then suggested!)", SlashCommandOptionType.STRING, False, choices=profiles)])
    async def dungeons(self, ctx : SlashContext, username=None, profile=None):
        await ctx.defer()
        player = await self.make_player(ctx=ctx, uname=username, profile=profile)
        if not player: return
        embed = await Player.get_dungeon_embed(self, ctx=ctx, player=player)
        await ctx.send(embeds=[embed])
        
    @cog_ext.cog_slash(name="networth", description="View a more in-depth breakdown of your estimated networth.", options=[manage_commands.create_option("username", "Minecraft username/Discord user if linked.", SlashCommandOptionType.STRING, False), 
                                                                                                                                      manage_commands.create_option("profile", "Profile name (There are more profile names then suggested!)", SlashCommandOptionType.STRING, False, choices=profiles)])
    async def networth(self, ctx : SlashContext, username=None, profile=None):
        await ctx.defer()
        player = await self.make_player(ctx=ctx, uname=username, profile=profile)
        if not player: return
        success = await player.skylea_stats(self.bot.stats_api)
        if success:
            embeds = await Player.get_networth_embeds(self, ctx=ctx, player=player)
            msg = await ctx.send(embed=embeds[0])
            await Expander(self.bot, msg, embeds=embeds, timeout=120, only=ctx.author).start()
        else:
            await ctx.send(content=f"An error occurred, perhaps this user has not played skyblock.")    
        
    @cog_ext.cog_slash(name="skills", description="Shows you Skyblock skill levels and xp.", options=[manage_commands.create_option("username", "Minecraft username/Discord user if linked.", SlashCommandOptionType.STRING, False), 
                                                                                                                                      manage_commands.create_option("profile", "Profile name (There are more profile names then suggested!)", SlashCommandOptionType.STRING, False, choices=profiles)])
    async def skills(self, ctx : SlashContext, username=None, profile=None):
        await ctx.defer()
        player = await self.make_player(ctx=ctx, uname=username, profile=profile)
        if not player: return
        embed = await Player.get_skills_embed(self, ctx=ctx, player=player)
        await ctx.send(embeds=[embed])
        
    @cog_ext.cog_slash(name="stats", description="Shows you Skyblock profile stats like health, strength and more.", options=[manage_commands.create_option("username", "Minecraft username/Discord user if linked.", SlashCommandOptionType.STRING, False), 
                                                                                                                                      manage_commands.create_option("profile", "Profile name (There are more profile names then suggested!)", SlashCommandOptionType.STRING, False, choices=profiles)])
    async def stats(self, ctx : SlashContext, username=None, profile=None):
        await ctx.defer()
        player = await self.make_player(ctx=ctx, uname=username, profile=profile)
        if not player: return
        success = await player.skylea_stats(self.bot.stats_api)
        if success:
            embed = await Player.get_stats_embed(self, ctx=ctx, player=player)
            await ctx.send(embeds=[embed])
        else:
            await ctx.send(content=f"An error occurred, perhaps this user has not played skyblock.")
        
    @cog_ext.cog_slash(name="slayer", description="Shows you Slayer stats.", options=[manage_commands.create_option("username", "Minecraft username/Discord user if linked.", SlashCommandOptionType.STRING, False), 
                                                                                                                                      manage_commands.create_option("profile", "Profile name (There are more profile names then suggested!)", SlashCommandOptionType.STRING, False, choices=profiles)])
    async def slayer(self, ctx : SlashContext, username=None, profile=None):
        await ctx.defer()
        player = await self.make_player(ctx=ctx, uname=username, profile=profile)
        if not player: return
        embed = await Player.get_slayer_embed(self, ctx=ctx, player=player)
        await ctx.send(embeds=[embed])
        
    @cog_ext.cog_slash(name="profiles", description="Shows you all your available profiles on Skyblock.", options=[manage_commands.create_option("username", "Minecraft username/Discord user if linked.", SlashCommandOptionType.STRING, False)])
    async def profiles(self, ctx : SlashContext, username=None):
        await ctx.defer()
        uname = await self.get_uname(ctx, username)
        if not uname: return
        embed : Embed = await Player.get_profiles_embed(self, ctx=ctx, uname=uname)
        await ctx.send(embeds=[embed])
        
    # @cog_ext.cog_slash(name="auctions", description="Shows you Skyblock auctions and information about them.", options=[manage_commands.create_option("username", "Minecraft username/Discord user if linked.", SlashCommandOptionType.STRING, False), 
    #                                                                                                                                   manage_commands.create_option("profile", "Profile name (There are more profile names then suggested!)", SlashCommandOptionType.STRING, False, choices=profiles)])
    # async def auctions(self, ctx : SlashContext, username=None, profile=None):
    #     player = await self.make_player(ctx=ctx, uname=username, profile=profile)
    #     if not player: return
    #     embeds = await Player.get_auctions_embeds(self, ctx=ctx, player=player)
    #     if not embeds:
    #             return await ctx.send(content=f"{player.uname} has no auctions running.")
    #     msg = await ctx.send(embeds=[embeds[0]])
    #     if len(embeds) > 1:
    #         pages = Paginator(self.bot, msg, embeds=embeds, only=ctx.author, use_more=True)
    #         await pages.start()

        
    async def get_help_embed(self, ctx):
        staff = is_staff(ctx)
        list_embed = Embed(title="Categories", bot=self.bot, user=ctx.author)
        # list_embed.set_author(name=f"Use {ctx.prefix}help [Command/Category]")
        await list_embed.set_requested_by_footer()

        for name, cog in self.bot.cogs.items():
            if name == "Admin" or name == "Help": continue
            if not cog.get_commands(): continue
            
            commands = []
            for command in cog.get_commands():
                if has_is_staff(command) and not staff: continue
                commands.append(f"`{command.name}`")
            list_embed.add_field(name=name, value=", ".join(commands), inline=False)

        list_embed.add_field(name="Links", value="[Contribute](https://discord.gg/zqRsduD2JN) | [Vote](https://top.gg/bot/630106665387032576/vote) | [Invite the Bot to your server](https://discordapp.com/oauth2/authorize?client_id=630106665387032576&scope=bot&permissions=8) | [Support Server](https://discord.gg/7fPv2uY2Tf) | [Todos](https://trello.com/b/2yBAtx82/skybot-rewrite) | [GitHub repo](https://github.com/Skybot-dev/Skybot-rewrite)", inline=False)
        return list_embed
        
    @cog_ext.cog_slash(name="help", description="List commands and command info.", guild_ids=[636937988248436736])
    async def help(self, ctx : SlashContext):
        await ctx.defer()
        embed = await self.get_help_embed(ctx)
        await ctx.send(embeds=[embed])

    

def setup(bot):
    bot.add_cog(SlashCmds(bot))
