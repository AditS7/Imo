import os
import logging
import json
import re
import httpx
from groq import AsyncGroq
from bot.config import MODEL_NAME, TEMPERATURE, MAX_OUTPUT_TOKENS
from bot.personality import SYSTEM_INSTRUCTION

logger = logging.getLogger(__name__)

async def search_web(query: str) -> str:
    """Searches the web using Tavily API for up-to-date context."""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return "Error: TAVILY_API_KEY is not set in the environment variables."
    
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
                timeout=10.0
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
    Generates a response from Groq given the prompt and conversation history.
    Includes Tool Calling logic to allow the AI to search the web.
    """
    api_key = os.getenv("GROQ_API_KEY")
    
    if not api_key:
        logger.error("GROQ_API_KEY is missing from the OS environment variables!")
        return "my brain just lagged 💀 (API Key missing in Railway)"

    try:
        client = AsyncGroq(api_key=api_key)
        
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
                    "description": "Searches the web for up-to-date information, news, or facts about a topic. Use this when the user asks about real-world events, current meta, or things you aren't certain about.",
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
        
        # Initial call - let the AI decide if it wants to search
        chat_completion = await client.chat.completions.create(
            messages=messages,
            model=MODEL_NAME,
            temperature=TEMPERATURE,
            max_tokens=MAX_OUTPUT_TOKENS,
            tools=tools,
            tool_choice="auto"
        )
        
        response_message = chat_completion.choices[0].message
        raw_content = response_message.content or ""

        # Did the AI decide to call a tool using standard JSON?
        if response_message.tool_calls:
            messages.append(response_message)
            
            for tool_call in response_message.tool_calls:
                if tool_call.function.name == "search_web":
                    try:
                        args = json.loads(tool_call.function.arguments)
                        query = args.get("query", "")
                        logger.info(f"AI is searching the web (JSON) for: {query}")
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
            
            chat_completion = await client.chat.completions.create(
                messages=messages,
                model=MODEL_NAME,
                temperature=TEMPERATURE,
                max_tokens=MAX_OUTPUT_TOKENS
            )
            response_message = chat_completion.choices[0].message
            raw_content = response_message.content or ""
            
        # Fallback: Did Qwen leak the tool call into the raw content as XML/text?
        elif "<tool_call>" in raw_content or "search_web" in raw_content:
            # Try to extract the query from the leaked XML
            match = re.search(r'query>?(?:\s*|["\']?)([^<"\'\n]+)', raw_content, flags=re.IGNORECASE)
            if match:
                query = match.group(1).strip()
                logger.info(f"AI is searching the web (XML fallback) for: {query}")
                search_results = await search_web(query)
                
                messages.append({"role": "assistant", "content": raw_content})
                messages.append({"role": "user", "content": f"Here are the web search results for '{query}':\n\n{search_results}\n\nNow, ignore your previous XML block and give me a normal conversational response."})
                
                chat_completion = await client.chat.completions.create(
                    messages=messages,
                    model=MODEL_NAME,
                    temperature=TEMPERATURE,
                    max_tokens=MAX_OUTPUT_TOKENS
                )
                response_message = chat_completion.choices[0].message
                raw_content = response_message.content or ""

        # Strip <think> tags from the final content
        clean_content = re.sub(r'<think>.*?(?:</think>|$)', '', raw_content, flags=re.DOTALL).strip()
        
        return clean_content
    except Exception as e:
        logger.error(f"Groq API Error: {e}")
        return f"my brain just lagged 💀 (Error: {e})"
