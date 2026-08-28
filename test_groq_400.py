import os
import asyncio
from openai import AsyncOpenAI

async def main():
    client = AsyncOpenAI(api_key=os.getenv("GROQ_API_KEY"), base_url="https://api.groq.com/openai/v1")
    try:
        response = await client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[{"role": "user", "content": "Hello"}],
            tools=[{
                "type": "function",
                "function": {
                    "name": "test_tool",
                    "description": "Test",
                    "parameters": {"type": "object", "properties": {}}
                }
            }],
            tool_choice="auto"
        )
        print("Success:", response.choices[0].message.content)
    except Exception as e:
        print("Error type:", type(e))
        print("Error details:", e)

asyncio.run(main())
