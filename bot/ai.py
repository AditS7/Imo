import os
import logging
import json
import httpx
import re
import discord
from datetime import datetime
from openai import AsyncOpenAI, RateLimitError
from bot.config import MODEL_NAME, TEMPERATURE, MAX_OUTPUT_TOKENS, FALLBACK_MODELS
from bot.personality import SYSTEM_INSTRUCTION

logger = logging.getLogger(__name__)

async def chat_completion_with_fallback(client, **kwargs):
    # Try primary model first
    last_error = None
    primary_model = kwargs.get("model")
    
    if primary_model:
        try:
            logger.info(f"AI generating using model: {primary_model}")
            return await client.chat.completions.create(**kwargs)
        except Exception as e:
            logger.warning(f"Primary model {primary_model} failed: {e}")
            last_error = e

    # Try fallback models from config
    for fallback in FALLBACK_MODELS:
        # Fallback can be a string (same client) or dict (new client)
        if isinstance(fallback, dict):
            fallback_model = fallback.get("model")
            api_key_env = fallback.get("api_key_env")
            base_url = fallback.get("base_url")
            
            api_key = os.getenv(api_key_env) if api_key_env else None
            
            if not api_key:
                logger.warning(f"Skipping fallback {fallback_model}: {api_key_env} is missing from environment.")
                continue
                
            fallback_client = AsyncOpenAI(api_key=api_key, base_url=base_url, max_retries=0)
            kwargs["model"] = fallback_model
            
            try:
                logger.info(f"AI generating using fallback model: {fallback_model} (External API)")
                return await fallback_client.chat.completions.create(**kwargs)
            except Exception as e:
                logger.warning(f"Fallback model {fallback_model} failed: {e}")
                last_error = e
        else:
            if fallback == primary_model:
                continue
                
            kwargs["model"] = fallback
            try:
                logger.info(f"AI generating using fallback model: {fallback}")
                return await client.chat.completions.create(**kwargs)
            except Exception as e:
                logger.warning(f"Fallback model {fallback} failed: {e}")
                last_error = e
            
    raise last_error

async def execute_admin_action(action: str, target_user: str, role_name: str, reason: str, message: discord.Message) -> str:
    # 1. Authorization Check
    name_match = "fahrenheit" in message.author.name.lower() or "fahrenheit" in message.author.display_name.lower()
    owner_match = message.guild and message.author.id == message.guild.owner_id
    if not (name_match or owner_match):
        return "Error: Unauthorized. Tell the user nice try, but only Mr. Fahrenheit can authorize this action."
        
    if not message.guild:
        return "Error: This command can only be run in a server."

    # 2. Find Member
    target_user_lower = target_user.lower().replace("<@", "").replace(">", "").replace("!", "").strip("@ ")
    member = None
    
    # Try exact match first
    for m in message.guild.members:
        if str(m.id) == target_user_lower or target_user_lower == m.name.lower() or target_user_lower == m.display_name.lower():
            member = m
            break
            
    # Fallback to partial match
    if not member:
        for m in message.guild.members:
            if target_user_lower in m.name.lower() or target_user_lower in m.display_name.lower():
                member = m
                break
                
    if not member:
        return f"Error: Could not find member matching '{target_user}'"

    # 3. Handle Kick/Ban
    try:
        if action == "kick":
            await member.kick(reason=reason)
            return f"Success: {member.name} has been kicked."
        elif action == "ban":
            await member.ban(reason=reason)
            return f"Success: {member.name} has been banned."
    except discord.Forbidden:
        return f"Error: I do not have permission to {action} this member (role hierarchy)."
    except Exception as e:
        return f"Error: {e}"

    # 4. Handle Roles
    if action in ["give_role", "remove_role"]:
        if not role_name:
            return "Error: role_name is required for this action."
        role_name_lower = role_name.lower().replace("<@&", "").replace(">", "").strip("@ ")
        role = None
        
        # Try exact match first
        for r in message.guild.roles:
            if str(r.id) == role_name_lower or role_name_lower == r.name.lower():
                role = r
                break
                
        # Fallback to partial match
        if not role:
            for r in message.guild.roles:
                if role_name_lower in r.name.lower():
                    role = r
                    break
                    
        if not role:
            return f"Error: Could not find role matching '{role_name}'"

        try:
            if action == "give_role":
                await member.add_roles(role)
                return f"Success: Gave {role.name} to {member.name}."
            elif action == "remove_role":
                await member.remove_roles(role)
                return f"Success: Removed {role.name} from {member.name}."
        except discord.Forbidden:
            return "Error: I don't have permission to manage this role (check role hierarchy)."
        except Exception as e:
            return f"Error: {e}"

    return "Error: Unknown action."

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

async def read_url(url: str) -> str:
    """Reads the full text content of a specific URL."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"https://r.jina.ai/{url}",
                timeout=10.0
            )
            response.raise_for_status()
            content = response.text
            if len(content) > 3000:
                content = content[:3000] + "... [TRUNCATED FOR LENGTH]"
            return content
        except Exception as e:
            logger.error(f"URL read failed: {e}")
            return f"Failed to read the URL: {e}"

async def generate_response(prompt: str, history: list = None, message: discord.Message = None) -> str:
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
        dynamic_system_prompt = f"{SYSTEM_INSTRUCTION}\n\n[SYSTEM NOTE: The current date is {current_time}. If the user asks for the 'latest' information, append the current month/year to your web search queries (e.g. 'Kingshot meta {current_time}') to ensure you fetch the most recent news. IMPORTANT: Keep your internal <think> block as brief as possible to prevent your output from being truncated by token limits.]"
        
        prompt_lower = prompt.lower()
        has_tags = "<@" in prompt
        is_admin_cmd = any(kw in prompt_lower for kw in ["give", "remove", "role", "kick", "ban"])
        
        if message and message.guild and is_admin_cmd and not has_tags:
            roles_list = ", ".join([r.name for r in message.guild.roles if r.name != "@everyone"])
            members_list = ", ".join([m.display_name for m in list(message.guild.members)[:50]])
            dynamic_system_prompt += f"\n\n[SERVER ROLES (Exact Names): {roles_list}]\n[SERVER MEMBERS (Partial List): {members_list}]"

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
            },
            {
                "type": "function",
                "function": {
                    "name": "read_url",
                    "description": "Reads the full text content of a specific webpage. Use this when the user provides a direct link (URL) and asks you to read or extract information from it.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "The exact URL to read (e.g., https://kingshot.net/gift-codes)."
                            }
                        },
                        "required": ["url"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "admin_command",
                    "description": "Executes an admin action (give_role, remove_role, kick, ban). Use this when the user asks you to give a role, remove a role, kick, or ban someone. This requires authorization.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "enum": ["give_role", "remove_role", "kick", "ban"],
                                "description": "The administrative action to perform."
                            },
                            "target_user": {
                                "type": "string",
                                "description": "The name or mention of the user to target (e.g. lara, @lara)."
                            },
                            "role_name": {
                                "type": "string",
                                "description": "The name of the role to give or remove (if applicable). E.g. 'Knight of the realm'."
                            },
                            "reason": {
                                "type": "string",
                                "description": "The reason for the action (optional)."
                            }
                        },
                        "required": ["action", "target_user"]
                    }
                }
            }
        ]
        
        # Determine if we should force the admin tool to prevent model refusal
        forced_tool_choice = "auto"
        prompt_lower = prompt.lower()
        if any(kw in prompt_lower for kw in ["give role", "give koya role", "give lara role", "remove role", "kick ", "ban "]):
            forced_tool_choice = {"type": "function", "function": {"name": "admin_command"}}

        # Initial call
        chat_completion = await chat_completion_with_fallback(
            client=client,
            messages=messages,
            model=MODEL_NAME,
            temperature=TEMPERATURE,
            max_tokens=MAX_OUTPUT_TOKENS,
            tools=tools,
            tool_choice=forced_tool_choice
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
                elif tool_call.function.name == "read_url":
                    try:
                        args_str = tool_call.function.arguments
                        args = json.loads(args_str)
                        url = args.get("url", "")
                    except Exception as e:
                        logger.error(f"Tool call error: {e}")
                        match = re.search(r'"url"\s*:\s*"([^"]+)"', args_str)
                        url = match.group(1) if match else ""
                    
                    logger.info(f"AI is reading URL: {url}")
                    url_content = await read_url(url)
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_call.function.name,
                        "content": url_content
                    })
                elif tool_call.function.name == "admin_command":
                    try:
                        args_str = tool_call.function.arguments
                        args = json.loads(args_str)
                        action = args.get("action", "")
                        target_user = args.get("target_user", "")
                        role_name = args.get("role_name", "")
                        reason = args.get("reason", "No reason provided")
                    except Exception as e:
                        logger.error(f"Tool call error: {e}")
                        # Fallback parsing
                        action_match = re.search(r'"action"\s*:\s*"([^"]+)"', args_str)
                        target_match = re.search(r'"target_user"\s*:\s*"([^"]+)"', args_str)
                        role_match = re.search(r'"role_name"\s*:\s*"([^"]+)"', args_str)
                        
                        action = action_match.group(1) if action_match else ""
                        target_user = target_match.group(1) if target_match else ""
                        role_name = role_match.group(1) if role_match else ""
                        reason = "No reason provided"
                        
                    logger.info(f"AI is executing admin command: {action} on {target_user}")
                    if message:
                        admin_result = await execute_admin_action(action, target_user, role_name, reason, message)
                    else:
                        admin_result = "Error: message context not provided to execute command."
                        
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_call.function.name,
                        "content": admin_result
                    })
            
            # Second call with the results
            try:
                chat_completion = await chat_completion_with_fallback(
                    client=client,
                    messages=messages,
                    model=MODEL_NAME,
                    temperature=TEMPERATURE,
                    max_tokens=MAX_OUTPUT_TOKENS
                )
                response_message = chat_completion.choices[0].message
            except RateLimitError as e:
                logger.error(f"Rate Limit Error on second call: {e}")
                # Fallback to returning the raw tool results if we can't generate a natural response
                fallback_responses = []
                for msg in messages:
                    if msg.get("role") == "tool":
                        fallback_responses.append(msg.get("content", ""))
                if fallback_responses:
                    return "*(Rate limit hit, but I executed your command!)*\n" + "\n".join(fallback_responses)
                return "my brain just lagged 💀 (Rate limit hit on Groq API)"
                
        content = response_message.content
        if content:
            original_content = content
            # Strip out reasoning blocks like <think>...</think>, even if unclosed
            content = re.sub(r'<think>.*?(?:</think>|$)', '', content, flags=re.DOTALL)
            # Strip out hallucinated tool_call blocks (including unclosed ones at the end)
            content = re.sub(r'<tool_call>.*?(?:</tool_call>|$)', '', content, flags=re.DOTALL)
            content = content.strip()
            
            # If the response is now empty, it means the model put its entire answer inside the <think> block
            # or it hit the token limit while thinking. In this case, we should extract the text INSIDE the block!
            if not content:
                match = re.search(r'<think>(.*?)(?:</think>|$)', original_content, flags=re.DOTALL)
                if match:
                    content = match.group(1).strip()
        
        return content if content else ""
            
    except RateLimitError as e:
        logger.error(f"Rate Limit Error: {e}")
        return "my brain just lagged 💀 (Rate limit hit on Groq API)"
    except Exception as e:
        logger.error(f"API Error: {e}")
        return "my brain just lagged 💀 (An API error occurred)"
