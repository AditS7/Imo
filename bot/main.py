import discord
from discord.ext import commands
import logging
from bot.config import DISCORD_TOKEN
from bot.message_handler import handle_message

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

class ImoBot(commands.Bot):
    def __init__(self):
        # Intents are required to read messages and mentions
        intents = discord.Intents.default()
        intents.message_content = True  # Crucial for reading normal text messages
        intents.guilds = True
        intents.members = True  # Added to track member joins

        super().__init__(
            command_prefix=commands.when_mentioned_or("!", "?"),
            intents=intents,
            help_command=None  # Disable default help command
        )

    async def setup_hook(self):
        """
        Executed when the bot is setting up.
        Load cogs (slash commands) and sync the command tree.
        """
        # Load extensions
        await self.load_extension("bot.admin")
        await self.load_extension("bot.kingdom")
        
        # Sync slash commands with Discord
        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} command(s).")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")

    async def on_ready(self):
        logger.info(f"Imo started. Logged in as {self.user} (ID: {self.user.id})")
        logger.info("Connected to Discord")
        
        # Set status
        await self.change_presence(activity=discord.Game(name="hanging out"))

    async def on_member_join(self, member: discord.Member):
        logger.info(f"New member joined: {member.name} in {member.guild.name}")
        
        # Send welcome message to the specific General channel
        welcome_channel_id = 1537882198454042666
        channel = member.guild.get_channel(welcome_channel_id)
        
        if not channel:
            logger.error(f"Could not find the welcome channel with ID {welcome_channel_id}")
            return
                    
        if channel:
            from bot.ai import generate_response
            prompt = f"A new member named '{member.name}' just joined the 'Immortals' server! Give them a short, friendly, and casual welcome message."
            
            async with channel.typing():
                response = await generate_response(prompt, [])
                if response:
                    clean_response = response.strip()
                    try:
                        await channel.send(f"Welcome {member.mention}! {clean_response}")
                    except discord.HTTPException as e:
                        logger.error(f"Failed to send welcome message: {e}")

    async def on_message(self, message: discord.Message):
        # Allow standard @Imo <command> prefix commands to process first
        ctx = await self.get_context(message)
        if ctx.valid:
            await self.invoke(ctx)
            return # Skip AI response since this was a real admin command!
            
        # Handle natural conversation for everything else
        await handle_message(self, message)

def main():
    if not DISCORD_TOKEN:
        logger.error("DISCORD_TOKEN is not set in environment variables.")
        return

    bot = ImoBot()
    bot.run(DISCORD_TOKEN)

if __name__ == "__main__":
    main()
