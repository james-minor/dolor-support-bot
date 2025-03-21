import discord
import os
import dotenv
import sqlite3

import dm_support.database
import dm_support.utils
import dm_support.messaging

# Initializing environment.
dotenv.load_dotenv()

# Initializing the Discord bot.
intents: discord.Intents = discord.Intents.all()
bot = discord.Bot(intents=intents)

# Initializing database connection and creating tables.
connection: sqlite3.Connection = sqlite3.connect("database.db")
dm_support.database.initialize(connection)


@bot.event
async def on_ready():
    print(f"Support bot logged in as {bot.user}!")


@bot.command(description="Creates a register support ticket button")
async def button(ctx: discord.ApplicationContext):
    await dm_support.messaging.send_register_direct_message(ctx.user, ctx.guild)


@bot.event
async def on_guild_join(guild: discord.Guild):
    # Creating the support role (if it did not already exist).
    staff_role = await dm_support.utils.create_role(guild, "Support Staff")

    # Creating the generic registered user role (if it did not already exist).
    student_role = await dm_support.utils.create_role(guild, "Student")
    if student_role:
        await student_role.edit(color=discord.Color(0x4499d5))


@bot.event
async def on_member_join(member: discord.Member):
    await dm_support.messaging.send_register_direct_message(member._user, member.guild, register_callback=register_user)



async def register_user(interaction: discord.Interaction, name: str, guild_id: int):
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
    if dm_support.database.is_user_registered(connection, interaction.user.id, guild.id):
        print(f"User '{interaction.user}' already registered.")

        # Getting the support channel id for the user.
        support_channel_id: int = dm_support.database.get_support_channel_id(connection, interaction.user.id, guild.id)

        # Updating the existing support channel.
        if discord.utils.get(guild.text_channels, id=support_channel_id):
            print(f"Support channel already exists for '{interaction.user}', updating existing support channel name.")
            await bot.get_channel(support_channel_id).edit(name=dm_support.utils.generate_channel_name(name))
            await interaction.followup.send("Successfully updated your support channel name.", ephemeral=True)

        # Creating a new support channel (in the event the existing channel got deleted).
        else:
            print(f"Support channel does not exist for '{interaction.user}' (probable accidental deletion), creating new support channel.")
            new_channel: discord.TextChannel = await dm_support.utils.create_support_channel(interaction, guild, name)
            dm_support.database.update_support_channel_id(connection, interaction.user.id, guild.id, new_channel.id)
            await interaction.followup.send("Successfully recreated your support channel.", ephemeral=True)

        return

    # Creating new member support channel.
    new_support_channel = await dm_support.utils.create_support_channel(interaction, guild, name)
    print(f"Successfully created support channel '{new_support_channel.name}'.")

    # Registering new user in database.
    dm_support.database.register_user(connection, interaction.user.id, guild.id, new_support_channel.id)

    # Adding member to Student role.
    try:
        registered_user_role: discord.Role = discord.utils.get(guild.roles, name="Student")

        if registered_user_role:
            print(f"Successfully retrieved Student role.")
            await member.add_roles(registered_user_role)
            print(f"Assigned student role to {member}")
        else:
            print("Had issues retrieving registered user role.")

    except BaseException:
        await interaction.followup.send("Could not give you Student role (does not work for administrators).", ephemeral=True)

    # End-user response.
    await interaction.followup.send("Successfully registered you to the support system!", ephemeral=True)
    print(f"Successfully registered user '{interaction.user}' to the support system.")



bot.run(str(os.getenv("DISCORD_API_TOKEN")))
