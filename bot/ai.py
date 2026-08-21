import os
import logging
from openai import AsyncOpenAI
from bot.config import MODEL_NAME, TEMPERATURE, MAX_OUTPUT_TOKENS
from bot.personality import SYSTEM_INSTRUCTION

logger = logging.getLogger(__name__)

async def generate_response(prompt: str, history: list = None) -> str:
    """
    Generates a response using the OpenAI SDK (OpenRouter)
    """
    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    
    if not api_key:
        logger.error("API Key is missing from the OS environment variables!")
        return "my brain just lagged 💀 (API Key missing in Railway)"

    try:
        client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        
        messages = [
            {"role": "system", "content": SYSTEM_INSTRUCTION}
        ]
        
        if history:
            for msg in history:
                role = "assistant" if msg["role"] == "model" else "user"
                messages.append({"role": role, "content": msg["content"]})
        
        messages.append({"role": "user", "content": prompt})
        
        # Initial call
        chat_completion = await client.chat.completions.create(
            messages=messages,
            model=MODEL_NAME,
            temperature=TEMPERATURE,
            max_tokens=MAX_OUTPUT_TOKENS
        )
        
        response_message = chat_completion.choices[0].message
            
        content = response_message.content
        return content.strip() if content else ""
            
    except Exception as e:
        logger.error(f"API Error: {e}")
        return f"my brain just lagged 💀 (Error: {e})"
