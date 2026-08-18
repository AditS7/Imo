import discord
import random
import time
import logging
from bot.memory import add_message, get_history
from bot.ai import generate_response
import bot.config as config

logger = logging.getLogger(__name__)

last_spontaneous_time = 0

async def handle_message(bot, message: discord.Message):
    global last_spontaneous_time

    # Ignore messages from bots (including ourselves)
    if message.author.bot:
        return

    # Ignore empty messages
    if not message.content or not message.content.strip():
        return

    content_lower = message.content.lower()
    is_direct_call = False

    # Check if mentioned
    if bot.user in message.mentions:
        is_direct_call = True
    
    # Check if addressed by name (contains standalone word "imo")
    # Using word boundaries to avoid matching "imodium" or "imovie"
    import re
    if re.search(r'\bimo\b', content_lower):
        is_direct_call = True

    # Check if it's a direct reply to Imo
    if message.reference and message.reference.cached_message:
        if message.reference.cached_message.author == bot.user:
            is_direct_call = True

    channel_id = message.channel.id
    user_name = message.author.display_name

    # Check spontaneous conditions if not directly called
    is_spontaneous = False
    if not is_direct_call and config.SPONTANEOUS_REPLY_ENABLED:
        current_time = time.time()
        if current_time - last_spontaneous_time > config.SPONTANEOUS_COOLDOWN_SECONDS:
            if random.random() < config.SPONTANEOUS_REPLY_CHANCE:
                is_spontaneous = True
                last_spontaneous_time = current_time

    if is_direct_call or is_spontaneous:
        # Show typing indicator while generating
        async with message.channel.typing():
            # Get history
            history = get_history(channel_id)
            
            prompt = f"{user_name}: {message.content}"
            if is_spontaneous:
                logger.info(f"Spontaneous response triggered in {message.channel.name}")

            # Generate response
            response = await generate_response(prompt, history)

            if response:
                # Add user message to memory
                add_message(channel_id, user_name, message.content, is_bot=False)
                
                # We format Imo's response
                clean_response = response.strip()
                
                if not clean_response:
                    clean_response = "*just stares blankly* (I overthought that and forgot to speak 💀)"

                # Send the response (replying to the user if directly called, or just sending if spontaneous)
                try:
                    # Discord has a strict 2000 character limit per message
                    if len(clean_response) > 2000:
                        # Split into chunks of 2000 chars
                        chunks = [clean_response[i:i+1999] for i in range(0, len(clean_response), 1999)]
                        for i, chunk in enumerate(chunks):
                            if i == 0 and is_direct_call:
                                await message.reply(chunk, mention_author=False)
                            else:
                                await message.channel.send(chunk)
                    else:
                        if is_direct_call:
                            await message.reply(clean_response, mention_author=False)
                        else:
                            await message.channel.send(clean_response)
                        
                    # Add Imo's response to memory
                    add_message(channel_id, "Imo", clean_response, is_bot=True)
                    logger.info("Response sent.")
                except discord.HTTPException as e:
                    logger.error(f"Failed to send message: {e}")
    else:
        # Just record it in memory for context later
        add_message(channel_id, user_name, message.content, is_bot=False)
