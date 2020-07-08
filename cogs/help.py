import discord
from utils.embed import Embed
from discord.ext import commands
from utils import logging

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot : commands.AutoShardedBot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        pass
    
    def cog_unload(self):
        pass

    @commands.cooldown(3, 5, commands.BucketType.user)
    @commands.group(name="help", description="List commands and command info.", aliases=["cmds"], usage="[Category/Command]")
    async def help(self, ctx : commands.Context, arg=None):
        if arg is None or arg.lower() == "list":
            await ctx.invoke(self.list)
            return

        arg = arg.lower()

        cog_names = [cog.lower() for cog in self.bot.cogs if cog != "Admin" and cog != "Help"]
        if arg in cog_names:
            await ctx.invoke(self.show_cog, arg=arg)
            return

        command_names = [command.name for command in self.bot.commands if str(command.cog) != "Admin" and str(commands.Cog) != "Help"]
        if arg in command_names:
            await ctx.invoke(self.show_command, arg=arg)
            return
        
        raise commands.BadArgument(message="Command or Cog")
        

    @help.command()
    async def list(self, ctx):
        list_embed = Embed(title="Categories", bot=self.bot, user=ctx.author)
        list_embed.set_author(name=f"Use {ctx.prefix}help [Command/Category]")
        await list_embed.set_requested_by_footer()

        for name in self.bot.cogs:
            if name != "Admin" and name != "Help" : cog : commands.Cog = self.bot.get_cog(name) 
            else: continue
            list_embed.add_field(name=name, value=", ".join(["`" + command.name + "`" for command in cog.get_commands()]), inline=True)
        list_embed.add_field(name="Links", value="[Apply as Dev](https://discord.gg/SQebkz9) | [Vote](https://top.gg/bot/630106665387032576/vote) | [Invite the Bot to your server](https://discordapp.com/oauth2/authorize?client_id=630106665387032576&scope=bot&permissions=8) | [Support Server](https://discord.gg/hmmfXud) | [Todos](https://trello.com/b/2yBAtx82/skybot-rewrite)", inline=False)
        await ctx.send(embed=list_embed)

    @help.command()
    async def show_cog(self, ctx, arg):
        cog : commands.Cog = self.bot.get_cog(arg.capitalize())
        cog_embed = Embed(title=arg.capitalize() + " Help", bot=self.bot, user=ctx.author)
        await cog_embed.set_requested_by_footer()

        for command in cog.get_commands():
            if command.description == "":
                description = "No Description."
            else:
                description = command.description
            cog_embed.add_field(name=command.name, value=description, inline=True)
            
        await ctx.send(embed=cog_embed)
    
    
    @help.command()
    async def show_command(self, ctx, arg):
        command : commands.Command = self.bot.get_command(arg)
        
        command_embed = Embed(title=ctx.prefix + command.name.capitalize(), bot=self.bot, user=ctx.author)
        await command_embed.set_requested_by_footer()

        if command.description == "": description = "No Description."
        else: description = command.description
        if command.usage == None: usage = "No Usage."
        else: usage = ctx.prefix + command.name + " " + command.usage
        if command.aliases == []: aliases = "No Aliases."
        else: aliases = str(command.aliases).replace("[", " ").replace("]", " ").replace("'", " ").replace(",", "\n")

        command_embed.add_field(name="Description", value=description, inline=False)
        command_embed.add_field(name="Usage", value=usage, inline=False)
        command_embed.add_field(name="Aliases", value=aliases, inline=False)

        await ctx.send(embed=command_embed)



    @commands.command(name="support", description="Support Server link", aliases=["sup"], usage="")
    async def support(self, ctx):
        await ctx.send("Join the Support Discord here: https://discord.gg/hmmfXud")


def setup(bot):
    bot.add_cog(Help(bot))

        