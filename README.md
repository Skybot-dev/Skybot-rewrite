# Skybot-rewrite
Rewrite of the Hypixel Skybot.
---

## Features
- **!skills**

![skill image](https://cdn.discordapp.com/attachments/667402160505487360/741030715923103787/unknown.png)

- **!stats**

![stats image](https://cdn.discordapp.com/attachments/667402160505487360/741030821854445658/unknown.png)

- **!slayer**

![slayer image](https://cdn.discordapp.com/attachments/667402160505487360/741030911134400632/unknown.png)
### And many more commands inlcuding user management commands for server owners, scammer report/check commands and more!
---
## Hosting

### Config.json
config.json must be filled out correctly in order for the bot to function properly.
```javascript
{
    "token" : "", // put your bot token from discordapp.com/developers here (required)
    "api_keys" : [""], // List of hypixel API keys to use (required)
    "default_prefix" : "", // the default prefix for the bot (required)
    "database" : {
        "local": false, // whether the mongoDB database is hosted locally or on MongoDB atlas (required)
        "username" : "", // mongoDB username (required)
        "password" : "", // mongoDB password (required)
        "address" : "", //mongoDB database address (required)
        "default_db" : "" //default database to use (optional)
    },
    "staff_role" : 0, // ID of the role that has access to all developer commands (required)
    "slothpixel_key": "", // Slothpixel API key (optional)
    "support_guild": {
	"ID": 0, // guild ID of the discord support server (required)
	"invite_link": "https://discord.com/invite/inviteCode", // invite link for the discord support server (required)
    "suggest_channel": 0, // channel ID for suggestions to go to (required)
    "log_channel": 0, // channel ID for all bot logs to be sent to (required)
    "report_channel": 0, // channel ID for scammer reports to be sent to (required)
    "stats": {
        "channel": 0, // channel ID for bot stats (optional)
        "message": 0 // message ID of stats message (optional)
    }
    },
    "trello": {
        "enabled": false, // whether to integrate suggestions with a trello board (required)
        "api_key": "", // trello API key (required if enabled)
        "api_secret": "", // trello API secret (required if enabled)
        "board_id": "" // trello board ID for suggestions (required if enabled)
    },
    "statuspage": {
        "enabled": false // whether or not to enable statuspage.io (required)
    },
    "bot_invite": "", // bot invite link (required, but doesn't have to work)
    "status_list": [{"type": "playing", "content": "skyblock"}] // list of statuses for the bot (required)
}
```
### requirements
- the bot must be run with at least python3.7
- all dependencies must be install with `python3 -m pip install -r requirements.txt`.
---
# Contributors:
- [@lolieg](https://github.com/lolieg) - Lead developer and project owner
- [@pjones123](https://github.com/pjones123) - Contributing developer
- [@juli324](https://github.com/Juli324)- server administrator
##### If you feel that you have something to add, feel free to fork the repository and open a pull request.
# Links
- join the [support server](https://discord.gg/7fPv2uY2Tf) on discord
- vote for the bot on [top.gg](https://top.gg/bot/630106665387032576)
