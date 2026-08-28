import os
import asyncio
from openai import AsyncOpenAI

async def main():
    client = AsyncOpenAI(api_key=os.getenv("GROQ_API_KEY"), base_url="https://api.groq.com/openai/v1")
    try:
        response = await client.chat.completions.create(
            model="qwen/qwen3.6-27b",
            messages=[{"role": "user", "content": "Hello"}]
        )
        print("Success:", response.choices[0].message.content)
    except Exception as e:
        print("Error:", e)

asyncio.run(main())
