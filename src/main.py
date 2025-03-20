# TODO: prevent multiple registrations (utilize a simple sqlite db).

# TODO: give user role to registered user, role allows for viewing stuff.
# TODO: have default text placed into support channel.

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

@bot.event
async def on_ready():
    print(f"Support bot logged in as {bot.user}!")


@bot.command(description="Registers the user to the support system.")
async def register(ctx: discord.ApplicationContext, name: discord.SlashCommandOptionType.string):
    # Creating member object.
    member: discord.Member = ctx.guild.get_member(ctx.author.id)

    # Updating existing support channel name.
    if src.database.is_user_registered(connection, ctx.author.id, ctx.guild.id):
        print("User already registered!")
        return

    # Setting member nickname.
    try:
        await member.edit(nick=name)
    except BaseException:
        await ctx.respond("Could not change your nickname (does not work for admins).", ephemeral=True)

    # Creating support channel category (if it did not already exist).
    category = discord.utils.get(ctx.guild.categories, name="support")
    if not category:
        category = await ctx.guild.create_category("support")

    # Creating the support role (if it did not already exist).
    support_role = await create_role(ctx.guild, "Support Staff")
    # Creating the generic user role (if it did not already exist).
    generic_role = await create_role(ctx.guild, "User")

    # Creating role overrides to make member support channel private.
    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        support_role: discord.PermissionOverwrite(read_messages=True),
        member: discord.PermissionOverwrite(read_messages=True),
    }

    # Creating member support channel.
    new_channel_name: str = "-".join(name.lower().split()) + "-support"
    new_channel: discord.TextChannel = await ctx.guild.create_text_channel(
        name=new_channel_name,
        category=category,
        overwrites=overwrites
    )
    print(f"Successfully created support channel '{new_channel_name}'.")

    src.database.register_user(connection, ctx.author.id, ctx.guild.id, new_channel.id)

    # End-user response.
    await ctx.respond("Successfully registered you to the support system!", ephemeral=True)
    print(f"Successfully registered user '{ctx.user}' to the support system.")


# Attempts to create a user role in a selected guild. If the role already exists, returns the role object.
# Otherwise, creates the role and returns the role object.
async def create_role(guild: discord.Guild, role_name: str) -> discord.Role:
    if not discord.utils.get(guild.roles, name=role_name):
        new_role: discord.Role = await guild.create_role(name=role_name)
        print(f"Successfully created role '{role_name}'.")
    else:
        new_role: discord.Role = discord.utils.get(guild.roles, name=role_name)

    return new_role


bot.run(str(os.getenv("DISCORD_API_TOKEN")))
