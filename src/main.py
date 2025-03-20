# TODO: prevent multiple registrations (utilize a simple sqlite db).

# TODO: give user role to registered user, role allows for viewing stuff.
# TODO: have default text placed into support channel.

import discord
import os
import dotenv
import sqlite3

# Initializing environment.
dotenv.load_dotenv()

# Initializing the Discord bot.
intents: discord.Intents = discord.Intents.all()
bot = discord.Bot(intents=intents)

# Initializing database connection and creating tables.
database: sqlite3.Connection = sqlite3.connect("database.db")

def initialize_database(database_connection: sqlite3.Connection):
    cursor: sqlite3.Cursor = database_connection.cursor()
    cursor.execute("""
        create table if not exists `registered_users` (
          `id` integer not null primary key autoincrement,
          `user_id` int not null,
          `guild_id` int not null
        )
    """)

initialize_database(database)

# Returns True if the passed Discord user is registered in a selected Guild, otherwise returns False.
def is_user_registered(database_connection: sqlite3.Connection, user_id: int, guild_id: int) -> bool:
    cursor: sqlite3.Cursor = database_connection.cursor()
    cursor.execute("SELECT id FROM registered_users WHERE user_id = ? AND guild_id = ?", (user_id, guild_id))

    if not cursor.fetchone():
        return False

    return True

def register_user_to_database(database_connection: sqlite3.Connection, user_id: int, guild_id: int):
    cursor: sqlite3.Cursor = database_connection.cursor()
    cursor.execute("INSERT INTO registered_users (user_id, guild_id) VALUES (?, ?)", (user_id, guild_id))
    database_connection.commit()


@bot.event
async def on_ready():
    print(f"Support bot logged in as {bot.user}!")


@bot.command(description="Registers the user to the support system.")
async def register(ctx: discord.ApplicationContext, name: discord.SlashCommandOptionType.string):
    # Creating member object.
    member: discord.Member = ctx.guild.get_member(ctx.author.id)

    if is_user_registered(database, ctx.author.id, ctx.guild.id):
        print("User already registered!")
    else:
        register_user_to_database(database, ctx.author.id, ctx.guild.id)
        print("Registering user...")

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
