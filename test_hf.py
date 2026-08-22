import asyncio
import httpx
import os

async def main():
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post("https://api-inference.huggingface.co/v1/chat/completions", json={"model": "Qwen/Qwen2.5-72B-Instruct", "messages": [{"role": "user", "content": "hi"}]})
            print(resp.status_code, resp.text)
        except Exception as e:
            print("Conn Error:", e)

asyncio.run(main())
