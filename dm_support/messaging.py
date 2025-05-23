import typing

import discord

import dm_support.utils

class PersistentRegisterView(discord.ui.View):
    def __init__(self, register_callback: typing.Callable):
        super().__init__(timeout=None)

        self.add_item(RegisterButton(register_callback))


class RegisterButton(discord.ui.Button):
    def __init__(self, register_callback: typing.Callable):
        super().__init__(label="Register", style=discord.ButtonStyle.primary, custom_id="register_button")
        self.register_callback = register_callback

    async def callback(self, interaction: discord.Interaction):
        register_modal = RegisterModal(interaction.guild_id, self.register_callback)
        await interaction.response.send_modal(register_modal)


class RegisterModal(discord.ui.Modal):
    def __init__(self, guild_id: int, register_callback: typing.Callable):
        super().__init__(title="Register")

        self.name_input = discord.ui.InputText(label="Enter your name:", style=discord.InputTextStyle.short)
        self.add_item(self.name_input)

        self.guild_id: int = guild_id
        self.register_callback = register_callback


    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        # Name parameter validation.
        if not dm_support.utils.is_valid_name_parameter(self.name_input.value):
            await interaction.followup.send("Names must be between 1 and 35 characters long.", ephemeral=True)
            await interaction.followup.send("Names may only contain letters.", ephemeral=True)
            return

        await self.register_callback(interaction, self.name_input.value, self.guild_id)


async def send_register_button(message: str, guild_id: int, channel: discord.DMChannel, register_callback: typing.Callable):
    register_button = discord.ui.Button(label="Register", style=discord.ButtonStyle.primary)

    async def register_button_callback(interaction: discord.Interaction):
        register_modal = RegisterModal(guild_id, register_callback)
        await interaction.response.send_modal(register_modal)

    register_button.callback = register_button_callback

    view = discord.ui.View()
    view.add_item(register_button)

    await channel.send(content=f"{message}", view=view)
