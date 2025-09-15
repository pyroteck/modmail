import discord
from discord.ext import commands
import json
import io

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.dm_messages = True

bot = commands.Bot(command_prefix='!', intents=intents)

with open('secrets.json') as config_file:
    config = json.load(config_file)

MODMAIL_CHANNEL_ID = int(config.get("MODMAIL_CHANNEL_ID"))

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
            user_thread = await modmail_channel.create_thread(
                name=str(message.author.id),
                type=discord.ChannelType.public_thread,
                auto_archive_duration=10080
            )

        # Create an embedded message for the modmail thread
        embed = discord.Embed(
            description=f"ModMail message from <@{message.author.id}>:\n\n{message.content}",
            color=discord.Color.blue()
        )
        embed.set_author(name=message.author.name, icon_url=message.author.avatar.url if message.author.avatar else discord.Embed.Empty)
        embed.timestamp = message.created_at

        # Handle images in the message
        files = []
        if message.attachments:
            for attachment in message.attachments:
                if attachment.content_type and attachment.content_type.startswith('image/'):
                    # Download the image
                    image_data = await attachment.read()
                    file = discord.File(io.BytesIO(image_data), filename=attachment.filename)
                    files.append(file)

        # Send the embedded message first, then files
        sent_message = await user_thread.send(embed=embed)

        # If there are files, send them as a separate message
        if files:
            await user_thread.send(files=files)

        message_link = f"https://discord.com/channels/{modmail_channel.guild.id}/{user_thread.id}/{sent_message.id}"
        await modmail_channel.send(f"@here new ModMail message from <@{message.author.id}>. [Click here to view]({message_link})")

        await message.author.send("Your message has been sent to the mods. You will receive a response shortly.")

    elif isinstance(message.channel, discord.Thread):
        # Check if the message is a reply to the modmail embed
        if message.reference and message.reference.message_id:
            referenced_message = message.reference.cached_message or await message.channel.fetch_message(message.reference.message_id)

            if referenced_message.embeds and referenced_message.embeds[0].color == discord.Color.blue():
                # This is a response to a modmail message
                user_id = int(message.channel.name)
                user = await bot.fetch_user(user_id)

                # Create an embedded message for the user
                embed = discord.Embed(
                    title="Response from a mod",
                    description=message.content,
                    color=discord.Color.green()
                )
                embed.timestamp = message.created_at

                # Handle images in the response
                files = []
                if message.attachments:
                    for attachment in message.attachments:
                        if attachment.content_type and attachment.content_type.startswith('image/'):
                            image_data = await attachment.read()
                            file = discord.File(io.BytesIO(image_data), filename=attachment.filename)
                            files.append(file)

                # Send embed first, then files if any
                sent_message = await user.send(embed=embed)

                # If there are files, send them as a separate message
                if files:
                    await user.send(files=files)

                await message.channel.send("Response sent")

    await bot.process_commands(message)

bot.run(config.get("CLIENT_TOKEN"))
