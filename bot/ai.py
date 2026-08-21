import os
import logging
import json
import httpx
import re
from openai import AsyncOpenAI, RateLimitError, APIStatusError
from bot.config import MODEL_NAME, FALLBACK_MODELS, TEMPERATURE, MAX_OUTPUT_TOKENS
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
        
        models_to_try = [MODEL_NAME] + FALLBACK_MODELS
        
        for idx, current_model in enumerate(models_to_try):
            try:
                # Initial call
                chat_completion = await client.chat.completions.create(
                    messages=messages,
                    model=current_model,
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
                        logger.info(f"AI requested tool: {tool_call.function.name}")
                        if tool_call.function.name == "search_web":
                            try:
                                args_str = tool_call.function.arguments
                                query = ""
                                try:
                                    args = json.loads(args_str)
                                    query = args.get("query", "")
                                except json.JSONDecodeError as json_err:
                                    logger.error(f"Tool call JSON error: {json_err} - Raw args: {args_str}")
                                    # Fallback 1: Extract using regex if JSON is malformed
                                    import re
                                    match = re.search(r'"query"\s*:\s*"([^"]+)"', args_str)
                                    if match:
                                        query = match.group(1)
                                    else:
                                        # Fallback 2: relaxed regex
                                        match2 = re.search(r'query.*?[:=]\s*(?:["\']?)([^"\'\}]+)', args_str)
                                        if match2:
                                            query = match2.group(1).strip()
                                        else:
                                            # Absolute fallback, just search the user's prompt or generic kingshot
                                            query = "Kingshot Century Games best heroes meta"
                                
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
                        else:
                            logger.warning(f"AI called unknown tool: {tool_call.function.name}")
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": tool_call.function.name,
                                "content": "Error: Unknown tool. Please reply directly to the user."
                            })
                    
                    # Second call with the results
                    chat_completion = await client.chat.completions.create(
                        messages=messages,
                        model=current_model,
                        temperature=TEMPERATURE,
                        max_tokens=MAX_OUTPUT_TOKENS,
                        tools=tools
                    )
                    response_message = chat_completion.choices[0].message
                    
                content = response_message.content
                if content:
                    # Strip any "Imo:" or "**Imo:**" prefix forcibly
                    content = re.sub(r'^(?:\*\*Imo\*\*|Imo)\s*:\s*', '', content.strip(), flags=re.IGNORECASE)
                return content.strip() if content else ""
            except (RateLimitError, APIStatusError) as api_err:
                # If we encounter a rate limit or 502/429 error, try the next model
                logger.warning(f"Model {current_model} failed: {api_err}")
                if idx < len(models_to_try) - 1:
                    logger.info(f"Falling back to {models_to_try[idx + 1]}")
                    
                    # Clean up messages array by removing tool calls and responses that might have been added
                    # before retrying, we just want system prompt, history, and user prompt
                    # Keep only the first len(history) + 2 messages
                    keep_len = 1 + (len(history) if history else 0) + 1
                    messages = messages[:keep_len]
                    continue
                else:
                    raise api_err # re-raise if all models fail
            
    except Exception as e:
        logger.error(f"API Error: {e}")
        return f"my brain just lagged 💀 (Error: {e})"
