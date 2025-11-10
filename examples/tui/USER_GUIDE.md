# CyTube TUI Chat Client - User Guide

A terminal-based chat client for CyTube channels, inspired by classic IRC clients like BitchX and IRCII.

## Table of Contents
- [Getting Started](#getting-started)
- [Basic Usage](#basic-usage)
- [Interface Overview](#interface-overview)
- [Commands Reference](#commands-reference)
- [Keybindings](#keybindings)
- [Themes](#themes)
- [Configuration](#configuration)
- [Tips & Tricks](#tips--tricks)

## Getting Started

### Installation

1. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

2. (Optional) Install PyYAML for YAML config support:
   ```bash
   pip install pyyaml
   ```

### First Run

1. **Create your config file:**
   ```bash
   cp examples/tui/config.yaml examples/tui/my_config.yaml
   ```

2. **Edit the config** (see [CONFIG.md](CONFIG.md) for all options)

3. **Run the TUI:**
   ```bash
   python -m examples.tui.bot examples/tui/my_config.yaml
   ```

## Basic Usage

### Sending Messages

Simply type your message and press **Enter**. Your message will appear in the chat with your username.

### Using Commands

Commands start with a forward slash (`/`). For example:
```
/help          - Show available commands
/pm Alice Hey! - Send a private message to Alice
/theme hal9000 - Change to the HAL 9000 theme
```

### Tab Completion

Press **Tab** to auto-complete:
- Usernames (start typing and press Tab)
- Channel emotes (type `#` followed by emote name)

### Scrolling

- **Page Up/Page Down** - Scroll through chat history
- **Ctrl+Up/Down** - Alternative scroll keys
- `/scroll` - Jump to bottom of chat

### Command History

- **Up Arrow** - Previous command
- **Down Arrow** - Next command

## Interface Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│ 📺 420Grindhouse                            🕐 07:15:42 PM         │ Top Status Bar
├─────────────────────────────────────────────────────────┬───────────┤
│                                                          │  Users    │
│  [19:15] Alice: Hey everyone!                           │           │
│  [19:16] Bob: What's playing?                           │  @Alice   │
│  [19:16] * Charlie waves                                │  +Bob     │
│  [PM->] Alice: Hi there!                                │  Charlie  │
│                                                          │  Dave     │
│                                                          │  Eve [AFK]│
│                                                          │           │
├─────────────────────────────────────────────────────────┴───────────┤
│ ▶ Movie Title (1h 23m)  │  👥 5/7  │  ⏱ Runtime: 45m 23s          │ Bottom Status
├─────────────────────────────────────────────────────────────────────┤
│ > Type your message here...                                         │ Input Line
└─────────────────────────────────────────────────────────────────────┘
```

### Layout Components

**Top Status Bar:**
- Left: Channel name with 📺 icon
- Right: Current time (12h or 24h format)

**Main Chat Area:**
- Scrollable message history (up to 1000 messages)
- Timestamps in [HH:MM] format
- Color-coded usernames by rank
- Private messages in magenta with [PM->] or [PM<-] prefix
- System messages in cyan

**User List (Right Side):**
- Sorted by rank: Moderators, Regular Users, AFK Users
- Rank indicators: `@` (moderator), `+` (registered), ` ` (guest)
- Status indicators: `[AFK]`, `[MUTED]`, `[LEADER]`
- Alphabetically sorted within each group

**Bottom Status Bar:**
- Current media title and duration
- User count (chat users / total viewers)
- Playback information (runtime, remaining time)
- Your username with 👤 icon

**Input Line:**
- Type messages and commands here
- `>` prompt indicates ready for input
- Supports command history and tab completion

## Commands Reference

### General Commands

#### `/help` or `/h`
Show the help message with all available commands.

#### `/info`
Display information about your connection and the channel:
- Your username and rank
- AFK status
- Channel name
- User counts
- Playlist statistics
- Currently playing media

#### `/status`
Show connection and uptime information:
- Session uptime
- Connection status
- Server address
- Channel leader
- Playback state (playing/paused)

#### `/theme [name]`
Manage color themes.
- No argument: List all available themes with descriptions
- With theme name: Switch to that theme and save preference

Example:
```
/theme           - List themes
/theme hal9000   - Switch to HAL 9000 theme
```

#### `/quit` or `/q`
Exit the chat client cleanly.

### User Commands

#### `/users`
List all users currently in the channel, sorted by rank and showing status flags.

Example output:
```
━━━ Users in Channel (8) ━━━
  [3.0] Alice [LEADER]
  [2.0] Bob
  [1.0] Charlie
  [0.0] Dave
  [0.0] Eve [AFK]
```

#### `/user <name>`
Show detailed information about a specific user:
- Username
- Rank level
- AFK status
- Muted status
- Leader status (if applicable)

Example:
```
/user Alice
```

#### `/afk [on|off]`
Set your AFK (Away From Keyboard) status.
- No argument: Shows current status
- `on`, `yes`, `true`, `1`: Set AFK
- `off`, `no`, `false`, `0`: Clear AFK

Examples:
```
/afk          - Check status
/afk on       - Set AFK
/afk off      - Clear AFK
```

### Chat Commands

#### `/pm <user> <message>`
Send a private message to a specific user.

Example:
```
/pm Alice Hey, how are you?
```

Your sent PMs appear with the `[PM->]` prefix in magenta.
Received PMs appear with the `[PM<-]` prefix.

#### `/me <action>`
Send an action message (like IRC's `/me`).

Example:
```
/me waves at everyone
```

Appears as: `* YourName waves at everyone`

#### `/clear`
Clear all chat history from your display. Does not affect other users.

#### `/scroll`
Scroll to the bottom of the chat history instantly.

#### `/togglejoins`
Toggle the display of user join and quit messages. Useful for busy channels.

### Playlist Commands

#### `/playlist [number]`
Show the playlist queue. Optional number limits how many items to display (default: 10).

The currently playing item is marked with `►`.

Example:
```
/playlist       - Show 10 items
/playlist 20    - Show 20 items
```

#### `/current` or `/np`
Show detailed information about the currently playing media:
- Title
- Duration
- Current position
- Who queued it
- Temporary or permanent

#### `/add <url> [temp]`
Add a video to the playlist.
- `url`: YouTube, Vimeo, or other supported video URL
- `temp`: Optional. `yes` (default) for temporary, `no` or `perm` for permanent

Examples:
```
/add https://youtu.be/dQw4w9WgXcQ
/add https://youtu.be/dQw4w9WgXcQ no
```

**Note**: Requires appropriate permissions in the channel.

#### `/remove <position>`
Remove an item from the playlist by its position number.

Example:
```
/remove 3       - Remove the 3rd item
```

#### `/move <from> <to>`
Move a playlist item from one position to another.

Example:
```
/move 5 2       - Move item 5 to position 2
```

#### `/jump <position>`
Jump to a specific item in the playlist and start playing it.

Example:
```
/jump 7         - Jump to and play item 7
```

### Control Commands

#### `/pause`
Pause the currently playing video.

**Note**: Requires moderator permissions.

#### `/kick <user> [reason]`
Kick a user from the channel with an optional reason.

Example:
```
/kick Spammer
/kick Troll Inappropriate behavior
```

**Note**: Requires moderator permissions.

#### `/voteskip`
Show the current voteskip status: how many votes have been cast and how many are needed.

Example output: `Voteskip: 3/5`

## Keybindings

### Essential Keys

| Key | Action |
|-----|--------|
| **Enter** | Send your message or command |
| **Tab** | Auto-complete username or emote |
| **Ctrl+C** | Force quit immediately |

### Navigation

| Key | Action |
|-----|--------|
| **Up Arrow** | Previous command in history |
| **Down Arrow** | Next command in history |
| **Page Up** | Scroll chat up |
| **Page Down** | Scroll chat down |
| **Ctrl+Up** | Alternative scroll up |
| **Ctrl+Down** | Alternative scroll down |

## Themes

The TUI includes 10 robot-themed color schemes inspired by famous movie robots!

### Available Themes

| Theme | Description | Colors |
|-------|-------------|--------|
| **default** | Original cyan theme | Cyan status bars, white text |
| **hal9000** | "I'm sorry Dave..." | Red menacing (2001) |
| **r2d2** | "Beep boop!" | Blue & white (Star Wars) |
| **c3po** | "Oh my!" | Gold & yellow (Star Wars) |
| **t800** | "I'll be back" | Red HUD, dark (Terminator) |
| **walle** | Last robot on Earth | Rusty yellow/brown |
| **robby** | Retro sci-fi classic | Cyan (Forbidden Planet) |
| **marvin** | "Brain the size of a planet" | Depressed green (Hitchhiker's Guide) |
| **johnny5** | "Number 5 is ALIVE!" | Bright friendly colors (Short Circuit) |
| **robocop** | "Serve the public trust" | Blue steel (RoboCop) |
| **data** | "Fully functional" | Yellow uniform (Star Trek: TNG) |

### Changing Themes

**In the TUI:**
```
/theme hal9000
```

**In Config File:**
```yaml
tui:
  theme: hal9000
```

Theme changes are automatically saved to your config file.

## Configuration

See [CONFIG.md](CONFIG.md) for detailed configuration options.

### Quick Config Reference

```yaml
# Connection
domain: https://cytu.be
channel: YourChannel
user:
  - YourUsername
  - your_password

# TUI Settings
tui:
  theme: robby                # Theme name
  show_join_quit: true        # Show join/quit messages
  clock_format: 12h           # 12h or 24h
  hide_afk_users: false       # Hide AFK from userlist
```

## Tips & Tricks

### For New Users

1. **Start with /help** - Get familiar with available commands
2. **Try different themes** - Use `/theme` to find one you like
3. **Use Tab completion** - Faster than typing full usernames
4. **Check /info regularly** - Stay informed about channel stats

### For Power Users

1. **Command aliases** - `/np` = `/current`, `/q` = `/quit`, `/h` = `/help`
2. **Hide AFK users** - Set `hide_afk_users: true` in config for cleaner userlist
3. **Adjust clock format** - Use 24h format if you prefer military time
4. **Command history** - Press Up to recall recent commands quickly
5. **Long messages wrap** - Messages automatically wrap with clean indentation

### For Moderators

1. **Quick user info** - Use `/user <name>` to check rank and status
2. **Playlist management** - Use `/playlist`, `/jump`, `/remove` for queue control
3. **Monitor voteskips** - Check `/voteskip` to see if a skip will pass
4. **Batch operations** - Use command history to repeat similar commands

### Troubleshooting

**Problem**: Chat is scrolled up and new messages aren't visible
- **Solution**: Press `/scroll` or Page Down to jump to bottom

**Problem**: Join/quit spam is annoying
- **Solution**: Use `/togglejoins` to hide them

**Problem**: Can't see AFK users
- **Solution**: Check if `hide_afk_users: true` in your config

**Problem**: Theme change didn't save
- **Solution**: Check file permissions on your config file

**Problem**: Tab completion not working
- **Solution**: Make sure you start typing before pressing Tab

## Advanced Features

### Message Wrapping

Long messages automatically wrap cleanly with proper indentation:
```
[19:15] Alice: This is a really long message that will wrap
              to the next line with proper indentation so 
              it's easy to read and looks nice.
```

### User List Sorting

The user list is intelligently sorted:
1. **Moderators** (rank ≥ 2) - Alphabetically
2. **Regular Users** (rank < 2) - Alphabetically  
3. **AFK Users** - Alphabetically (can be hidden)

### Colored Usernames

Usernames are consistently colored based on their rank:
- **Owners/Admins** - Bright yellow
- **Moderators** - Bright yellow
- **Registered Users** - Green
- **Guests** - White

### Real-time Updates

Status bars update every second with:
- Current time
- Media playback progress
- Session duration
- User counts

## Support & Contributing

For issues, feature requests, or contributions, please see the main project README.

---

**Enjoy your CyTube experience! 🎬🤖**
