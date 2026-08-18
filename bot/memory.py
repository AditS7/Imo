from collections import deque
from bot.config import MAX_HISTORY_MESSAGES

# A dictionary to store recent messages for each channel.
# Format: { channel_id: deque([{ "role": "user", "content": "..." }, ...]) }
channel_memory = {}

def add_message(channel_id: int, user_name: str, content: str, is_bot: bool = False):
    """
    Adds a message to the channel's short-term memory.
    """
    if channel_id not in channel_memory:
        channel_memory[channel_id] = deque(maxlen=MAX_HISTORY_MESSAGES)
    
    # We format the content so the model knows who said what
    formatted_content = f"{user_name}: {content}"
    role = "model" if is_bot else "user"
    
    channel_memory[channel_id].append({"role": role, "content": formatted_content})

def get_history(channel_id: int) -> list:
    """
    Returns the recent message history for a channel.
    """
    if channel_id in channel_memory:
        return list(channel_memory[channel_id])
    return []

def clear_history(channel_id: int):
    """
    Clears the history for a channel.
    """
    if channel_id in channel_memory:
        channel_memory[channel_id].clear()
