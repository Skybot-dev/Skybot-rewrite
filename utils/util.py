import json
import aiohttp
from trello import TrelloClient
def get_config():
    with open("config.json", "r") as fp:
        return json.load(fp)
def trelloinit():
    trelloconfig = get_config()["trello"]
    client = TrelloClient(api_key=trelloconfig["api_key"], api_secret=trelloconfig["api_secret"])
    return client.get_board(trelloconfig["board_id"])

def is_staff(ctx):
    return get_config()["staff_role"] in [role.id for role in ctx.author.roles]

async def uuid_from_name(name):
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.mojang.com/users/profiles/minecraft/'+name) as resp:
                try:
                    player = await resp.json()
                except aiohttp.ContentTypeError:
                    return None
        return player["id"]