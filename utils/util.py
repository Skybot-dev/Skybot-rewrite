import json
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