import asyncio
import os
from bot.ai import generate_response

async def main():
    print("Testing generate_response...")
    resp = await generate_response("imo how are you", [])
    print(f"RESPONSE: {resp}")

if __name__ == '__main__':
    asyncio.run(main())
