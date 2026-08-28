import re

with open("bot/ai.py", "r") as f:
    content = f.read()

# We want to replace everything from `# Initial call` down to `        if content:` with a loop.
start_marker = "        # Initial call"
end_marker = "        content = response_message.content\n        if content:"

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx == -1 or end_idx == -1:
    print("Could not find markers!")
    exit(1)

new_logic = """        for iteration in range(3):
            try:
                chat_completion = await chat_completion_with_fallback(
                    client=client,
                    messages=messages,
                    model=MODEL_NAME,
                    temperature=TEMPERATURE,
                    max_tokens=MAX_OUTPUT_TOKENS,
                    tools=tools,
                    tool_choice=forced_tool_choice if iteration == 0 else "auto"
                )
            except RateLimitError as e:
                logger.error(f"Rate Limit Error on iteration {iteration}: {e}")
                if iteration > 0:
                    # Fallback to returning the raw tool results if we can't generate a natural response
                    fallback_responses = []
                    for msg in messages:
                        if msg.get("role") == "tool":
                            fallback_responses.append(msg.get("content", ""))
                    if fallback_responses:
                        return "*(Rate limit hit, but I executed your command!)*\\n" + "\\n".join(fallback_responses)
                return "my brain just lagged 💀 (Rate limit hit on Groq API)"
                
            response_message = chat_completion.choices[0].message
            
            if not response_message.tool_calls:
                break # Final text response received
                
            # Append the assistant's message with tool calls
            messages.append(response_message.model_dump(exclude_unset=True))
            
            for tool_call in response_message.tool_calls:
                if tool_call.function.name == "search_web":
                    try:
                        args_str = tool_call.function.arguments
                        args = json.loads(args_str)
                        query = args.get("query", "")
                    except Exception as e:
                        logger.error(f"Tool call error: {e}")
                        match = re.search(r'"query"\\s*:\\s*"([^"]+)"', args_str)
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
                        match = re.search(r'"url"\\s*:\\s*"([^"]+)"', args_str)
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
                        action_match = re.search(r'"action"\\s*:\\s*"([^"]+)"', args_str)
                        target_match = re.search(r'"target_user"\\s*:\\s*"([^"]+)"', args_str)
                        role_match = re.search(r'"role_name"\\s*:\\s*"([^"]+)"', args_str)
                        
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

        content = response_message.content
        if content:
"""

new_content = content[:start_idx] + new_logic + content[end_idx + len(end_marker) - 13:]

with open("bot/ai.py", "w") as f:
    f.write(new_content)

print("Done!")
