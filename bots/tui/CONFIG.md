# TUI Configuration

The TUI bot supports both JSON and YAML configuration files.

## Using YAML (Recommended)

YAML is more human-friendly with comments and better readability:

```bash
python bots/tui/bot.py bots/tui/config.yaml
```

**Note**: Requires PyYAML: `pip install pyyaml`

## Using JSON (Original)

JSON format still works for backward compatibility:

```bash
python bots/tui/bot.py bots/tui/config.json
```

## Configuration Options

### Connection Settings
- `domain`: CyTube server URL
- `channel`: Channel name to join
- `user`: [username, password] for bot account
- `response_timeout`: Socket.IO response timeout (seconds)
- `restart_delay`: Delay before reconnecting on error (seconds)
- `log_level`: DEBUG | INFO | WARNING | ERROR | CRITICAL

### TUI Settings (`tui` section)
- `theme`: Theme name (see Themes section)
- `show_join_quit`: Show/hide join/quit messages (true/false)
- `clock_format`: `12h` (AM/PM) or `24h` (military time)
- `hide_afk_users`: Hide AFK users from userlist (true/false, default: false)

## Themes

The TUI includes 10 robot-themed color schemes inspired by famous movie robots:

| Theme | Robot | Movie/Series | Style |
|-------|-------|--------------|-------|
| `default` | - | - | Original cyan/white theme |
| `hal9000` | HAL 9000 | 2001: A Space Odyssey | Red menacing eye |
| `r2d2` | R2-D2 | Star Wars | Blue/white astromech |
| `c3po` | C-3PO | Star Wars | Golden protocol droid |
| `t800` | T-800 | Terminator | Red HUD, dark cyborg |
| `walle` | WALL-E | WALL-E | Rusty yellow/brown |
| `robby` | Robby | Forbidden Planet | Cyan retro sci-fi |
| `marvin` | Marvin | Hitchhiker's Guide | Depressed green |
| `johnny5` | Johnny 5 | Short Circuit | Bright friendly colors |
| `robocop` | RoboCop | RoboCop | Blue steel law enforcement |
| `data` | Data | Star Trek: TNG | Yellow Starfleet uniform |

Change themes with `/theme <name>` command or in config file.

## Example YAML Config

```yaml
domain: https://cytu.be
channel: 420Grindhouse
user:
  - BotUsername
  - bot_password_here
response_timeout: 1
restart_delay: 5
log_level: WARNING

tui:
  theme: hal9000  # I'm sorry Dave...
  show_join_quit: true
  clock_format: 12h
  hide_afk_users: false  # Set to true to hide AFK users
```

## Example JSON Config

```json
{
  "domain": "https://cytu.be",
  "channel": "420Grindhouse",
  "user": ["BotUsername", "bot_password_here"],
  "response_timeout": 1,
  "restart_delay": 5,
  "log_level": "WARNING",
  "tui": {
    "theme": "hal9000",
    "show_join_quit": true,
    "clock_format": "12h",
    "hide_afk_users": false
  }
}
```
