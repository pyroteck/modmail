import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.dm_messages = True

bot = commands.Bot(command_prefix='!', intents=intents)

MODMAIL_CHANNEL_ID = 0000000000000000000  # Replace with your modmail channel ID

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    modmail_channel = bot.get_channel(MODMAIL_CHANNEL_ID)
    if modmail_channel is None:
        print(f"Modmail channel with ID {MODMAIL_CHANNEL_ID} not found.")
    else:
        print(f"Modmail channel is {modmail_channel.name}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if isinstance(message.channel, discord.DMChannel):
        modmail_channel = bot.get_channel(MODMAIL_CHANNEL_ID)
        if modmail_channel is None:
            await message.author.send("There was an error sending your message to the mods. Please try again later.")
            return

        # Check if a thread already exists for this user
        user_thread = None
        for thread in modmail_channel.threads:
            if thread.name == str(message.author.id):
                user_thread = thread
                break

        if user_thread is None:
            # Create a new thread if one doesn't exist
            user_thread = await modmail_channel.create_thread(name=str(message.author.id), auto_archive_duration=10080)  # Use auto_archive_duration in minutes

        # Create an embedded message for the modmail thread
        embed = discord.Embed(
            description=f"ModMail message from <@{message.author.id}>:\n\n{message.content}",
            color=discord.Color.blue()
        )
        embed.set_author(name=message.author.name, icon_url=message.author.avatar.url if message.author.avatar else discord.Embed.Empty)
        embed.timestamp = message.created_at

        # Send the embedded message to the thread and get the message object
        sent_message = await user_thread.send(embed=embed)  # Send the embedded message to the thread
        # Create a link to the sent message
        message_link = f"https://discord.com/channels/{modmail_channel.guild.id}/{user_thread.id}/{sent_message.id}"
        # Send the link to the modmail channel
        await modmail_channel.send(f"@here new ModMail message from <@{message.author.id}>. [Click here to view]({message_link})")

        await message.author.send("Your message has been sent to the mods. You will receive a response shortly.")

    elif isinstance(message.channel, discord.Thread):
        # Assuming the thread name is the user's ID
        user_id = int(message.channel.name)
        user = await bot.fetch_user(user_id)

        # Create an embedded message for the user
        embed = discord.Embed(
            title="Response from a mod",
            description=message.content,
            color=discord.Color.green()
        )
        embed.timestamp = message.created_at

        await user.send(embed=embed)  # Send the embedded message to the user

        # Send a confirmation message to the mod
        await message.channel.send("Response sent")

    await bot.process_commands(message)

bot.run('')  # Replace with your bot token
