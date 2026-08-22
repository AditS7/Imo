import discord
from discord.ext import commands
from discord import app_commands
import bot.config as config
from bot.memory import clear_history

def is_mr_fahrenheit():
    def predicate(interaction: discord.Interaction) -> bool:
        # Match by specific username or display name as requested for Mr. Fahrenheit
        name_match = "fahrenheit" in interaction.user.name.lower() or "fahrenheit" in interaction.user.display_name.lower()
        owner_match = interaction.guild and interaction.user.id == interaction.guild.owner_id
        return name_match or owner_match
    return app_commands.check(predicate)

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

    @app_commands.command(name="kick", description="[Mr. Fahrenheit Only] Kick a member from the server.")
    @is_mr_fahrenheit()
    async def kick_member(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        try:
            await member.kick(reason=reason)
            await interaction.response.send_message(f"Done, boss. {member.mention} has been kicked. Reason: {reason}")
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to kick this member. Make sure my role is higher than theirs!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)

    @app_commands.command(name="ban", description="[Mr. Fahrenheit Only] Ban a member from the server.")
    @is_mr_fahrenheit()
    async def ban_member(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        try:
            await member.ban(reason=reason)
            await interaction.response.send_message(f"Done, boss. {member.mention} has been banned. Reason: {reason}")
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to ban this member. Make sure my role is higher than theirs!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)

    @app_commands.command(name="give_role", description="[Mr. Fahrenheit Only] Give a role to a member.")
    @is_mr_fahrenheit()
    async def give_role(self, interaction: discord.Interaction, member: discord.Member, role: discord.Role):
        try:
            await member.add_roles(role)
            await interaction.response.send_message(f"Done, boss. Gave {role.name} to {member.mention}.")
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to manage this role. Make sure my role is higher than the role I'm trying to assign!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)

    @app_commands.command(name="remove_role", description="[Mr. Fahrenheit Only] Remove a role from a member.")
    @is_mr_fahrenheit()
    async def remove_role(self, interaction: discord.Interaction, member: discord.Member, role: discord.Role):
        try:
            await member.remove_roles(role)
            await interaction.response.send_message(f"Done, boss. Removed {role.name} from {member.mention}.")
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to manage this role.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)

    @kick_member.error
    @ban_member.error
    @give_role.error
    @remove_role.error
    async def mr_fahrenheit_only_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CheckFailure):
            await interaction.response.send_message("Nice try! 🚫 Only Mr. Fahrenheit is allowed to give me these orders.", ephemeral=True)
        else:
            await interaction.response.send_message(f"An error occurred: {error}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(AdminCog(bot))
