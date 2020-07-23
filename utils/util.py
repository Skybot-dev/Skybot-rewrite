import json
import aiohttp
import discord
from trello import TrelloClient
from discord.ext import commands


def get_config():
    with open("config.json", "r") as fp:
        return json.load(fp)
def trelloinit():
    trelloconfig = get_config()["trello"]
    client = TrelloClient(api_key=trelloconfig["api_key"], api_secret=trelloconfig["api_secret"])
    return client.get_board(trelloconfig["board_id"])

def is_staff(ctx):
    if isinstance(ctx.author, discord.Member):
        return get_config()["staff_role"] in [role.id for role in ctx.author.roles]
    return ctx.author.id == 201686355493912576 or ctx.author.id == 564798709045526528

def has_is_staff(command):
    if command and hasattr(command, "checks"):
        checks = [check.__name__ for check in command.checks]
        if "is_staff" in checks:
            return True
    return False