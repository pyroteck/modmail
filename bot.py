from datetime import datetime
import discord
from discord.ext import commands
import json
import io
import pytz

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)
timezone = pytz.timezone("America/Los_Angeles")

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

class FormResponses():
    def __init__(self):
        self.general_nature = {
            "label": "Package Information",
            "description": "What is the general nature of what you'd like to send?",
            "input": ""
        }
        self.sender_type = {
            "label": "Sender Type",
            "description": "Are you sending something from yourself, or on behalf of someone else?",
            "input": ""
        }
        self.special_handling = {
            "label": "Special Handling Requirements",
            "description": "Are there any unusual contents, special handling requirements, or other things to be noted?",
            "input": "No response"
        }
        self.stream_opening = {
            "label": "Stream Opening",
            "description": "Are you comfortable with the contents being opened on stream?",
            "input": ""
        }
        self.mailbox_privacy = {
            "label": "Mailbox Privacy",
            "description": "Do you understand the mailbox address is private and should not be reposted or shared with others?",
            "input": ""
        }
        self.safety_concerns = {
            "label": "Safety Concerns",
            "description": "Are you comfortable with Chai/the mod team declining your package for safety concerns?",
            "input": ""
        }
        self.claim_rights = {
            "label": "Claim Rights",
            "description": "Do you agree that once an item is delivered, you forfeit the right to claim it back?",
            "input": ""
        }

# Modal for the form submission
class FormModal(discord.ui.Modal, title='CHAI-MAIL Form Submission'):
    def __init__(self, thread_id, user_id):
        super().__init__()
        self.thread_id = thread_id
        self.user_id = user_id
        self.responses = FormResponses()

        # Define text inputs as instance attributes
        self.general_nature = discord.ui.TextInput(
            label=self.responses.general_nature["label"],
            placeholder=self.responses.general_nature["description"],
            style=discord.TextStyle.long,
            required=True
        )

        self.sender_type = discord.ui.TextInput(
            label=self.responses.sender_type["label"],
            placeholder=self.responses.special_handling["description"],
            style=discord.TextStyle.long,
            required=True
        )

        self.special_handling = discord.ui.TextInput(
            label=self.responses.special_handling["label"],
            placeholder=self.responses.special_handling["description"],
            style=discord.TextStyle.long,
            required=False
        )

        # Add the text inputs to the modal
        self.add_item(self.general_nature)
        self.add_item(self.sender_type)
        self.add_item(self.special_handling)

    async def on_submit(self, interaction: discord.Interaction):
        self.responses.general_nature["input"]=self.general_nature.value
        self.responses.sender_type["input"]=self.sender_type.value
        if self.special_handling.value:
            self.responses.special_handling["input"] = self.special_handling.value

        # Delete the original message with the form button
        try:
            await interaction.message.delete()
        except:
            pass

        # Send a new message with the agreement form button
        agreement_embed = discord.Embed(
            title="📄 CHAI-MAIL AGREEMENTS 📄",
            description="Form responses saved. Please complete this agreement form as well to submit it!",
            color=discord.Color.light_gray()
        )

        agreement_view = AgreementButtonView(self.user_id, self.thread_id, self.responses)

        # Send the agreement form to the user
        user = await bot.fetch_user(self.user_id)
        try:
            await user.send(embed=agreement_embed, view=agreement_view)
        except discord.Forbidden:
            print("Error happened.")

        await interaction.response.defer()

class AgreementModal(discord.ui.Modal, title='CHAI-MAIL Agreement Form'):
    def __init__(self, thread_id, user_id, responses: FormResponses):
        super().__init__()
        self.thread_id = thread_id
        self.user_id = user_id
        self.responses = responses

        self.stream_opening = discord.ui.TextInput(
            label=self.responses.stream_opening["label"],
            placeholder=self.responses.stream_opening["description"],
            style=discord.TextStyle.long,
            required=True
        )
        self.mailbox_privacy = discord.ui.TextInput(
            label=self.responses.mailbox_privacy["label"],
            placeholder=self.responses.mailbox_privacy["description"],
            style=discord.TextStyle.long,
            required=True
        )
        self.safety_concerns = discord.ui.TextInput(
            label=self.responses.safety_concerns["label"],
            placeholder=self.responses.safety_concerns["description"],
            style=discord.TextStyle.long,
            required=True
        )
        self.claim_rights = discord.ui.TextInput(
            label=self.responses.claim_rights["label"],
            placeholder=self.responses.claim_rights["description"],
            style=discord.TextStyle.long,
            required=True
        )

        # Add the text inputs to the modal
        self.add_item(self.stream_opening)
        self.add_item(self.mailbox_privacy)
        self.add_item(self.safety_concerns)
        self.add_item(self.claim_rights)

    async def on_submit(self, interaction: discord.Interaction):
        # Delete the original message with the form button
        try:
            await interaction.message.delete()
        except:
            pass

        # Process the agreement form submission
        form_embed = discord.Embed(
            title="Mail Form Response",
            description=f"Submitted by <@{self.user_id}>\n"
                        f"User ID: `{self.user_id}`",
            color=discord.Color.green(),
            timestamp=datetime.now(timezone)
        )
        user_response_embed=discord.Embed(
            title="Form Submitted Successfully ✅",
            description="Your form has been submitted to the mods with the following information:",
            color=discord.Color.green(),
            timestamp=datetime.now(timezone)
        )

        self.responses.stream_opening["input"] = self.stream_opening.value
        self.responses.mailbox_privacy["input"] = self.mailbox_privacy.value
        self.responses.safety_concerns["input"] = self.safety_concerns.value
        self.responses.claim_rights["input"] = self.claim_rights.value

        for key, value in vars(self.responses).items():
            form_embed.add_field(
                name=value["description"],
                value=value["input"],
                inline=False
            )
            user_response_embed.add_field(
                name=value["description"],
                value=value["input"],
                inline=False
            )
        # Send the response back to the modmail thread
        modmail_channel = bot.get_channel(MODMAIL_CHANNEL_ID)
        if modmail_channel:
            thread = modmail_channel.get_thread(self.thread_id)
            if thread:
                await thread.send(embed=form_embed)

        await interaction.response.send_message(embed=user_response_embed)


class AgreementButtonView(discord.ui.View):
    def __init__(self, user_id, thread_id, responses: FormResponses):
        super().__init__()
        self.user_id = user_id
        self.thread_id = thread_id
        self.responses = responses

    @discord.ui.button(label="Complete Agreement Form (2/2)", style=discord.ButtonStyle.primary, custom_id="open_agreement_form")
    async def open_agreement_form_button(self, interaction, button):
        # Create and send the agreement modal
        modal = AgreementModal(self.thread_id, self.user_id, self.responses)
        await interaction.response.send_modal(modal)


# View for the form button
class FormButtonView(discord.ui.View):
    def __init__(self, user_id, thread_id):
        super().__init__()
        self.user_id = user_id
        self.thread_id = thread_id

    @discord.ui.button(label="Complete Info Form (1/2)", style=discord.ButtonStyle.primary, custom_id="open_form")
    async def open_form_button(self, interaction, button):
        # Create and send the modal correctly
        modal = FormModal(self.thread_id, self.user_id)
        await interaction.response.send_modal(modal)

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
            try:
                user_thread = await modmail_channel.create_thread(
                    name=str(message.author.id),
                    type=discord.ChannelType.public_thread,
                    auto_archive_duration=10080
                )
            except discord.Forbidden:
                await message.author.send("I couldn't create a modmail thread. Please try again later or contact a moderator directly.")
                return

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

                await message.channel.send("Response sent to user")

    await bot.process_commands(message)

# Command to send the form
@bot.command(name="sendmailform")
@commands.has_permissions(administrator=True)
async def sendmailform(ctx):
    # Check if the command is used in a modmail thread
    if not isinstance(ctx.channel, discord.Thread):
        await ctx.reply("This command can only be used in a modmail thread!", delete_after=5)
        return

    # Verify this is a modmail thread (by checking the parent channel)
    if not ctx.channel.parent_id == MODMAIL_CHANNEL_ID:
        await ctx.reply("This command can only be used in a modmail thread!", delete_after=5)
        return

    # Get the user ID from the thread name
    user_id = int(ctx.channel.name)  # This gets the user ID from thread name
    user = await bot.fetch_user(user_id)

    # Create the form embed
    form_embed = discord.Embed(
        title="📬 CHAI-MAIL MINI FORM 📬",
        description="This form is required to be submitted before the mailing address is provided.\n"
                    "Click the button below to open the form.",
        color=discord.Color.light_gray()
    )

    # Create a view with the form button
    view = FormButtonView(user_id, ctx.channel.id)

    try:
        # Send the form to the user
        await user.send(embed=form_embed, view=view)
        await ctx.reply(f"Mail form sent to <@{user_id}>.")
    except discord.Forbidden:
        await ctx.reply("I couldn't send the form to the user. They may have DMs disabled.")

@sendmailform.error
async def lockdown_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        print(f"Attempt from {ctx.author} (user ID: {ctx.author.id}) to run sendmailform command.")

bot.run(config.get("CLIENT_TOKEN"))
