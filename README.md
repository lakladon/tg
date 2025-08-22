### Telegram Admin Bot

A Telegram bot with an admin panel and in-Telegram DB editing (KV and optional SQL).

#### Requirements
- Python 3.10+
- A Telegram Bot token from @BotFather

#### Setup
1. Copy `.env.example` to `.env` and set values.
2. Create and activate a virtualenv (optional):
   ```bash
   python3 -m venv .venv && source .venv/bin/activate
   ```
3. Install deps:
   ```bash
   pip install -r requirements.txt
   ```

#### Run
```bash
python -m src.main
```

#### Features
- /start registers the user
- /admin shows admin panel for configured admins
- KV store editor: list/add/edit/delete keys
- Optional SQL executor (admin-only) with safety confirmation

#### Env Vars
- BOT_TOKEN: Telegram bot token
- ADMINS: Comma-separated Telegram user IDs allowed to use admin panel
- DB_PATH: SQLite file path (default `data/bot.db`)