# Imo - Kingshot & Immortals Discord AI Bot

Imo is a casual, witty, and knowledgeable AI-powered Discord community member built with Python (`discord.py`) and high-speed LLM inference (powered by Groq / OpenRouter via the `openai` SDK).

Customized specifically for the **Kingshot** mobile game community and the **Immortals** alliance, Imo acts like a real player hanging out in the server: chatting, searching guides, tracking kingdom milestones, and moderating.

---

## Features

- **Natural Name Trigger**: Responds naturally when addressed by name (e.g. `imo ...`), mentioned (`@Imo`), or replied to directly.
- **Spontaneous Banter**: Occasionally chimes in on conversations without being pinged (configurable probability and cooldown).
- **Kingshot Strategy & Web Search**: Integrated live web search powered by Tavily (`search_web`), prioritizing `kingshotguides.com` with broader fallback for heroes, meta, mechanics, and event guides.
- **URL Ingestion**: Ingests and reads direct article/guide links via Jina Reader (`read_url`) when pasted into chat.
- **Kingdom 2403 Daily Tracker**:
  - Automatically posts the Kingdom's age (started **August 8, 2026**) and upcoming event countdowns daily at **00:00 UTC**.
  - Tracks 21 milestone events across 2026–2027 (Gen 2–6 Heroes & Pets, King's Castle Wars, KvK Preparation & Battles, Age of Truegold, War Academy, etc.).
- **Server Administration & Moderation**:
  - Administrative slash and text commands (`/kick`, `/ban`, `/give_role`, `/remove_role`) reserved for Mr. Fahrenheit.
  - LLM tool-calling support (`admin_command`) allowing authorized conversational moderation.
- **Automatic Welcome Greetings**: Welcomes newly joined members with custom, AI-crafted greetings in the welcome channel.
- **Configurable Context Memory**: Maintains short-term conversational context per channel (`bot/memory.py`).

---

## Tech Stack & Architecture

- **Language & Runtime**: Python 3.12
- **Discord Framework**: `discord.py` 2.4.0 (Application Commands & Tasks)
- **AI Inference**: `openai` SDK (Groq API by default with OpenRouter fallback)
- **Primary Model**: `qwen/qwen3.8-27b` (configurable via `MODEL_NAME`)
- **Web Search**: Tavily Search API (`httpx`)
- **Deployment**: Docker (`Dockerfile`), Railway (`railway.json` / `railway.toml`)

---

## 1. Setup & Credentials

### Step 1: Discord Bot Setup
1. Go to the [Discord Developer Portal](https://discord.com/developers/applications).
2. Click **New Application** and name it "Imo".
3. Navigate to the **Bot** tab.
4. Under **Privileged Gateway Intents**, enable:
   - **Message Content Intent** (Required for reading messages and name triggers)
   - **Server Members Intent** (Required for welcome greetings and moderation)
5. Under **Bot Permissions**, ensure the bot has permissions for:
   - `Send Messages`, `Read Messages/View Channels`, `Read Message History`
   - `Manage Roles`, `Kick Members`, `Ban Members` (if using moderation features)
6. Click **Reset Token** and copy your bot token (`DISCORD_TOKEN`).
7. In the **OAuth2 > URL Generator** tab, select `bot` and `applications.commands` scopes, copy the URL, and invite the bot to your Discord server.

### Step 2: Get AI API Keys
1. **Groq API Key (Recommended for speed)**:
   - Get a free key at [Groq Console](https://console.groq.com/).
2. **OpenRouter API Key (Alternative / Fallback)**:
   - Get a key at [OpenRouter](https://openrouter.ai/).
3. **Tavily API Key (For Guide & Web Search)**:
   - Get an API key at [Tavily AI](https://tavily.com/).

---

## 2. Environment Configuration

Copy the sample environment file:

```bash
cp .env.example .env
```

Configure the following variables in `.env`:

| Variable | Required | Default | Description |
| :--- | :---: | :---: | :--- |
| `DISCORD_TOKEN` | **Yes** | — | Discord Bot Token from Developer Portal |
| `GROQ_API_KEY` | **Yes\*** | — | Primary fast LLM inference API key (\*or `OPENROUTER_API_KEY`) |
| `OPENROUTER_API_KEY` | Optional | — | Fallback / alternative LLM inference key |
| `TAVILY_API_KEY` | Optional | — | Enables live web search and guide retrieval |
| `MODEL_NAME` | Optional | `qwen/qwen3.8-27b` | Primary AI model identifier |
| `SPONTANEOUS_REPLY_ENABLED` | Optional | `true` | Enable/disable spontaneous replies |
| `SPONTANEOUS_REPLY_CHANCE` | Optional | `0.10` | 10% chance to reply spontaneously |
| `SPONTANEOUS_COOLDOWN_SECONDS` | Optional | `60` | Minimum seconds between spontaneous messages |
| `MAX_HISTORY_MESSAGES` | Optional | `3` | Messages retained in memory per channel |
| `KINGDOM_CHANNEL_ID` | Optional | — | Channel ID for daily 00:00 UTC kingdom updates |

---

## 3. Running Locally

Requires **Python 3.12+**:

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd imo-bot

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the bot
python -m bot.main
```

You should see:
```text
[INFO] bot.main: Synced command(s).
[INFO] bot.main: Imo started. Logged in as Imo#xxxx
[INFO] bot.main: Connected to Discord
```

---

## 4. 24/7 Hosting & Deployment

Because Discord bots require a persistent WebSocket connection, Imo must run continuously in a container or background process.

### Option A: Railway (Recommended)

This repository includes a native `Dockerfile` and `railway.json`:

1. Fork or push this repository to GitHub.
2. Log into [Railway](https://railway.app) and create a **New Project > Deploy from GitHub repo**.
3. Railway will automatically detect the `Dockerfile` and build the container.
4. Go to the service **Variables** tab and set:
   - `DISCORD_TOKEN`
   - `GROQ_API_KEY`
   - `TAVILY_API_KEY`
   - `MODEL_NAME` (optional)
   - `KINGDOM_CHANNEL_ID` (optional)
5. Deploy! Railway will launch `python -m bot.main`.

### Option B: Docker on VPS / Server

```bash
# Build Docker image
docker build -t imo-bot .

# Run container with auto-restart
docker run -d \
  --name imo-bot \
  --restart unless-stopped \
  --env-file .env \
  imo-bot
```

---

## 5. Bot Commands Reference

### Kingdom 2403 Tracker Commands
| Slash Command | Text Command | Permission | Description |
| :--- | :--- | :---: | :--- |
| `/set_kingdom_channel` | `!set_kingdom_channel #channel` | Admin | Sets channel for daily 00:00 UTC kingdom updates |
| `/kingdom_age` | `!kingdom_age` | Everyone | Shows current kingdom age and upcoming events |
| `/kingdom_schedule` | `!kingdom_schedule` | Everyone | Displays full milestone timeline (2026–2027) |
| `/post_kingdom_age_now` | `!post_kingdom_age_now` | Admin | Immediately triggers the daily announcement |

### Admin & Utility Commands
| Slash Command | Text Command | Permission | Description |
| :--- | :--- | :---: | :--- |
| `/status` | — | Everyone | Checks latency and bot uptime |
| `/settings` | — | Admin | Displays spontaneous chat and kingdom settings |
| `/toggle_spontaneous` | — | Admin | Toggles unprompted chat replies on/off |
| `/clear_memory` | — | Admin | Clears conversation history for the channel |
| `/kick` | `!kick @user [reason]` | Mr. Fahrenheit | Kicks member from server |
| `/ban` | `!ban @user [reason]` | Mr. Fahrenheit | Bans member from server |
| `/give_role` | `!give_role @user @role` | Mr. Fahrenheit | Assigns a role to a member |
| `/remove_role` | `!remove_role @user @role`| Mr. Fahrenheit | Removes a role from a member |

---

## 6. Project Structure

```text
├── Dockerfile                 # Container definition for Railway/Docker
├── requirements.txt           # Python package dependencies
├── railway.json               # Railway build and deploy manifest
├── railway.toml               # Railway builder configuration
├── server.js                  # Lightweight healthcheck server for dev previews
├── .env.example               # Example environment variables
└── bot/
    ├── main.py                # Bot lifecycle, cogs loading, and event listeners
    ├── config.py              # Environment variable loader and settings
    ├── personality.py         # Kingshot system prompt, persona, and guidelines
    ├── ai.py                  # LLM inference, Tavily search, URL reader & function calls
    ├── message_handler.py     # Trigger detection, spontaneous chat logic, chunking
    ├── memory.py              # In-memory per-channel conversation buffer
    ├── admin.py               # Moderation & configuration commands cog
    └── kingdom.py             # 00:00 UTC loop, age calculator, and event schedule cog
```

---

## 7. Troubleshooting

- **Bot doesn't respond to messages without a ping:**
  - Verify **Message Content Intent** is enabled in the Discord Developer Portal under the **Bot** tab.
- **Welcome message doesn't trigger when members join:**
  - Verify **Server Members Intent** is enabled in the Discord Developer Portal.
- **Bot replies with "my brain just lagged 💀":**
  - Verify `GROQ_API_KEY` (or `OPENROUTER_API_KEY`) is valid and has remaining credits/rate limits. Check server logs for exact error messages.
- **Web search doesn't return Kingshot guides:**
  - Verify `TAVILY_API_KEY` is set in your environment variables.
- **Admin moderation commands fail with permission error:**
  - Ensure Imo's bot role in Discord Server Settings > Roles is dragged **above** the roles of the members it is trying to moderate or assign.
