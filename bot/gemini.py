from google import genai
from google.genai import types
from bot.config import GEMINI_API_KEY, MODEL_NAME, TEMPERATURE, MAX_OUTPUT_TOKENS
from bot.personality import SYSTEM_INSTRUCTION
import logging

logger = logging.getLogger(__name__)

# Initialize the Gemini client
client = None
if GEMINI_API_KEY:
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        logger.error(f"Failed to initialize Gemini client: {e}")

async def generate_response(prompt: str, history: list = None) -> str:
    """
    Generates a response from Gemini given the prompt and conversation history.
    """
    if not client:
        logger.error("Gemini client is not initialized.")
        return "my brain just lagged 💀 give me a sec"

    try:
        # Convert history format to the google.genai Content format if needed,
        # but the simplest way to inject Discord context with multiple users
        # is often to pass the history as a single block of text or properly structured contents.
        
        contents = []
        if history:
            for msg in history:
                contents.append(
                    types.Content(
                        role=msg["role"],
                        parts=[types.Part.from_text(text=msg["content"])]
                    )
                )
        
        # Add the current prompt
        contents.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=prompt)]
            )
        )

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=TEMPERATURE,
                max_output_tokens=MAX_OUTPUT_TOKENS,
            )
        )
        return response.text
    except Exception as e:
        logger.error(f"Gemini API Error: {e}")
        return "my brain just lagged 💀 give me a sec"
