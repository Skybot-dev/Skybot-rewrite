import json
import discord
from trello import TrelloClient
from discord.ext import commands


def get_config():
    with open("config.json", "r") as fp:
        return json.load(fp)
def trelloinit(config):
    trelloconfig = config["trello"]
    client = TrelloClient(api_key=trelloconfig["api_key"], api_secret=trelloconfig["api_secret"])
    return (client, client.get_board(trelloconfig["board_id"]))

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

async def get_user_guilds(bot : commands.AutoShardedBot, user):
    guilds = []
    for guild in bot.guilds:
        guild : discord.Guild
        member_ids = [member.id for member in await guild.chunk()]
        if user.id in member_ids:
            guilds.append(guild)
    return guilds

async def is_verified(bot, user):
    if isinstance(user, discord.abc.User):
        user_doc = await bot.users_db["connections"].find_one({"id" : user.id})
        if not user_doc : return False
        return user_doc["verified"]
    else:
        if not user : return False
        return user["verified"]
    
async def get_uuid_profileid(bot : commands.Bot, user : discord.abc.User):
    user_doc = await bot.users_db["connections"].find_one({"id" : user.id})
    if not user_doc: return None, None
    if "profile_id" not in user_doc.keys():
        return user_doc["uuid"], None
    else:
        return user_doc["uuid"], user_doc["profile_id"]
    