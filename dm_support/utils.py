import discord
import datetime

import dm_support.support_bot


# Creates and returns a generated support ticket channel name.
def generate_channel_name(name: str) -> str:
    return "ticket-" + "-".join(name.lower().split())


# Attempts to create a user role in a selected guild. If the role already exists, returns None.
# Otherwise, creates the role and returns the role object.
async def create_role(guild: discord.Guild, role_name: str) -> discord.Role | None:
    if not discord.utils.get(guild.roles, name=role_name):
        new_role: discord.Role = await guild.create_role(name=role_name)
        print(f"Successfully created role '{role_name}'.")
        return new_role

    return None


async def create_support_channel(interaction: discord.Interaction, guild: discord.Guild, name: str, bot: dm_support.support_bot.SupportBot) -> discord.TextChannel:
    # Creating support channel category (if it did not already exist).
    category = discord.utils.get(guild.categories, name=bot.json_config["TICKET_CATEGORY"])
    if not category:
        category = await guild.create_category(bot.json_config["TICKET_CATEGORY"])

    # Creating role overrides to make member support channel private.
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        discord.utils.get(guild.roles, name=bot.json_config["STAFF_ROLE"]): discord.PermissionOverwrite(read_messages=True),
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
    await new_channel.send(content=bot.json_config["NEW_TICKET_TEXT"])

    return new_channel


def is_valid_name_parameter(name: str) -> bool:
    if len(name) < 1 or len(name) > 35:
        return False
    if not name.replace(" ", "").isalpha():
        return False
    return True


def get_date_time() -> str:
    return datetime.datetime.now().replace(microsecond=0).isoformat()