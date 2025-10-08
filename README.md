# Group Inviter Bot

Telegram bot skeleton built on Python 3.13 and the latest `aiogram` 3.x stack. The project ships with typed configuration, structured logging, and ready-to-extend `/start` handlers.

## Features
- Async-first architecture using `aiogram` 3 with router-based handler registration
- Pydantic-powered configuration models loaded from YAML or `GROUP_INVITER_CONFIG`
- Timezone-aware logging with optional JSON output plus rotating file handlers
- Makefile workflows backed by `uv` for reproducible environments, linting, and type checks

## Requirements
- Python 3.13 (matches the interpreter targeted by this project)
- [`uv`](https://github.com/astral-sh/uv) available on your `PATH`
- A Telegram bot token from [BotFather](https://telegram.me/BotFather)

## Quickstart
1. Copy `config/config.yaml` and fill in `telegram.bot_token`.
2. Provision the virtual environment and install dependencies:
   ```bash
   make setup
   ```
3. Launch the bot (polling mode):
   ```bash
   make run
   # or equivalently
   start-bot
   # or
   python -m group_inviter
   ```

The default dispatcher wires routers from `src/group_inviter/handlers`. Extend or add modules under that package to grow the bot's behaviour.

## Configuration
- `telegram.bot_token`: required token string supplied by BotFather.
- `telegram.parse_mode`: parse mode name understood by aiogram (e.g. `HTML`, `MarkdownV2`). Unknown values fall back to HTML with a warning.
- `telegram.admin_chat_id`: optional numeric chat ID that receives notifications when unexpected errors occur.
- `logging.json`: flip to `true` for JSON-formatted logs. Classic text formatting remains the default.
- `logging.directory`: directory for rotating log files (`info.log`, `debug.log`), created automatically.
- `logging.timezone`: IANA timezone name used for timestamps (defaults to UTC, invalid names fall back to UTC).
- Override the config path via `GROUP_INVITER_CONFIG=/path/to/custom.yaml` or pass a path into `group_inviter.main.main`.

## Development Workflow
- `make lint` – run Ruff checks and MyPy over `src`.
- `ruff format src tests` – format the codebase.
- `pytest` – execute the test suite (add tests under `tests/`).
- `make clean` – drop the virtual environment created by `make setup`.

If you prefer to manage environments manually, create a Python 3.13 virtualenv and run:
```bash
python -m pip install --upgrade pip
python -m pip install -e .[dev]
```

With structured logging, rotating file handlers, and typed configuration in place, you can focus on implementing domain-specific handlers while the scaffold handles the wiring.
