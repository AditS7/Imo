import discord
from discord.ext import commands
from discord import app_commands
import bot.config as config
from bot.memory import clear_history

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="status", description="Check Imo's status and latency.")
    async def status(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(f"I'm alive! Latency: {latency}ms", ephemeral=True)

    @app_commands.command(name="settings", description="View current settings.")
    @app_commands.default_permissions(administrator=True)
    async def settings(self, interaction: discord.Interaction):
        msg = (
            f"**Imo Settings**\n"
            f"Spontaneous Replies: {'Enabled' if config.SPONTANEOUS_REPLY_ENABLED else 'Disabled'}\n"
            f"Spontaneous Chance: {config.SPONTANEOUS_REPLY_CHANCE * 100}%\n"
            f"Model: {config.MODEL_NAME}"
        )
        await interaction.response.send_message(msg, ephemeral=True)

    @app_commands.command(name="toggle_spontaneous", description="Toggle spontaneous replies on or off.")
    @app_commands.default_permissions(administrator=True)
    async def toggle_spontaneous(self, interaction: discord.Interaction):
        config.SPONTANEOUS_REPLY_ENABLED = not config.SPONTANEOUS_REPLY_ENABLED
        state = "enabled" if config.SPONTANEOUS_REPLY_ENABLED else "disabled"
        await interaction.response.send_message(f"Spontaneous replies are now {state}.", ephemeral=True)
    
    @app_commands.command(name="clear_memory", description="Clears my short-term memory for this channel.")
    @app_commands.default_permissions(administrator=True)
    async def clear_channel_memory(self, interaction: discord.Interaction):
        clear_history(interaction.channel_id)
        await interaction.response.send_message("Channel memory cleared. Who are you people again?", ephemeral=False)

async def setup(bot):
    await bot.add_cog(AdminCog(bot))
