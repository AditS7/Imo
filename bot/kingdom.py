import os
import json
import logging
import datetime
import discord
from discord.ext import commands, tasks
from discord import app_commands
import bot.config as config
from bot.admin import is_mr_fahrenheit, is_mr_fahrenheit_ctx

logger = logging.getLogger(__name__)

KINGDOM_NUMBER = 2403
KINGDOM_START_DATE = datetime.date(2026, 8, 8)

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "kingdom_settings.json")

# Full timeline of upcoming Kingdom 2403 events
EVENTS = [
    {"date": datetime.date(2026, 9, 21), "name": "Alliance Resource Exchange"},
    {"date": datetime.date(2026, 9, 21), "name": "Generation 2 Heroes"},
    {"date": datetime.date(2026, 9, 30), "name": "First King's Castle Battle"},
    {"date": datetime.date(2026, 10, 1), "name": "Generation 1 Pets — Gray Wolf"},
    {"date": datetime.date(2026, 10, 3), "name": "King's Castle War"},
    {"date": datetime.date(2026, 10, 10), "name": "King's Castle War"},
    {"date": datetime.date(2026, 10, 16), "name": "Age of Truegold begins"},
    {"date": datetime.date(2026, 10, 17), "name": "King's Castle War"},
    {"date": datetime.date(2026, 10, 18), "name": "Generation 2 Pets — Moose, Cheetah, Bison, Lynx"},
    {"date": datetime.date(2026, 10, 20), "name": "First KvK Preparation"},
    {"date": datetime.date(2026, 10, 24), "name": "King's Castle War"},
    {"date": datetime.date(2026, 10, 25), "name": "First KvK Castle Battle"},
    {"date": datetime.date(2026, 10, 27), "name": "First Alliance Brawl"},
    {"date": datetime.date(2026, 11, 23), "name": "Governor Gear Exchange + Generation 3 Heroes + Generation 3 Pets"},
    {"date": datetime.date(2027, 1, 4), "name": "Truegold 5 + Governor Charm Exchange"},
    {"date": datetime.date(2027, 1, 25), "name": "Governor Charm Cap Raised"},
    {"date": datetime.date(2027, 2, 15), "name": "Generation 4 Heroes + Generation 4 Pets"},
    {"date": datetime.date(2027, 3, 15), "name": "War Academy"},
    {"date": datetime.date(2027, 5, 10), "name": "Generation 5 Heroes + Generation 5 Pets"},
    {"date": datetime.date(2027, 6, 21), "name": "Truegold 8"},
    {"date": datetime.date(2027, 8, 2), "name": "Generation 6 Heroes + Generation 6 Pets"},
]

def get_kingdom_channel_id() -> int | None:
    """Returns the channel ID configured for kingdom daily announcements."""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)
                val = data.get("kingdom_channel_id")
                if val:
                    return int(val)
        except Exception as e:
            logger.error(f"Error reading kingdom settings: {e}")
    return getattr(config, "KINGDOM_CHANNEL_ID", None)

def set_kingdom_channel_id(channel_id: int) -> bool:
    """Saves the kingdom announcement channel ID to persistent storage."""
    try:
        data = {}
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r") as f:
                    data = json.load(f)
            except Exception:
                data = {}
        data["kingdom_channel_id"] = channel_id
        with open(SETTINGS_FILE, "w") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving kingdom channel ID: {e}")
        return False

def format_kingdom_age_message(target_date: datetime.date = None) -> str:
    """Formats the daily Kingdom 2403 age and upcoming events report."""
    if target_date is None:
        target_date = datetime.datetime.now(datetime.timezone.utc).date()

    age_days = (target_date - KINGDOM_START_DATE).days

    today_events = [e["name"] for e in EVENTS if e["date"] == target_date]
    upcoming = [e for e in EVENTS if e["date"] > target_date]

    lines = [
        f"👑 **Kingdom {KINGDOM_NUMBER} Daily Update**",
        "",
        f"Our kingdom {KINGDOM_NUMBER} is **{age_days} days** old! 🏰",
    ]

    if today_events:
        lines.append("")
        header = "🎉 **Today's Event:**" if len(today_events) == 1 else "🎉 **Today's Events:**"
        lines.append(header)
        for ev in today_events:
            lines.append(f"• **{ev}** is active today!")

    if upcoming:
        lines.append("")
        lines.append("⏳ **Upcoming Events:**")
        # Display the next 4 upcoming events
        for ev in upcoming[:4]:
            days_left = (ev["date"] - target_date).days
            day_str = "day" if days_left == 1 else "days"
            lines.append(f"• **{ev['name']}** in **{days_left} {day_str}** ({ev['date'].strftime('%d %b %Y')})")
    else:
        lines.append("")
        lines.append("No further scheduled events listed.")

    return "\n".join(lines)

def format_full_schedule(target_date: datetime.date = None) -> str:
    """Formats the full timeline of events for Kingdom 2403."""
    if target_date is None:
        target_date = datetime.datetime.now(datetime.timezone.utc).date()

    age_days = (target_date - KINGDOM_START_DATE).days
    lines = [
        f"📜 **Kingdom {KINGDOM_NUMBER} Complete Timeline**",
        f"Started: **{KINGDOM_START_DATE.strftime('%d %b %Y')}** (Current Age: **{age_days} days**)",
        "",
    ]

    for ev in EVENTS:
        date_str = ev["date"].strftime("%d %b %Y")
        diff = (ev["date"] - target_date).days
        if diff < 0:
            status = f"✅ Finished ({abs(diff)} days ago)"
        elif diff == 0:
            status = "🔥 **TODAY**"
        else:
            status = f"⏳ in {diff} days"
        lines.append(f"`{date_str}` — **{ev['name']}** ({status})")

    return "\n".join(lines)


# UTC Midnight trigger (00:00 UTC)
UTC_MIDNIGHT = datetime.time(hour=0, minute=0, tzinfo=datetime.timezone.utc)

class KingdomCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.last_posted_date: datetime.date | None = None
        self.daily_kingdom_loop.start()

    def cog_unload(self):
        self.daily_kingdom_loop.cancel()

    @tasks.loop(time=UTC_MIDNIGHT)
    async def daily_kingdom_loop(self):
        """Runs every day at UTC 00:00 to post the kingdom age and upcoming events."""
        today_utc = datetime.datetime.now(datetime.timezone.utc).date()
        if self.last_posted_date == today_utc:
            logger.info("Daily kingdom announcement already posted for today.")
            return

        channel_id = get_kingdom_channel_id()
        if not channel_id:
            logger.warning("Kingdom announcement channel is not configured. Skipping daily post.")
            return

        channel = self.bot.get_channel(channel_id)
        if not channel:
            try:
                channel = await self.bot.fetch_channel(channel_id)
            except Exception as e:
                logger.error(f"Failed to fetch kingdom channel {channel_id}: {e}")
                return

        if channel:
            try:
                msg = format_kingdom_age_message(today_utc)
                await channel.send(msg)
                self.last_posted_date = today_utc
                logger.info(f"Posted daily kingdom update to channel #{channel.name} ({channel_id})")
            except Exception as e:
                logger.error(f"Error sending daily kingdom announcement: {e}")

    @daily_kingdom_loop.before_loop
    async def before_daily_kingdom_loop(self):
        await self.bot.wait_until_ready()

    # --- Slash Commands ---

    @app_commands.command(
        name="set_kingdom_channel",
        description="Set the channel where daily Kingdom 2403 updates will be posted at 00:00 UTC."
    )
    @app_commands.default_permissions(administrator=True)
    async def set_kingdom_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        success = set_kingdom_channel_id(channel.id)
        if success:
            await interaction.response.send_message(
                f"✅ Kingdom updates will now be posted daily at **00:00 UTC** in {channel.mention}!",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "❌ Failed to save the kingdom channel setting. Please check bot logs.",
                ephemeral=True
            )

    @app_commands.command(
        name="kingdom_age",
        description="View Kingdom 2403's current age and upcoming events."
    )
    async def kingdom_age(self, interaction: discord.Interaction):
        msg = format_kingdom_age_message()
        await interaction.response.send_message(msg)

    @app_commands.command(
        name="kingdom_schedule",
        description="View the full upcoming event timeline for Kingdom 2403."
    )
    async def kingdom_schedule(self, interaction: discord.Interaction):
        msg = format_full_schedule()
        if len(msg) > 2000:
            # Discord message limit safety
            parts = [msg[i:i+1900] for i in range(0, len(msg), 1900)]
            await interaction.response.send_message(parts[0], ephemeral=True)
            for part in parts[1:]:
                await interaction.followup.send(part, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)

    @app_commands.command(
        name="post_kingdom_age_now",
        description="[Admin] Manually trigger the Kingdom 2403 daily announcement right now."
    )
    @app_commands.default_permissions(administrator=True)
    async def post_kingdom_age_now(self, interaction: discord.Interaction):
        channel_id = get_kingdom_channel_id()
        if not channel_id:
            await interaction.response.send_message(
                "⚠️ No kingdom announcement channel configured! Use `/set_kingdom_channel` first.",
                ephemeral=True
            )
            return

        channel = self.bot.get_channel(channel_id)
        if not channel:
            try:
                channel = await self.bot.fetch_channel(channel_id)
            except Exception as e:
                await interaction.response.send_message(f"❌ Could not find channel {channel_id}: {e}", ephemeral=True)
                return

        try:
            today_utc = datetime.datetime.now(datetime.timezone.utc).date()
            msg = format_kingdom_age_message(today_utc)
            await channel.send(msg)
            await interaction.response.send_message(f"✅ Announcement sent to {channel.mention}!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to send announcement: {e}", ephemeral=True)

    # --- Text Command Fallbacks ---

    @commands.command(name="set_kingdom_channel")
    @commands.has_permissions(administrator=True)
    async def txt_set_kingdom_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        success = set_kingdom_channel_id(channel.id)
        if success:
            await ctx.send(f"✅ Kingdom updates will now be posted daily at **00:00 UTC** in {channel.mention}!")
        else:
            await ctx.send("❌ Failed to save the kingdom channel setting.")

    @commands.command(name="kingdom_age")
    async def txt_kingdom_age(self, ctx: commands.Context):
        msg = format_kingdom_age_message()
        await ctx.send(msg)

    @commands.command(name="kingdom_schedule")
    async def txt_kingdom_schedule(self, ctx: commands.Context):
        msg = format_full_schedule()
        if len(msg) > 2000:
            parts = [msg[i:i+1900] for i in range(0, len(msg), 1900)]
            for part in parts:
                await ctx.send(part)
        else:
            await ctx.send(msg)

    @commands.command(name="post_kingdom_age_now")
    @commands.has_permissions(administrator=True)
    async def txt_post_kingdom_age_now(self, ctx: commands.Context):
        channel_id = get_kingdom_channel_id()
        if not channel_id:
            await ctx.send("⚠️ No kingdom announcement channel configured! Use `!set_kingdom_channel #channel` first.")
            return

        channel = self.bot.get_channel(channel_id)
        if not channel:
            try:
                channel = await self.bot.fetch_channel(channel_id)
            except Exception as e:
                await ctx.send(f"❌ Could not find channel {channel_id}: {e}")
                return

        try:
            today_utc = datetime.datetime.now(datetime.timezone.utc).date()
            msg = format_kingdom_age_message(today_utc)
            await channel.send(msg)
            await ctx.send(f"✅ Announcement sent to {channel.mention}!")
        except Exception as e:
            await ctx.send(f"❌ Failed to send announcement: {e}")

async def setup(bot: commands.Bot):
    await bot.add_cog(KingdomCog(bot))
