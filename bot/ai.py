import os
import logging
import json
import httpx
import re
from datetime import datetime
from openai import AsyncOpenAI, RateLimitError
from bot.config import MODEL_NAME, TEMPERATURE, MAX_OUTPUT_TOKENS
from bot.personality import SYSTEM_INSTRUCTION

logger = logging.getLogger(__name__)

async def search_web(query: str) -> str:
    """Searches the web using Tavily API for up-to-date context."""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return "Error: TAVILY_API_KEY is not set in the environment variables."
    
    # Use advanced depth and more results to get the most recent and accurate information
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": api_key,
                    "query": query,
                    "search_depth": "basic",
                    "max_results": 3
                },
                timeout=8.0
            )
            response.raise_for_status()
            data = response.json()
            results = data.get("results", [])
            context = []
            for res in results:
                context.append(f"Source: {res.get('url')}\nContent: {res.get('content')}")
            
            full_context = "\n\n".join(context) if context else "No relevant results found."
            # Truncate to save tokens and prevent rate limit errors on the second request
            if len(full_context) > 2500:
                full_context = full_context[:2500] + "... [TRUNCATED FOR LENGTH]"
            return full_context
        except Exception as e:
            logger.error(f"Tavily search failed: {e}")
            return f"Search failed: {e}"

async def generate_response(prompt: str, history: list = None) -> str:
    """
    Generates a response using the OpenAI SDK (OpenRouter)
    """
    # Check for Groq API key first, otherwise default to OpenRouter
    if os.getenv("GROQ_API_KEY"):
        api_key = os.getenv("GROQ_API_KEY")
        base_url = "https://api.groq.com/openai/v1"
    else:
        api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    
    if not api_key:
        logger.error("API Key is missing from the OS environment variables!")
        return "my brain just lagged 💀 (API Key missing in Railway)"

    try:
        client = AsyncOpenAI(api_key=api_key, base_url=base_url, max_retries=0)
        
        current_time = datetime.now().strftime("%B %d, %Y")
        dynamic_system_prompt = f"{SYSTEM_INSTRUCTION}\n\n[SYSTEM NOTE: The current date is {current_time}. If the user asks for the 'latest' information, append the current month/year to your web search queries (e.g. 'Kingshot meta {current_time}') to ensure you fetch the most recent news.]"

        messages = [
            {"role": "system", "content": dynamic_system_prompt}
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
                    "description": "Searches the web for up-to-date information, news, or facts about a topic you are unsure about.",
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
                        args_str = tool_call.function.arguments
                        args = json.loads(args_str)
                        query = args.get("query", "")
                    except Exception as e:
                        logger.error(f"Tool call error: {e}")
                        # Fallback regex extraction
                        match = re.search(r'"query"\s*:\s*"([^"]+)"', args_str)
                        query = match.group(1) if match else "Kingshot Century Games"
                    
                    logger.info(f"AI is searching the web for: {query}")
                    search_results = await search_web(query)
                    
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
        if content:
            # Strip out reasoning blocks like <think>...</think>
            content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
            # Strip out hallucinated tool_call blocks (including unclosed ones at the end)
            content = re.sub(r'<tool_call>.*?(?:</tool_call>|$)', '', content, flags=re.DOTALL)
            content = content.strip()
        
        return content if content else ""
            
    except RateLimitError as e:
        logger.error(f"Rate Limit Error: {e}")
        return ""
    except Exception as e:
        logger.error(f"API Error: {e}")
        return ""
