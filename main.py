import sys
import discord
import os
import dotenv

import dm_support.database
import dm_support.utils
import dm_support.messaging
import dm_support.support_bot

# Runner guard.
if __name__ != "__main__":
    print("Not main process, aborting...")
    sys.exit(1)

# Initializing environment.
dotenv.load_dotenv()

# Initializing the Discord bot.
bot = dm_support.support_bot.SupportBot()

# Defining bot commands.
@bot.command(description="Resends the registration Direct Message.", dm_support=False)
async def resend_register_invite(ctx: discord.ApplicationContext):
    await dm_support.messaging.send_register_direct_message(ctx.user, ctx.guild, register_callback=bot.register_user)

# Starting discord bot.
bot.run(str(os.getenv("DISCORD_API_TOKEN")))
