import os
import logging
import json
import httpx
from openai import AsyncOpenAI
from bot.config import MODEL_NAME, TEMPERATURE, MAX_OUTPUT_TOKENS
from bot.personality import SYSTEM_INSTRUCTION

logger = logging.getLogger(__name__)

async def search_web(query: str) -> str:
    """Searches the web using Tavily API for up-to-date context."""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return "Error: TAVILY_API_KEY is not set in the environment variables."
    
    # Use a faster timeout and slightly fewer results for speed
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": api_key,
                    "query": query,
                    "search_depth": "basic",
                    "max_results": 2
                },
                timeout=5.0
            )
            response.raise_for_status()
            data = response.json()
            results = data.get("results", [])
            context = []
            for res in results:
                context.append(f"Source: {res.get('url')}\nContent: {res.get('content')}")
            return "\n\n".join(context) if context else "No relevant results found."
        except Exception as e:
            logger.error(f"Tavily search failed: {e}")
            return f"Search failed: {e}"

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
        
        # Define the Search Tool for the AI
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_web",
                    "description": "Searches the web for up-to-date information, news, or facts about a topic. You MUST use this tool WHENEVER the user asks a question about the game 'Kingshot' (Century Games), its meta, heroes, or mechanics. Do not guess Kingshot info, always search first.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query to look up on the internet."
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
        ]
        
        # Initial call
        chat_completion = await client.chat.completions.create(
            messages=messages,
            model=MODEL_NAME,
            temperature=TEMPERATURE,
            max_tokens=MAX_OUTPUT_TOKENS,
            tools=tools,
            tool_choice="auto"
        )
        
        response_message = chat_completion.choices[0].message

        # Handle tool calls
        if response_message.tool_calls:
            # Append the assistant's message
            messages.append(response_message.model_dump(exclude_unset=True))
            
            for tool_call in response_message.tool_calls:
                if tool_call.function.name == "search_web":
                    try:
                        args = json.loads(tool_call.function.arguments)
                        query = args.get("query", "")
                        logger.info(f"AI is searching the web for: {query}")
                        search_results = await search_web(query)
                    except Exception as e:
                        logger.error(f"Tool call error: {e}")
                        search_results = f"Error executing search: {e}"
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_call.function.name,
                        "content": search_results
                    })
            
            # Second call with the results
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
