import os
import logging
from groq import AsyncGroq
from bot.config import MODEL_NAME, TEMPERATURE, MAX_OUTPUT_TOKENS
from bot.personality import SYSTEM_INSTRUCTION

logger = logging.getLogger(__name__)

async def generate_response(prompt: str, history: list = None) -> str:
    """
    Generates a response from Groq given the prompt and conversation history.
    """
    # Grab the key directly from the environment exactly when needed
    api_key = os.getenv("GROQ_API_KEY")
    
    if not api_key:
        logger.error("GROQ_API_KEY is missing from the OS environment variables!")
        return "my brain just lagged 💀 (API Key missing in Railway)"

    try:
        # Initialize client here to prevent startup race conditions
        client = AsyncGroq(api_key=api_key)
        
        messages = [
            {"role": "system", "content": SYSTEM_INSTRUCTION}
        ]
        
        if history:
            for msg in history:
                # Memory saves bot messages as "model". Groq uses "assistant".
                role = "assistant" if msg["role"] == "model" else "user"
                messages.append({"role": role, "content": msg["content"]})
        
        # Add the current user prompt
        messages.append({"role": "user", "content": prompt})
        
        chat_completion = await client.chat.completions.create(
            messages=messages,
            model=MODEL_NAME,
            temperature=TEMPERATURE,
            max_tokens=MAX_OUTPUT_TOKENS,
        )
        
        # Qwen models often output their reasoning process inside <think> tags.
        # We need to strip these tags out so they don't show up in Discord.
        raw_content = chat_completion.choices[0].message.content
        import re
        clean_content = re.sub(r'<think>.*?(?:</think>|$)', '', raw_content, flags=re.DOTALL).strip()
        
        return clean_content
    except Exception as e:
        logger.error(f"Groq API Error: {e}")
        return f"my brain just lagged 💀 (Error: {e})"
