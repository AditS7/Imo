# Imo - The Casual Discord Bot

Imo is a casual, witty, AI-powered Discord community member powered by Google's Gemini API and Python (`discord.py`).

Unlike a typical utility bot or ChatGPT wrapper, Imo is designed to feel like a real person hanging out in the server. It remembers recent context, responds when mentioned or called by name, and can even spontaneously chime in on normal conversations.

## Features
- **Name Trigger**: Responds naturally when you start a message with "imo" or "@Imo".
- **Spontaneous Chat**: Occasionally replies to conversations without being pinged (configurable probability and cooldown).
- **Short-term Memory**: Remembers the last 20 messages in a channel to understand context.
- **Admin Commands**: Built-in slash commands (`/settings`, `/status`, `/toggle_spontaneous`, `/clear_memory`).
- **Gemini Powered**: Uses the official `google-genai` Python SDK.

---

## 1. Setup Instructions

### Step 1: Create the Discord Bot
1. Go to the [Discord Developer Portal](https://discord.com/developers/applications).
2. Click **New Application** and name it "Imo".
3. Go to the **Bot** tab.
4. Under **Privileged Gateway Intents**, turn ON **Message Content Intent**. (This is critical, otherwise Imo cannot read normal messages).
5. Click **Reset Token** to get your bot token. Copy this token (you won't see it again!).

### Step 2: Invite Imo to your Server
1. Go to the **OAuth2 > URL Generator** tab.
2. Select the `bot` and `applications.commands` scopes.
3. Under Bot Permissions, select `Send Messages`, `Read Message History`, and `View Channels`.
4. Copy the generated URL and paste it into your browser to invite Imo to your server.

### Step 3: Get a Gemini API Key
1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Click **Create API key** and copy it.

---

## 2. Running Locally (For Testing)

Make sure you have Python 3.12+ installed.

1. Clone or download this project.
2. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
3. Edit `.env` and paste your `DISCORD_TOKEN` and `GEMINI_API_KEY`.
4. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
5. Run the bot:
   ```bash
   python -m bot.main
   ```

You should see logs indicating Imo has connected to Discord!

---

## 3. How It Works

### Name Trigger
Imo responds if you start a message with its name (case-insensitive) or mention it.
- `imo hello`
- `@Imo what's up?`
- `Imo, do you play Minecraft?`
- *Note: Words like "imodium" will NOT trigger it.*

### Spontaneous Conversation
If enabled, Imo will occasionally respond to normal messages without being called. This is controlled in the `.env` file:
- `SPONTANEOUS_REPLY_ENABLED=true`
- `SPONTANEOUS_REPLY_CHANCE=0.10` (10% chance)
- `SPONTANEOUS_COOLDOWN_SECONDS=60` (Won't speak again spontaneously for at least 60 seconds)

### Changing Personality
Open `bot/personality.py` and modify the `SYSTEM_INSTRUCTION` text block. Save and restart the bot.

### Changing the AI Model
Open `bot/config.py` and change the `MODEL_NAME` (e.g., to `gemini-2.5-pro` or `gemini-2.5-flash`).

---

## 4. Cloud Deployment (24/7 Hosting)

Because Imo needs to maintain a continuous WebSocket connection to Discord, it must run 24/7 on a server. It cannot just run when a message is received (like a serverless function).

### Option A: Google Compute Engine (e2-micro Free Tier)
Google Cloud offers a small virtual machine (`e2-micro`) that is completely free every month.
1. Create a Google Cloud Project.
2. Go to **Compute Engine** and create a new instance.
3. Choose the `e2-micro` machine type in an eligible US region (us-central1, us-east1, us-west1).
4. SSH into the machine, install Python/Git, clone your repo, configure `.env`.
5. Use `tmux` or `systemd` to keep the Python script running in the background even when you close the SSH window.

### Option B: Google Cloud Run
Cloud Run is mostly meant for HTTP servers. Discord bots run on persistent WebSockets. If you deploy this Dockerfile to Cloud Run, it will shut down when it thinks there is "no traffic".
*Workaround:* If you use Cloud Run, you MUST set **CPU Allocation** to "Always allocated". Note that this is NOT completely free, unlike the e2-micro VM.

### Other Options
You can deploy the included `Dockerfile` to services like **Railway**, **Render**, or **DigitalOcean App Platform**. Make sure to deploy as a **Background Worker**, not a Web Service, and set your Environment Variables in their dashboard.

---

## 5. Troubleshooting
- **Bot doesn't respond to natural text:** Make sure the **Message Content Intent** is enabled in the Discord Developer Portal.
- **Bot crashes with "Unauthorized":** Check that your `DISCORD_TOKEN` in `.env` is correct.
- **Bot responds with "my brain just lagged":** Your `GEMINI_API_KEY` might be invalid, or you hit the rate limit. Check the console logs.
