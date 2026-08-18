import logging
from groq import AsyncGroq
from bot.config import GROQ_API_KEY, MODEL_NAME, TEMPERATURE, MAX_OUTPUT_TOKENS
from bot.personality import SYSTEM_INSTRUCTION

logger = logging.getLogger(__name__)

# Initialize the Groq client
client = None
if GROQ_API_KEY:
    try:
        client = AsyncGroq(api_key=GROQ_API_KEY)
    except Exception as e:
        logger.error(f"Failed to initialize Groq client: {e}")

async def generate_response(prompt: str, history: list = None) -> str:
    """
    Generates a response from Groq given the prompt and conversation history.
    """
    if not client:
        logger.error("Groq client is not initialized.")
        return "my brain just lagged 💀 give me a sec"
    
    try:
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
        return chat_completion.choices[0].message.content
    except Exception as e:
        logger.error(f"Groq API Error: {e}")
        return "my brain just lagged 💀 give me a sec"
