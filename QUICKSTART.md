# Quick Start Guide - Rosey

## Running Your First Bot

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Choose Your Bot

**Rosey (Main Bot)** - Full-featured with logging, shell control, and database:

```bash
cd bot/rosey
cp config.json.dist config.json
```

**Simple Examples** - Minimal implementations:

```bash
cd examples/log  # or examples/echo, examples/markov, examples/tui
cp config.json.dist config.json
```

### 3. Configure Your Bot

Edit `config.json`:

```json
{
  "domain": "https://cytu.be",
  "channel": "YourChannelName",
  "user": ["YourBotName", "YourPassword"],
  "log_level": "INFO",
  "restart_delay": 5,
  "response_timeout": 1
}
```

### 4. Run the Bot

For Rosey:
```bash
cd bot/rosey
python rosey.py config.json
```

For examples:
```bash
cd examples/log  # or other example
python bot.py config.json
```

## Project Structure Overview

```
rosey-robot/
├── lib/                    # Core CyTube library - don't modify unless extending
│   ├── __init__.py        # Library exports
│   ├── bot.py             # Main Bot class
│   ├── channel.py         # Channel state
│   ├── playlist.py        # Playlist management
│   ├── socket_io.py       # WebSocket connection
│   ├── user.py            # User representation
│   ├── media_link.py      # Media URL parsing
│   ├── util.py            # Helpers
│   ├── error.py           # Exceptions
│   └── proxy.py           # Proxy support
│
├── common/                 # Shared bot utilities
│   ├── __init__.py
│   ├── config.py          # Configuration loader
│   ├── database.py        # SQLite for stats tracking
│   └── shell.py           # Remote shell interface
│
├── bot/                    # Main Rosey application
│   └── rosey/             # Full-featured CyTube bot
│       ├── rosey.py       # Main bot script
│       ├── prompt.md      # AI personality (for future LLM)
│       └── config.json.dist
│
├── examples/               # Example implementations
│   ├── tui/               # ⭐ Terminal UI chat client
│   ├── log/               # Simple logging
│   ├── echo/              # Echo bot
│   └── markov/            # Markov chain generator
│
├── requirements.txt        # Python dependencies
└── README.md              # Full documentation
```

## Creating a New Bot

1. Create a new directory under `examples/`:
   ```bash
   mkdir examples/mybot
   cd examples/mybot


2. Create `bot.py`:

   ```python
   #!/usr/bin/env python3
   import sys
   from pathlib import Path
   
   # Add project root to Python path
   project_root = Path(__file__).parent.parent.parent
   sys.path.insert(0, str(project_root))
   
   import asyncio
   from lib import Bot
   from common import get_config
   
   class MyBot(Bot):
       def __init__(self, *args, **kwargs):
           super().__init__(*args, **kwargs)
           self.on('chatMsg', self.handle_message)
       
       async def handle_message(self, event, data):
           # Your bot logic here
           pass
   
   async def run_bot():
       conf, kwargs = get_config()
       bot = MyBot(**kwargs)
       try:
           await bot.run()
       except KeyboardInterrupt:
           return 0
       return 1
   
   def main():
       return asyncio.run(run_bot())
   
   if __name__ == '__main__':
       sys.exit(main())
   ```

3. Create `config.json`:

   ```json
   {
     "domain": "https://cytu.be",
     "channel": "YourChannel",
     "user": ["BotName", "password"]
   }
   ```

4. Run it:

   ```bash
   python bot.py config.json
   ```


## Common Bot Events

- `'chatMsg'` - Someone sends a chat message
- `'pm'` - Private message received
- `'setCurrent'` - Media changes
- `'queue'` - Media added to playlist
- `'delete'` - Media removed
- `'addUser'` - User joins
- `'userLeave'` - User leaves
- `'login'` - Bot successfully logged in

## Useful Bot Methods

```python
# Chat
await bot.chat("Hello everyone!")
await bot.pm("username", "Private message")

# Playlist
await bot.add_media("https://youtube.com/watch?v=...")
await bot.remove_media(playlist_item)

# Users
await bot.kick("username", "Reason")
```

## Using the REPL Shell

Enable in config:
```json
{
  "shell": "127.0.0.1:8888"
}
```

Connect:
```bash
telnet 127.0.0.1 8888
```

Commands:
```python
>>> bot.user.name
>>> await bot.chat("Test")
>>> bot.channel.playlist.current
>>> exit
```

## Troubleshooting

**ModuleNotFoundError**: Install dependencies with `pip install -r requirements.txt`

**Connection Failed**: Check your domain and channel name in config.json

**Login Failed**: Verify your username and password

**Permission Denied**: Your bot needs appropriate rank in the channel

## Next Steps

- Read the full [README.md](README.md) for complete API documentation
- Check [CHANGELOG.md](CHANGELOG.md) for version history
- Explore the example implementations in `examples/` for patterns
- Study Rosey (`bot/rosey/`) for a full-featured bot implementation
- Review the TUI example (`examples/tui/`) for an interactive chat client

## Getting Help

1. Check the [CyTube Wiki](https://github.com/calzoneman/sync/wiki)
2. Review the example bots
3. Open an issue in this repository
4. Read the source code in `lib/` - it's well-commented!
