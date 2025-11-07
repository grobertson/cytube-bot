# CyTube Bot - Monolithic Edition

A Python-based framework for building bots that interact with [CyTube](https://github.com/calzoneman/sync) channels. This is a refactored, monolithic version designed for easier development and customization without the complexity of installable packages.

## 🎯 Project Goals

This project aims to provide:
- **Monolithic Architecture**: All core library code lives alongside bot implementations for easier development and debugging
- **Modern Python**: Updated for Python 3.8+ with proper asyncio patterns
- **Example Bots**: Multiple working examples (echo, logging, markov chain)
- **LLM Integration** *(Coming Soon)*: Non-intrusive AI-powered chat interactions using LLM APIs
- **Playlist Management**: Full support for CyTube playlist operations
- **REPL Interface**: Built-in shell for interactive bot control

## 📁 Project Structure

```
cytube-bot/
├── lib/                    # Core CyTube interaction library
│   ├── bot.py             # Main bot class
│   ├── channel.py         # Channel state management
│   ├── playlist.py        # Playlist operations
│   ├── socket_io.py       # Socket.IO connection handling
│   ├── user.py            # User representation
│   ├── media_link.py      # Media link parsing
│   ├── util.py            # Utility functions
│   ├── error.py           # Custom exceptions
│   └── proxy.py           # Proxy support
│
├── bots/                  # Bot implementations
│   ├── markov/           # Markov chain text generation bot
│   ├── echo/             # Simple echo bot
│   └── log/              # Channel logging bot
│
├── common/                # Shared utilities
│   ├── config.py         # Configuration management
│   └── shell.py          # Interactive REPL shell
│
└── requirements.txt       # Python dependencies
```

## 🚀 Quick Start

### Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd cytube-bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Running a Bot

Each bot requires a `config.json` file. See the example configurations in each bot directory.

**Echo Bot** (repeats messages back):
```bash
cd bots/echo
python bot.py config.json
```

**Log Bot** (logs all chat and media):
```bash
cd bots/log
python bot.py config.json
```

**Markov Bot** (learns from chat and generates responses):
```bash
cd bots/markov
python bot.py config.json
```

### Configuration Format

Example `config.json`:
```json
{
  "domain": "https://cytu.be",
  "channel": ["YourChannelName", "optional-password"],
  "user": ["BotUsername", "optional-password"],
  "response_timeout": 0.1,
  "restart_delay": 5,
  "log_level": "INFO",
  "shell": "127.0.0.1:8888"
}
```

#### Configuration Options

- **domain**: CyTube server URL (e.g., `https://cytu.be`)
- **channel**: Channel name or `[name, password]` for password-protected channels
- **user**: `null` (anonymous), `"GuestName"` (guest), or `["Username", "password"]` (registered)
- **response_timeout**: Socket.IO response timeout in seconds
- **restart_delay**: Delay before reconnecting after disconnect (`null` to disable auto-reconnect)
- **log_level**: Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`)
- **shell**: REPL server address (`"host:port"` or `null` to disable)
- **proxy**: Optional proxy server (`"host:port"`)

### Using the REPL Shell

If you enable the shell in your config, you can connect via telnet:

```bash
telnet 127.0.0.1 8888
```

Then interact with the bot directly:
```python
>>> bot.user.name
'YourBotName'
>>> await bot.chat("Hello from the shell!")
>>> bot.channel.playlist.current
<PlaylistItem ...>
```

## 🤖 Creating Your Own Bot

Create a new directory under `bots/` and subclass the `Bot` class:

```python
#!/usr/bin/env python3
import sys
from pathlib import Path

# Add project root to Python path (allows running from any directory)
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from lib import Bot, MessageParser
from lib.error import CytubeError, SocketIOError
from common import Shell, get_config

class MyBot(Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.msg_parser = MessageParser()
        
        # Register event handlers
        self.on('chatMsg', self.handle_chat)
        self.on('setCurrent', self.handle_media_change)
    
    async def handle_chat(self, event, data):
        username = data['username']
        msg = self.msg_parser.parse(data['msg'])
        self.logger.info(f'{username}: {msg}')
        
        # Example: respond to mentions
        if self.user.name in msg:
            await self.chat(f"{username}: You mentioned me!")
    
    async def handle_media_change(self, event, data):
        current = self.channel.playlist.current
        if current:
            self.logger.info(f'Now playing: {current.title}')

def main():
    conf, kwargs = get_config()
    loop = asyncio.get_event_loop()
    
    bot = MyBot(loop=loop, **kwargs)
    shell = Shell(conf.get('shell', None), bot, loop=loop)
    
    try:
        task = loop.create_task(bot.run())
        if shell.task is not None:
            task_ = asyncio.gather(task, shell.task)
        else:
            task_ = task
        loop.run_until_complete(task_)
    except (CytubeError, SocketIOError) as ex:
        print(repr(ex), file=sys.stderr)
    except KeyboardInterrupt:
        return 0
    finally:
        if shell.task:
            shell.task.cancel()
        task.cancel()
        shell.close()
        loop.close()
    
    return 1

if __name__ == '__main__':
    sys.exit(main())
```

## 📚 Core Library API

### Bot Class

The main `Bot` class provides methods for interacting with CyTube:

#### Chat Methods
- `await bot.chat(msg, meta=None)` - Send a chat message
- `await bot.pm(to, msg, meta=None)` - Send a private message
- `await bot.clear_chat()` - Clear the chat (requires permissions)

#### Playlist Methods
- `await bot.add_media(link, append=True, temp=True)` - Add media to playlist
- `await bot.remove_media(item)` - Remove a playlist item
- `await bot.move_media(item, after)` - Reorder playlist
- `await bot.set_current_media(item)` - Jump to a specific item

#### User Management
- `await bot.kick(user, reason='')` - Kick a user
- `await bot.set_leader(user)` - Assign leader
- `await bot.set_afk(value=True)` - Set AFK status

#### Event System
- `bot.on(event, *handlers)` - Register event handlers
- `bot.off(event, *handlers)` - Unregister event handlers
- `await bot.trigger(event, data)` - Manually trigger an event

#### Available Events
- `'chatMsg'` - Chat message received
- `'pm'` - Private message received
- `'setCurrent'` - Media changed
- `'queue'` - Media added to playlist
- `'delete'` - Media removed from playlist
- `'userlist'` - User list updated
- `'addUser'` - User joined
- `'userLeave'` - User left
- `'login'` - Bot logged in
- And many more...

### Channel State

Access channel information through `bot.channel`:

```python
bot.channel.name          # Channel name
bot.channel.motd          # Message of the day
bot.channel.userlist      # Dictionary of users
bot.channel.playlist      # Playlist object
bot.channel.permissions   # Channel permissions
```

### Playlist

Access playlist through `bot.channel.playlist`:

```python
playlist.current          # Currently playing item
playlist.queue            # List of queued items
playlist.locked           # Whether playlist is locked
playlist.get(uid)         # Get item by UID
```

## 🔮 Future Development

### Planned Features

1. **LLM Chat Integration**
   - OpenAI/Anthropic API support
   - Context-aware responses
   - Configurable trigger patterns
   - Rate limiting and cooldowns
   - Personality customization

2. **Advanced Playlist Features**
   - Smart playlist management
   - Media recommendations
   - Duplicate detection
   - Automatic queue filling

3. **Enhanced Bot Capabilities**
   - Plugin system for easy extensibility
   - Web dashboard for monitoring
   - Database integration for persistence
   - Multi-channel support

4. **AI-Powered Features**
   - Sentiment analysis
   - Content moderation
   - Smart responses based on channel context
   - Learning from user preferences

## 🛠️ Development

### Why Monolithic?

This project was restructured from a traditional Python package into a monolithic codebase for several reasons:

1. **Easier Development**: No need to reinstall packages after every change
2. **Better Debugging**: All code is local and easy to inspect
3. **Simpler Deployment**: Copy the directory and run
4. **Faster Iteration**: Modify library and bot code together
5. **Learning Friendly**: Everything is visible and accessible

### Project History

Originally based on [dead-beef's cytube-bot](https://github.com/dead-beef/cytube-bot), this project has been updated for modern Python and restructured for easier development and LLM integration.

## 📝 License

MIT License - See LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! This is a work in progress with the goal of creating a flexible, modern CyTube bot framework with AI capabilities.

## ⚠️ Notes

- Requires Python 3.8+
- Uses asyncio for all I/O operations
- Socket.IO connection via websockets
- Some features require specific channel permissions

## 📞 Support

For CyTube-related questions, see the [CyTube documentation](https://github.com/calzoneman/sync/wiki).

For bot-specific issues, please open an issue in this repository.
