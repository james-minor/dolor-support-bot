import discord

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


def is_valid_name_parameter(name: str) -> bool:
    if len(name) < 1 or len(name) > 35:
        return False
    if not name.replace(" ", "").isalpha():
        return False
    return True