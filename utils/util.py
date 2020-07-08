import json

def get_config():
    with open("config.json", "r") as fp:
        return json.load(fp)