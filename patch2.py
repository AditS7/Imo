with open("bot/ai.py", "r") as f:
    text = f.read()

text = text.replace(
    'return "my brain just lagged 💀 (Rate limit hit on Groq API)"',
    'return f"my brain just lagged 💀 (API Error on iteration {iteration}: {type(e).__name__})"'
)
with open("bot/ai.py", "w") as f:
    f.write(text)
