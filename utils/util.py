import json

def get_config():
    with open("config.json", "r") as fp:
        return json.load(fp)

def is_staff(ctx):
    return get_config()["staff_role"] in [role.id for role in ctx.author.roles]