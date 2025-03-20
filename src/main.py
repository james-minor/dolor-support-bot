# TODO: prevent multiple registrations (utilize a simple sqlite db).

# TODO: give user role to registered user, role allows for viewing stuff.
# TODO: have default text placed into support channel.

import discord
import os
import dotenv

# Initializing environment.
dotenv.load_dotenv()

# Initializing the Discord bot.
intents: discord.Intents = discord.Intents.all()

bot = discord.Bot(intents=intents)


@bot.event
async def on_ready():
    print(f"Support bot logged in as {bot.user}!")


@bot.command(description="Registers the user to the support system.")
async def register(ctx: discord.ApplicationContext, name: discord.SlashCommandOptionType.string):
    # Creating member object.
    member: discord.Member = ctx.guild.get_member(ctx.author.id)

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
    if not discord.utils.get(ctx.guild.roles, name="Support Staff"):
        support_role: discord.Role = await ctx.guild.create_role(name="Support Staff")
    else:
        support_role: discord.Role = discord.utils.get(ctx.guild.roles, name="Support Staff")

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


bot.run(str(os.getenv("DISCORD_API_TOKEN")))
