import os
from dotenv import load_dotenv

load_dotenv()

# Secrets
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
ADMIN_USER_ID = os.getenv("ADMIN_USER_ID") # Discord User ID of the primary admin

# Spontaneous settings
SPONTANEOUS_REPLY_ENABLED = os.getenv("SPONTANEOUS_REPLY_ENABLED", "true").lower() == "true"
SPONTANEOUS_REPLY_CHANCE = float(os.getenv("SPONTANEOUS_REPLY_CHANCE", "0.10"))
SPONTANEOUS_COOLDOWN_SECONDS = int(os.getenv("SPONTANEOUS_COOLDOWN_SECONDS", "60"))

# Memory settings
MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", "3"))

# AI Settings
MODEL_NAME = "qwen/qwen3.6-27b"
FALLBACK_MODELS = [
    "meta-llama/llama-prompt-guard-2-22m",  # The user's requested backup model
    "llama3-8b-8192",  # A functional fallback for Groq since Prompt Guard is a classifier
    "meta-llama/llama-3-8b-instruct:free"  # A functional fallback for OpenRouter
]
TEMPERATURE = 0.7
MAX_OUTPUT_TOKENS = 1800
