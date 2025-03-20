# TODO: ephemeral responses
# TODO: logging
# TODO: prevent multiple registrations (utilize a simple sqlite db).

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
    # Registering the member.
    try:
        # Setting member nickname.
        member: discord.Member = ctx.guild.get_member(ctx.author.id)
        # TODO: uncomment this, doing it for testing
        #await member.edit(nick=name)

        # Creating support channel category (if it did not already exist).
        category = discord.utils.get(ctx.guild.categories, name="support")
        if not category:
            category = await ctx.guild.create_category("support")

        # Creating the support role (if it did not already exist).
        if not discord.utils.get(ctx.guild.roles, name="Support Staff"):
            support_role: discord.Role = await ctx.guild.create_role(name="Support Staff")
        else:
            support_role: discord.Role = discord.utils.get(ctx.guild.roles, name="Support Staff")

        # Creating member support channel.
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            support_role: discord.PermissionOverwrite(read_messages=True),
            member: discord.PermissionOverwrite(read_messages=True),
        }

        new_channel_name: str = "-".join(name.lower().split()) + "-support"
        new_channel: discord.TextChannel = await ctx.guild.create_text_channel(name=new_channel_name, category=category, overwrites=overwrites)


        await ctx.respond("Successfully registered you to the support system!")
    except BaseException:
        await ctx.respond("Could not register you to the support system (does not work for admins).")


bot.run(str(os.getenv("DISCORD_API_TOKEN")))