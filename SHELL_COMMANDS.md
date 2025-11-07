# CyTube Bot Control Shell - Command Reference

The bot shell has been upgraded to a dedicated command-based control interface. It no longer evaluates arbitrary Python code - instead, it provides pre-made commands for all bot operations.

## Two Ways to Control the Bot

### 1. Via Telnet/Shell Connection

Connect directly to the shell server:

```bash
telnet 127.0.0.1 8081
```

Or use any telnet client, netcat, or even:
```python
import socket
s = socket.create_connection(('127.0.0.1', 8081))
```

### 2. Via Private Message (PM)

**Moderators (rank 2.0+)** can send commands directly to the bot via PM in the CyTube channel!

Simply send a PM to the bot with any command (without the `>` prompt):

- PM the bot: `info`
- PM the bot: `playlist 5`
- PM the bot: `add https://youtube.com/watch?v=... yes`
- PM the bot: `kick SpamUser Flooding the chat`

The bot will respond with the command results via PM. This allows moderators to control the bot without needing telnet access!

**Requirements for PM commands:**

- User must have rank 2.0 or higher (moderators)
- Commands are the same as shell commands
- Responses are sent back via PM
- Long responses are automatically split into multiple PMs
- Non-moderators' PMs are ignored (no response to avoid spam)

## Available Commands

### Connection & Info

- **help** - Show all available commands
- **exit** / **quit** - Close the connection
- **info** - Show bot name, rank, channel, user count, playlist info
- **status** - Show connection status, server, leader, playback state

### User Management

- **users** - List all users with ranks and flags (AFK, MUTED, LEADER)
- **user \<name\>** - Show detailed info about a specific user
  - Example: `user Alice`
- **afk [on|off]** - Set or show bot's AFK status
  - Example: `afk on`

### Chat Commands

- **say \<message\>** - Send a message to channel chat
  - Example: `say Hello everyone!`
- **pm \<user\> \<message\>** - Send a private message
  - Example: `pm Bob How are you doing?`
- **clear** - Clear the chat (requires permission)

### Playlist Management

- **playlist [n]** - Show playlist (optionally limit to n items)
  - Example: `playlist` (shows 10 items)
  - Example: `playlist 20` (shows 20 items)
- **current** - Show detailed info about currently playing item
- **add \<url\> [temp]** - Add media to playlist
  - Example: `add https://youtube.com/watch?v=dQw4w9WgXcQ`
  - Example: `add https://youtube.com/watch?v=dQw4w9WgXcQ no` (permanent)
  - temp can be: yes/no, true/false, 1/0, or perm
- **remove \<#\>** - Remove item by position number
  - Example: `remove 3` (removes 3rd item)
- **move \<from\> \<to\>** - Move item from one position to another
  - Example: `move 5 2` (moves 5th item to position 2)
- **jump \<#\>** - Jump to item at position
  - Example: `jump 7` (start playing 7th item)
- **next** - Skip to next item in playlist

### Channel Control

- **leader [user]** - Set or show leader
  - Example: `leader` (show current leader)
  - Example: `leader Alice` (make Alice the leader)
  - Example: `leader none` (remove leader)
- **pause** - Pause playback (must be leader)
- **kick \<user\> [reason]** - Kick a user from channel
  - Example: `kick Bob`
  - Example: `kick Bob Spamming the chat`
- **voteskip** - Show current voteskip count

## Example Session

```
> help
[help text displays]

> info
Bot: MyBot
Rank: 3.0
AFK: No
Channel: mychannel
Users: 15
Playlist: 42 items
Now playing: Cool Song

> users
Users in channel (15):
  [5.0] Admin [LEADER]
  [3.0] MyBot
  [2.0] Moderator
  [1.0] Alice [AFK]
  [1.0] Bob
  ...

> say Hello everyone!
Sent: Hello everyone!

> playlist 5
Playlist (42 items):
► 1. Cool Song (180s)
  2. Another Video (240s)
  3. Third Item (200s)
  4. Fourth Thing (300s)
  5. Fifth Media (150s)
  ... and 37 more

> current
Title: Cool Song
Duration: 180s
Queued by: Alice
URL: https://youtube.com/watch?v=...
Temporary: Yes
Status: Playing
Position: 45s

> add https://youtube.com/watch?v=example yes
Added: https://youtube.com/watch?v=example (temporary)

> jump 10
Jumped to: Some Cool Video

> pm Bob Check out item #15!
PM sent to Bob: Check out item #15!

> voteskip
Voteskip: 3/8

> exit
Goodbye!
```

## Example PM Session (Moderator)

As a moderator, you can PM the bot directly in the channel:

**You PM bot:** `info`
**Bot PMs back:**

```text
Bot: MyBot
Rank: 3.0
AFK: No
Channel: mychannel
Users: 15
Playlist: 42 items
Now playing: Cool Song
```

**You PM bot:** `playlist 3`
**Bot PMs back:**

```text
Playlist (42 items):
► 1. Cool Song (180s)
  2. Another Video (240s)
  3. Third Item (200s)
  ... and 39 more
```

**You PM bot:** `add https://youtube.com/watch?v=example yes`
**Bot PMs back:**

```text
Added: https://youtube.com/watch?v=example (temporary)
```

**You PM bot:** `kick SpamUser Please stop spamming`
**Bot PMs back:**

```text
Kicked SpamUser: Please stop spamming
```

This makes moderating much easier - no need to leave the channel or use telnet!

## Error Handling

All commands handle errors gracefully:

```
> remove 999
Position must be between 1 and 42

> kick NonExistentUser
Error: no user with name "NonExistentUser"

> add not-a-valid-url
Failed to add media: Invalid URL format
```

## Notes

- Commands are case-insensitive for the command word
- Arguments preserve case (usernames, messages, etc.)
- No more arbitrary Python code evaluation
- All operations use proper bot methods with error handling
- Permission errors are caught and reported clearly
- The shell is much safer and easier to use!

### PM Command Notes

- Only moderators (rank 2.0+) can use PM commands
- Non-moderators are silently ignored (no response)
- PM commands are logged for audit purposes
- Long responses are automatically chunked to avoid PM length limits
- All commands work the same via PM as via telnet shell
