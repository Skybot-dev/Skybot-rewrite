import discord
from EZPaginator import Paginator
from utils.embed import Embed
from utils.expander import Expander
from discord.ext import commands
from utils import logging
from utils.util import has_is_staff, is_staff

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot : commands.AutoShardedBot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        pass
    
    def cog_unload(self):
        pass

    @commands.cooldown(3, 5, commands.BucketType.channel)
    @commands.group(name="help", description="List commands and command info.", aliases=["cmds"], usage="[Category/Command]")
    async def help(self, ctx : commands.Context, *, arg=None):
        if arg is None or arg.lower() == "list":
            await ctx.invoke(self.list)
            return

        arg = arg.lower()
        staff = is_staff(ctx)
        command_names = [command.name for command in self.bot.commands if str(command.cog) != "Admin" and str(command.cog) != "Help" and not has_is_staff(command) or staff]
        for command in self.bot.commands:
            if str(command.cog) != "Admin" and str(command.cog) != "Help" and not has_is_staff(command) or staff:
                for alias in command.aliases:
                    command_names.append(alias)
        if arg.split(" ")[0] in command_names:
            await ctx.invoke(self.show_command, arg=arg)
            return
        
        cog_names = [cog.lower() for cog in self.bot.cogs if cog != "Admin" and cog != "Help"]
        if arg in cog_names:
            await ctx.invoke(self.show_cog, arg=arg)
            return

        raise commands.BadArgument(message="Command or Category")
        
    async def get_list_embed(self, ctx, expanded=False):
        staff = is_staff(ctx)
        list_embed = Embed(title="Categories", bot=self.bot, user=ctx.author)
        list_embed.set_author(name=f"Use {ctx.prefix}help [Command/Category]")
        await list_embed.set_requested_by_footer()

        for name, cog in self.bot.cogs.items():
            if name == "Admin" or name == "Help": continue
            if not cog.get_commands(): continue
            
            commands = []
            for command in cog.get_commands():
                if has_is_staff(command) and not staff: continue
                if hasattr(command, "commands") and expanded:
                    sub_cmds = [command.name for command in command.commands if not has_is_staff(command) or staff]
                    if sub_cmds:
                        commands.append("`" + command.name + "`\n - " + "\n - ".join(sub_cmds))
                    else:
                        commands.append(f"`{command.name}`")
                else:
                    commands.append(f"`{command.name}`")
            print(commands)
            list_embed.add_field(name=name, value="\n".join(commands), inline=True)

        list_embed.add_field(name="Links", value="[Apply as Dev](https://discord.gg/SQebkz9) | [Vote](https://top.gg/bot/630106665387032576/vote) | [Invite the Bot to your server](https://discordapp.com/oauth2/authorize?client_id=630106665387032576&scope=bot&permissions=8) | [Support Server](https://discord.gg/hmmfXud) | [Todos](https://trello.com/b/2yBAtx82/skybot-rewrite)", inline=False)
        return list_embed

    @help.command()
    async def list(self, ctx):
        embed_exp = await self.get_list_embed(ctx, True)
        embed = await self.get_list_embed(ctx)
        msg = await ctx.send(embed=embed)
        
        expander = Expander(self.bot, msg, embeds=[embed, embed_exp])
        await expander.start()
        

    @help.command()
    async def show_cog(self, ctx, arg):
        cogs = {z.lower(): self.bot.cogs[z] for z in self.bot.cogs}
        cog : commands.Cog = cogs[arg]
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
        if isinstance(arg, commands.Command):
            command = arg
        elif isinstance(arg, str):
            command = self.bot.get_command(arg)
            
        if has_is_staff(command) and not is_staff(ctx):
            raise commands.BadArgument(message="Command or Category")
        
        if command.parents:
            command_embed = Embed(title=f"{ctx.prefix}{' '.join([command.name.capitalize() for command in command.parents])} {command.name.capitalize()}", bot=self.bot, user=ctx.author)
        else:
            command_embed = Embed(title=f"{ctx.prefix}{command.name.capitalize()}", bot=self.bot, user=ctx.author)

        await command_embed.set_requested_by_footer()

        if command.description == "": description = "No Description."
        else: description = command.description
        if command.usage == None: usage = "No Usage."
        elif command.parents: usage = f"{ctx.prefix}{' '.join([command.name.capitalize() for command in command.parents])} {command.name.capitalize()} {command.usage}"
        else: usage = f"{ctx.prefix}{command.name.capitalize()} {command.usage}"
        if command.aliases == []: aliases = "No Aliases."
        else: aliases = str(command.aliases).replace("[", " ").replace("]", " ").replace("'", " ").replace(",", "\n")

        command_embed.add_field(name="Description", value=description, inline=False)
        command_embed.add_field(name="Usage", value=usage, inline=False)
        command_embed.add_field(name="Aliases", value=aliases, inline=False)

        await ctx.send(embed=command_embed)



def setup(bot):
    bot.add_cog(Help(bot))

        