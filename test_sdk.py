import asyncio
import os
from openai import AsyncOpenAI
import logging

logging.basicConfig(level=logging.INFO)

async def main():
    client = AsyncOpenAI(api_key="fake", base_url="https://api-inference.huggingface.co/v1/")
    try:
        response = await client.chat.completions.create(
            model="Qwen/Qwen2.5-72B-Instruct",
            messages=[{"role": "user", "content": "hello"}],
            max_tokens=10
        )
        print(response)
    except Exception as e:
        print(f"Error type: {type(e)}")
        print(f"Error: {e}")

asyncio.run(main())
