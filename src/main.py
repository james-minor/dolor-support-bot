import discord
import os
import dotenv
import sqlite3

import src.database

# Initializing environment.
dotenv.load_dotenv()

# Initializing the Discord bot.
intents: discord.Intents = discord.Intents.all()
bot = discord.Bot(intents=intents)

# Initializing database connection and creating tables.
connection: sqlite3.Connection = sqlite3.connect("database.db")
src.database.initialize(connection)

class RegisterModal(discord.ui.Modal):
    def __init__(self, guild_id: int):
        super().__init__(title="Register")

        self.name_input = discord.ui.InputText(label="Enter your name:", style=discord.InputTextStyle.short)
        self.add_item(self.name_input)

        self.guild_id: int = guild_id

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await register_user(interaction, self.name_input.value, self.guild_id)


def generate_channel_name(name: str) -> str:
    return "ticket-" + "-".join(name.lower().split())


async def create_support_channel(interaction: discord.Interaction, guild: discord.Guild, name: str) -> discord.TextChannel:
    # Creating support channel category (if it did not already exist).
    category = discord.utils.get(guild.categories, name="tickets")
    if not category:
        category = await guild.create_category("tickets")

    # Creating role overrides to make member support channel private.
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        discord.utils.get(guild.roles, name="Support Staff"): discord.PermissionOverwrite(read_messages=True),
        guild.get_member(interaction.user.id): discord.PermissionOverwrite(read_messages=True),
    }

    # Creating the support channel.
    new_channel_name: str = generate_channel_name(name)
    new_channel: discord.TextChannel = await guild.create_text_channel(
        name=new_channel_name,
        category=category,
        overwrites=overwrites
    )

    # Printing welcome text to support channel.
    welcome_file_path = "welcome.txt"
    with open(welcome_file_path, "r") as welcome_file:
        content = welcome_file.read()
        await new_channel.send(content=content)

    return new_channel


async def send_register_button(guild_id: int, channel: discord.DMChannel):
    register_button = discord.ui.Button(label="Register", style=discord.ButtonStyle.primary)

    async def register_button_callback(interaction: discord.Interaction):
        register_modal = RegisterModal(guild_id)
        await interaction.response.send_modal(register_modal)

    register_button.callback = register_button_callback

    view = discord.ui.View()
    view.add_item(register_button)

    await channel.send(content=f"Welcome to the server, click this button to open a ticket!", view=view)


async def send_register_direct_message(user: discord.User, guild: discord.Guild):
    dm_channel = await user.create_dm()
    await send_register_button(guild.id, dm_channel)

    print(f"Sent registration direct message to user '{user}'")


@bot.event
async def on_ready():
    print(f"Support bot logged in as {bot.user}!")


@bot.command(description="Creates a register support ticket button")
async def button(ctx: discord.ApplicationContext):
    await send_register_direct_message(ctx.user, ctx.guild)


@bot.event
async def on_guild_join(guild: discord.Guild):
    # Creating the support role (if it did not already exist).
    staff_role = await create_role(guild, "Support Staff")

    # Creating the generic registered user role (if it did not already exist).
    student_role = await create_role(guild, "Student")
    if student_role:
        await student_role.edit(color=discord.Color(0x4499d5))


@bot.event
async def on_member_join(member: discord.Member):
    await send_register_direct_message(member._user, member.guild)


async def register_user(interaction: discord.Interaction, name: str, guild_id: int):
    # Name parameter validation.
    if len(name) < 1 or len(name) > 35:
        await interaction.followup.send("Names must be between 1 and 35 characters long.", ephemeral=True)
        return
    if not name.replace(" ", "").isalpha():
        await interaction.followup.send("Names may only contain letters.", ephemeral=True)
        return

    # Getting guild object from guild ID.
    guild: discord.Guild = bot.get_guild(guild_id)

    # Getting local member object from interaction.
    member: discord.Member = guild.get_member(interaction.user.id)


    # Setting member nickname.
    try:
        await member.edit(nick=name)
    except BaseException:
        await interaction.followup.send("Could not change your nickname (does not work for admins).", ephemeral=True)

    # Updating existing support channel name.
    if src.database.is_user_registered(connection, interaction.user.id, guild.id):
        print(f"User '{interaction.user}' already registered.")

        # Getting the support channel id for the user.
        support_channel_id: int = src.database.get_support_channel_id(connection, interaction.user.id, guild.id)

        # Updating the existing support channel.
        if discord.utils.get(guild.text_channels, id=support_channel_id):
            print(f"Support channel already exists for '{interaction.user}', updating existing support channel name.")
            await bot.get_channel(support_channel_id).edit(name=generate_channel_name(name))
            await interaction.followup.send("Successfully updated your support channel name.", ephemeral=True)

        # Creating a new support channel (in the event the existing channel got deleted).
        else:
            print(f"Support channel does not exist for '{interaction.user}' (probable accidental deletion), creating new support channel.")
            new_channel: discord.TextChannel = await create_support_channel(interaction, guild, name)
            src.database.update_support_channel_id(connection, interaction.user.id, guild.id, new_channel.id)
            await interaction.followup.send("Successfully recreated your support channel.", ephemeral=True)

        return

    # Creating new member support channel.
    new_support_channel = await create_support_channel(interaction, guild, name)
    print(f"Successfully created support channel '{new_support_channel.name}'.")

    # Registering new user in database.
    src.database.register_user(connection, interaction.user.id, guild.id, new_support_channel.id)

    # Adding member to Student role.
    try:
        registered_user_role: discord.Role = discord.utils.get(guild.roles, name="Student")

        if registered_user_role:
            await interaction.user.add_roles(registered_user_role)
        else:
            print("Had issues retrieving registered user role.")

    except BaseException:
        await interaction.followup.send("Could not give you Student role (does not work for administrators).", ephemeral=True)

    # End-user response.
    await interaction.followup.send("Successfully registered you to the support system!", ephemeral=True)
    print(f"Successfully registered user '{interaction.user}' to the support system.")


# Attempts to create a user role in a selected guild. If the role already exists, returns None.
# Otherwise, creates the role and returns the role object.
async def create_role(guild: discord.Guild, role_name: str) -> discord.Role | None:
    if not discord.utils.get(guild.roles, name=role_name):
        new_role: discord.Role = await guild.create_role(name=role_name)
        print(f"Successfully created role '{role_name}'.")
        return new_role

    return None


bot.run(str(os.getenv("DISCORD_API_TOKEN")))
