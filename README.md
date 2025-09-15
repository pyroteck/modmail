Simple discord.py bot for a "Mod Mail" functionality.

Users can DM the bot, and the bot will create a thread in a specified channel (make sure this channel only has moderator access).

Responses to the embedded messages will then be sent back to the user anonymously.

To run this bot, clone the repository and create a file named `secrets.json` with the following:

```json
{
    "CLIENT_TOKEN": "",
    "MODMAIL_CHANNEL_ID": ""
}
```

Insert your bot's client token inside the quotes for CLIENT_TOKEN, and the channel ID you want threads to be created in for MODMAIL_CHANNEL_ID.

To start the bot with Docker, simply run `docker compose up -d`, or run the `bot.py` file with python after installing discord.py with pip.
