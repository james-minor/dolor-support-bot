import json
import os
import sqlite3
import sys
import typing
import discord

import dm_support.database
import dm_support.utils
import dm_support.messaging

class SupportBot(discord.Bot):

    def __init__(self):
        super().__init__(intents=self.get_intents())

        try:
            self.json_config: typing.Dict = json.load(open(os.getenv("JSON_CONFIG_PATH")))
            print(f"[{dm_support.utils.get_date_time()}] Successfully loaded JSON config!")
        except FileNotFoundError:
            print(f"[{dm_support.utils.get_date_time()}] Failed to load JSON config, aborting startup...")
            sys.exit(1)

        try:
            self.connection: sqlite3.Connection = sqlite3.connect(os.getenv("DATABASE_PATH"))
            print(f"[{dm_support.utils.get_date_time()}] Successfully opened SQLite connection!")
            dm_support.database.initialize(self.connection)
            print(f"[{dm_support.utils.get_date_time()}] Successfully initialized database!")
        except sqlite3.Error:
            print(f"[{dm_support.utils.get_date_time()}] Failed to connect and initialize database, aborting startup...")
            sys.exit(1)


    @staticmethod
    def get_intents() -> discord.Intents:
        return discord.Intents.all()


    async def on_ready(self):
        print(f"[{dm_support.utils.get_date_time()}] Support Bot successfully logged in as {self.user}!")


    async def on_guild_join(self, guild: discord.Guild):
        # Creating the support role (if it did not already exist).
        await dm_support.utils.create_role(guild, self.json_config["STAFF_ROLE"])

        # Creating the generic registered user role (if it did not already exist).
        student_role = await dm_support.utils.create_role(guild, self.json_config["USER_ROLE"])
        if student_role:
            await student_role.edit(color=discord.Color(0x4499d5))


    async def on_member_join(self, member: discord.Member):
        await dm_support.messaging.send_register_direct_message(member._user, member.guild, register_callback=self.register_user)


    async def register_user(self, interaction: discord.Interaction, name: str, guild_id: int):
        # Getting guild object from guild ID.
        guild: discord.Guild = self.get_guild(guild_id)

        # Getting local member object from interaction.
        member: discord.Member = guild.get_member(interaction.user.id)

        # Setting member nickname.
        try:
            await member.edit(nick=name)
        except BaseException:
            await interaction.followup.send("Could not change your nickname (does not work for admins).", ephemeral=True)

        # Updating existing support channel name.
        if dm_support.database.is_user_registered(self.connection, interaction.user.id, guild.id):
            print(f"User '{interaction.user}' already registered.")

            # Getting the support channel id for the user.
            support_channel_id: int = dm_support.database.get_support_channel_id(self.connection, interaction.user.id, guild.id)

            # Updating the existing support channel.
            if discord.utils.get(guild.text_channels, id=support_channel_id):
                print(f"Support channel already exists for '{interaction.user}', updating existing support channel name.")
                await self.get_channel(support_channel_id).edit(name=dm_support.utils.generate_channel_name(name))
                await interaction.followup.send("Successfully updated your support channel name.", ephemeral=True)

            # Creating a new support channel (in the event the existing channel got deleted).
            else:
                print(f"Support channel does not exist for '{interaction.user}' (probable accidental deletion), creating new support channel.")
                new_channel: discord.TextChannel = await dm_support.utils.create_support_channel(interaction, guild, name, self)
                dm_support.database.update_support_channel_id(self.connection, interaction.user.id, guild.id, new_channel.id)
                await interaction.followup.send("Successfully recreated your support channel.", ephemeral=True)

            return

        # Creating new member support channel.
        new_support_channel = await dm_support.utils.create_support_channel(interaction, guild, name, self)
        print(f"Successfully created support channel '{new_support_channel.name}'.")

        # Registering new user in database.
        dm_support.database.register_user(self.connection, interaction.user.id, guild.id, new_support_channel.id)

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
