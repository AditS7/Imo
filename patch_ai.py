import re

with open("bot/ai.py", "r") as f:
    content = f.read()

# Replace the RateLimitError block in the inner loop with a generic Exception block
old_block = """            except RateLimitError as e:
                logger.error(f"Rate Limit Error on iteration {iteration}: {e}")
                if iteration > 0:
                    # Fallback to returning the raw tool results if we can't generate a natural response
                    fallback_responses = []
                    for msg in messages:
                        if msg.get("role") == "tool":
                            fallback_responses.append(msg.get("content", ""))
                    if fallback_responses:
                        return "*(Rate limit hit, but I executed your command!)*\\n" + "\\n".join(fallback_responses)
                return "my brain just lagged 💀 (Rate limit hit on Groq API)" """

new_block = """            except Exception as e:
                logger.error(f"API Error on iteration {iteration}: {e}")
                if iteration > 0:
                    # Fallback to returning the raw tool results if we can't generate a natural response
                    fallback_responses = []
                    for msg in messages:
                        if msg.get("role") == "tool":
                            fallback_responses.append(msg.get("content", ""))
                    if fallback_responses:
                        return "*(I hit an API error while reading the results, but here is what I found!)*\\n\\n" + "\\n".join(fallback_responses)
                
                if "RateLimit" in str(type(e)):
                    return "my brain just lagged 💀 (Rate limit hit on Groq API)"
                return "my brain just lagged 💀 (An API error occurred while generating)" """

if old_block in content:
    content = content.replace(old_block, new_block)
    print("Replaced error block!")
else:
    print("Could not find old block!")

# Truncate search results more aggressively
old_trunc = """            if len(full_context) > 2500:
                full_context = full_context[:2500] + "... [TRUNCATED FOR LENGTH]" """

new_trunc = """            if len(full_context) > 1500:
                full_context = full_context[:1500] + "... [TRUNCATED FOR LENGTH]" """

if old_trunc in content:
    content = content.replace(old_trunc, new_trunc)
    print("Replaced truncation block!")
else:
    print("Could not find truncation block!")

with open("bot/ai.py", "w") as f:
    f.write(content)
