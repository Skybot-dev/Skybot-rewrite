import discord
from discord.ext import commands


class Connections(commands.Cog):
    def __init__(self, bot):
        self.bot=bot


    @commands.Cog.listener()
    async def on_ready(self):
        pass

    @commands.group(name="account",
                    description="Set up personal settings.",
                    aliases=["acc"],
                    usage="[setup/setlink/setprofile/verify]",
                    invoke_without_command=True)
    async def account(self, ctx):
        await ctx.invoke(self.bot.get_command("help show_command"), arg="account")

    @account.command()
    async def setup(self, ctx):
        print("Walk user trough linking and verifying and defaultprofile")

    @account.command()
    async def setlink(self, ctx):
        print("set link")

    @account.command()
    async def verify(self, ctx):
        print("verify")

    @account.command()
    async def setprofile(self, ctx):
        print("set profile")


def setup(bot):
    bot.add_cog(Connections(bot))