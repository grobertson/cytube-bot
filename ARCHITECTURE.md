# Architecture Overview

## Design Philosophy

This project follows a **monolithic architecture** where all components live together in a single repository. This design choice prioritizes:

1. **Development Speed**: No package installation between changes
2. **Transparency**: All code is visible and editable
3. **Simplicity**: Straightforward file organization
4. **Flexibility**: Easy to customize any layer

## Layer Architecture

```
┌─────────────────────────────────────────────────────┐
│              Bot Applications & Examples             │
│  • bot/rosey/ - Full-featured main bot              │
│  • examples/ - Reference implementations            │
│    - tui/ (terminal UI), log/, echo/, markov/       │
│  • Business logic                                    │
│  • Event handlers                                    │
│  • Bot-specific features                            │
└─────────────────────────────────────────────────────┘
                        ↓ uses
┌─────────────────────────────────────────────────────┐
│               Common Utilities (common/)             │
│  • Configuration loading (get_config)                │
│  • REPL shell interface                             │
│  • Logging setup                                     │
│  • Shared helper functions                          │
└─────────────────────────────────────────────────────┘
                        ↓ uses
┌─────────────────────────────────────────────────────┐
│              Core Library (lib/)                     │
│  • Bot base class                                    │
│  • Channel/Playlist/User models                     │
│  • Socket.IO communication                           │
│  • Event system                                      │
│  • CyTube protocol implementation                   │
└─────────────────────────────────────────────────────┘
                        ↓ uses
┌─────────────────────────────────────────────────────┐
│           External Dependencies                      │
│  • websockets (WebSocket client)                     │
│  • requests (HTTP client)                            │
│  • asyncio (Python standard library)                │
└─────────────────────────────────────────────────────┘
```

## Core Components

### lib/ - Core Library

**Purpose**: Handles all CyTube protocol interaction

**Key Files**:
- `bot.py` - Main Bot class with event system and CyTube API
- `socket_io.py` - WebSocket connection management
- `channel.py` - Channel state tracking
- `playlist.py` - Playlist state and operations
- `user.py` - User representation and permissions
- `media_link.py` - Media URL parsing (YouTube, Vimeo, etc.)

**Responsibilities**:
- WebSocket connection lifecycle
- CyTube protocol messages (emit/receive)
- State synchronization (users, playlist, channel settings)
- Permission checking
- Event emission

**Extension Points**:
- Subclass `Bot` for custom behavior
- Override event handlers (`_on_*` methods)
- Add new CyTube API methods

### common/ - Shared Utilities

**Purpose**: Reusable components for bot development

**Key Files**:
- `config.py` - JSON config loading, logging setup, proxy configuration
- `shell.py` - Interactive REPL server for runtime bot control

**Responsibilities**:
- Configuration management
- Logger configuration
- REPL server for debugging
- Shared utility functions

**Extension Points**:
- Add new configuration options
- Extend shell commands
- Add shared helper functions

### bot/ - Main Application & examples/ - Reference Implementations

**Purpose**: 
- `bot/rosey/` - Full-featured production bot with logging, shell, database
- `examples/` - Simplified reference implementations for learning

**Structure**:

```text
bot/
└── rosey/          # Main Rosey bot
    ├── rosey.py    # Full-featured implementation
    ├── prompt.md   # AI personality (for future LLM)
    └── config.json.dist

examples/
├── tui/            # ⭐ Terminal UI chat client
├── log/            # Simple chat/media logging
├── echo/           # Basic message echo
└── markov/         # Markov chain text generation
```

**Responsibilities**:
- Business logic
- Event handling
- Bot-specific features
- Configuration

**Extension Points**:
- Customize Rosey in `bot/rosey/`
- Create new examples in `examples/`
- Combine features from multiple examples
- Add custom commands and behaviors

## Event Flow

```
1. WebSocket Message Received
   ↓
2. socket_io.py: Parse message
   ↓
3. bot.py: Trigger event
   ↓
4. Internal handlers (_on_*): Update state
   ↓
5. User handlers: Custom bot logic
   ↓
6. [Optional] Send response back through socket
```

## State Management

The Bot maintains synchronized state:

```python
bot.user                    # Bot's user info
bot.channel                 # Channel state
  .name, .motd, .css, .js
  .userlist                 # All users
  .playlist                 # Playlist state
    .current               # Current media
    .queue                 # Queued items
  .permissions             # Channel permissions
```

State is updated automatically via internal event handlers (`_on_*` methods).

## Event System

### Registration
```python
bot.on('eventName', handler1, handler2, ...)
bot.off('eventName', handler1)
```

### Handler Signature
```python
async def handler(event: str, data: dict) -> bool:
    # Return True to stop propagation
    return False
```

### Event Priority
Handlers execute in registration order. Return `True` to stop propagation.

### Built-in Events
- Protocol events: `chatMsg`, `pm`, `setCurrent`, `queue`, `delete`, etc.
- Custom events: `login`, `error`

## Communication Patterns

### Request-Response
Some operations wait for confirmation:
```python
response = await bot.socket.emit(
    'eventName',
    payload,
    response_matcher,
    timeout
)
```

### Fire-and-Forget
Most state updates are broadcast:
```python
await bot.socket.emit('eventName', payload)
```

### State Sync
Channel state synced on connection:
1. Join channel
2. Receive initial state (userlist, playlist, settings)
3. Subscribe to updates

## Async Design

All I/O operations are asynchronous using `asyncio`:

- **Bot.run()**: Main event loop
- **Event handlers**: Can be sync or async
- **API methods**: All async (`await bot.chat(...)`)

### Event Loop Management
```python
loop = asyncio.get_event_loop()
bot = MyBot(loop=loop, ...)
loop.run_until_complete(bot.run())
```

## Error Handling

### Exception Hierarchy
```
CytubeError (base)
├── SocketIOError (connection issues)
├── LoginError (authentication)
├── ChannelError (general channel errors)
├── ChannelPermissionError (insufficient permissions)
└── Kicked (bot was kicked)
```

### Error Propagation
- Network errors: Caught, logged, trigger reconnect
- Permission errors: Raised to caller
- Unexpected errors in handlers: Logged, trigger 'error' event

## Future Architecture Plans

### LLM Integration Layer

```text
bot/rosey/
├── rosey.py            # Main bot
├── llm/
│   ├── client.py       # LLM API client
│   ├── context.py      # Context management
│   ├── prompts.py      # Prompt templates
│   └── filters.py      # Response filtering
└── config.json
```

### Plugin System

```text
bot/rosey/
├── rosey.py
└── plugins/
    ├── commands.py     # Command handler plugin
    ├── moderation.py   # Auto-moderation plugin
    └── playlist.py     # Playlist management plugin
```

### Multi-Channel Support
```python
class MultiBot:
    def __init__(self):
        self.bots = {}  # channel -> Bot instance
    
    async def connect(self, channel):
        bot = Bot(channel=channel, ...)
        self.bots[channel] = bot
        await bot.run()
```

## Development Workflow

### Making Changes

1. **Library Changes** (lib/)
   - Modify source
   - Test immediately (no reinstall needed)
   - Changes affect all bots

2. **Bot Changes** (bot/rosey/)
   - Modify rosey.py
   - Restart bot
   - Independent of examples

3. **Common Changes** (common/)
   - Modify utilities
   - Restart affected bots
   - Changes affect all users

4. **Example Changes** (examples/)
   - Modify for learning/testing
   - Won't affect main Rosey bot

### Testing Strategy

1. **Unit tests**: Test individual components
2. **Integration tests**: Test bot + library interaction
3. **Manual tests**: Run bots against test channels

### Debugging

1. **Enable DEBUG logging**: Set `"log_level": "DEBUG"` in config
2. **Use REPL shell**: Connect via telnet for runtime inspection
3. **Add print statements**: Direct console output
4. **Exception traces**: Full stack traces in logs

## Performance Considerations

### Bottlenecks
- WebSocket I/O (network bound)
- Message parsing (JSON deserialization)
- Event handler execution

### Optimizations
- Async I/O prevents blocking
- State caching reduces lookups
- Lazy loading for large data

### Scaling
- One bot = one connection
- Multiple bots = multiple processes
- Connection pooling not applicable

## Security Considerations

### Credentials
- Store passwords in config files (gitignored)
- Consider environment variables for production
- Never commit config.json with real credentials

### Input Validation
- Parse and sanitize all incoming messages
- Validate media URLs before queueing
- Check permissions before operations

### Rate Limiting
- Implement cooldowns for commands
- Track message frequency
- Respect channel flood protection

## Migration from Package Structure

Old structure:

```text
site-packages/cytube_bot_async/  # Installed package
your-project/
└── bot.py                        # Your code
```

New structure:

```text
rosey-robot/
├── lib/           # Library code (local)
├── common/        # Shared utilities
├── bot/rosey/     # Main application
└── examples/      # Reference implementations
```

Benefits:

- No installation step
- Edit library directly
- Single source tree
- Easier debugging

## Conventions

### Naming
- Classes: `PascalCase`
- Functions/methods: `snake_case`
- Private methods: `_leading_underscore`
- Constants: `UPPER_CASE`

### Async
- Prefix async functions with `async def`
- Always `await` coroutines
- Use `asyncio.create_task()` for background tasks

### Logging
- Use `self.logger` in Bot subclasses
- Log levels: DEBUG, INFO, WARNING, ERROR
- Include context in log messages

### Documentation
- Docstrings for public APIs
- Comments for complex logic
- README for usage instructions
