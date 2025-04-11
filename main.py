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

# Starting discord bot.
bot.run(str(os.getenv("DISCORD_API_TOKEN")))

# TODO:
# - move initial DM -> Welcome channel?
# - numbered categories for tickets
# - run this 24/7 in background AWS using some sort of script