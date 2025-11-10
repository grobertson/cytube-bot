#!/usr/bin/env python3
"""CyTube TUI Chat Client - A terminal-based chat interface inspired by BitchX/IRCII.

This module provides a full-featured text user interface for CyTube chat rooms,
combining the nostalgic feel of classic IRC clients with modern terminal capabilities.

Features:
    - Full-color terminal interface using blessed
    - Scrollable chat history with username colorization
    - Real-time user list with rank indicators
    - Command-line input with history
    - Support for private messages
    - Media notifications
    - Status bar with connection info
    - Configurable color schemes

Usage:
    python -m bots.tui.bot config.json

Keybindings:
    - Enter: Send message
    - Up/Down: Navigate command history
    - Page Up/Down: Scroll chat history
    - Ctrl+C: Quit
    - Alt+1-9: Switch windows (future)
"""

import sys
import os
from pathlib import Path
from collections import deque
from datetime import datetime
import asyncio
import logging

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from blessed import Terminal

from lib import Bot, MessageParser
from lib.error import CytubeError, SocketIOError

from common import get_config


class TUIBot(Bot):
    """CyTube bot with terminal user interface.

    This bot provides a rich terminal interface for interacting with CyTube
    chat rooms, inspired by classic IRC clients like BitchX and IRCII.

    Attributes:
        term (Terminal): Blessed terminal instance for rendering
        msg_parser (MessageParser): Parses HTML messages to plain text
        chat_history (deque): Scrollable message history buffer
        user_colors (dict): Username to color mapping for consistency
        input_buffer (str): Current input line being typed
        input_history (deque): Command history for up/down navigation
        history_pos (int): Current position in command history
        scroll_offset (int): Current scroll position in chat history
        running (bool): Whether the TUI loop is active
        status_message (str): Current status bar message
    """

    # Color palette for usernames (cycling through distinct colors)
    USERNAME_COLORS = [
        'cyan', 'green', 'yellow', 'blue', 'magenta',
        'bright_cyan', 'bright_green', 'bright_yellow',
        'bright_blue', 'bright_magenta'
    ]

    # Rank symbols for user list
    RANK_SYMBOLS = {
        0: ' ',      # Guest
        1: '+',      # Registered
        2: '@',      # Moderator
        3: '%',      # Admin
        4: '~',      # Owner
        5: '&',      # Founder
    }

    def __init__(self, *args, **kwargs):
        """Initialize the TUI bot.

        Args:
            *args: Positional arguments passed to Bot.__init__
            **kwargs: Keyword arguments passed to Bot.__init__
        """
        super().__init__(*args, **kwargs)

        # Initialize terminal
        self.term = Terminal()

        # Message parsing
        self.msg_parser = MessageParser()

        # Chat history buffer (max 1000 messages)
        self.chat_history = deque(maxlen=1000)

        # Username color mapping for consistency
        self.user_colors = {}
        self._color_index = 0

        # Input handling
        self.input_buffer = ''
        self.input_history = deque(maxlen=100)
        self.history_pos = -1
        self.tab_completion_matches = []
        self.tab_completion_index = 0
        self.tab_completion_prefix = ''

        # Scrolling
        self.scroll_offset = 0

        # State
        self.running = False
        self.status_message = 'Connecting...'

        # Setup logging to file
        self._setup_logging()

        # Register event handlers
        self.on('chatMsg', self.handle_chat)
        self.on('pm', self.handle_pm)
        self.on('userlist', self.handle_userlist)
        self.on('addUser', self.handle_user_join)
        self.on('userLeave', self.handle_user_leave)
        self.on('setCurrent', self.handle_media_change)
        self.on('login', self.handle_login)

    def _setup_logging(self):
        """Setup file logging for errors and chat history."""
        # Create logs directory if it doesn't exist
        log_dir = Path(__file__).parent / 'logs'
        log_dir.mkdir(exist_ok=True)

        # Error log file
        error_log = log_dir / 'tui_errors.log'
        error_handler = logging.FileHandler(error_log, encoding='utf-8')
        error_handler.setLevel(logging.WARNING)
        error_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(error_handler)

        # Chat history log file
        chat_log = log_dir / f'chat_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        self.chat_log_file = open(chat_log, 'a', encoding='utf-8')
        self.logger.info(f'Chat logging to: {chat_log}')
        self.logger.info(f'Error logging to: {error_log}')

    def _log_chat(self, username, message, prefix=''):
        """Log a chat message to the chat history file.

        Args:
            username (str): Username of the sender
            message (str): Message content
            prefix (str, optional): Prefix for the message (e.g., '[PM]', '*')
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if prefix:
            log_line = f'[{timestamp}] {prefix} <{username}> {message}\n'
        else:
            log_line = f'[{timestamp}] <{username}> {message}\n'
        try:
            self.chat_log_file.write(log_line)
            self.chat_log_file.flush()
        except Exception as e:
            self.logger.error(f'Failed to write to chat log: {e}')

    def get_username_color(self, username):
        """Get a consistent color for a username.

        Assigns each username a color from the palette that remains consistent
        throughout the session.

        Args:
            username (str): The username to colorize

        Returns:
            str: Color name from blessed (e.g., 'cyan', 'bright_green')
        """
        if username not in self.user_colors:
            color = self.USERNAME_COLORS[self._color_index % len(self.USERNAME_COLORS)]
            self.user_colors[username] = color
            self._color_index += 1
        return self.user_colors[username]

    def add_chat_line(self, username, message, prefix='', color_override=None):
        """Add a line to the chat history buffer.

        Args:
            username (str): Username of the sender
            message (str): Message content
            prefix (str, optional): Prefix for the line (e.g., '*', '@')
            color_override (str, optional): Override the username color
        """
        timestamp = datetime.now().strftime('%H:%M:%S')
        color = color_override or self.get_username_color(username)

        self.chat_history.append({
            'timestamp': timestamp,
            'username': username,
            'message': message,
            'prefix': prefix,
            'color': color
        })

        # Auto-scroll to bottom when new message arrives
        if self.scroll_offset == 0:
            self.render_chat()
            self.render_input()

    def add_system_message(self, message, color='bright_black'):
        """Add a system message to chat history.

        Args:
            message (str): System message content
            color (str, optional): Color for the message
        """
        timestamp = datetime.now().strftime('%H:%M:%S')

        self.chat_history.append({
            'timestamp': timestamp,
            'username': '*',
            'message': message,
            'prefix': '',
            'color': color
        })

        # Log system messages too
        self._log_chat('*', message, prefix='*')

        if self.scroll_offset == 0:
            self.render_chat()
            self.render_input()

    async def handle_chat(self, _, data):
        """Handle incoming chat messages.

        Args:
            _ (str): Event name (unused)
            data (dict): Message data from CyTube
        """
        username = data.get('username', '<unknown>')
        msg = self.msg_parser.parse(data.get('msg', ''))

        self.add_chat_line(username, msg)
        self._log_chat(username, msg)

    async def handle_pm(self, _, data):
        """Handle incoming private messages.

        Args:
            _ (str): Event name (unused)
            data (dict): PM data from CyTube
        """
        username = data.get('username', '<unknown>')
        msg = self.msg_parser.parse(data.get('msg', ''))

        self.add_chat_line(username, msg, prefix='[PM]', color_override='bright_magenta')
        self._log_chat(username, msg, prefix='[PM]')

    async def handle_userlist(self, _, data):
        """Handle initial userlist event.

        Args:
            _ (str): Event name (unused)
            data (list): List of user data from CyTube
        """
        # The userlist event provides the initial list of users
        # Render the user list once it's populated
        self.render_users()

    async def handle_user_join(self, _, data):
        """Handle user join events.

        Args:
            _ (str): Event name (unused)
            data (dict): User data from CyTube
        """
        username = data.get('name', '<unknown>')
        self.add_system_message(f'{username} has joined', color='bright_green')
        self.render_users()

    async def handle_user_leave(self, _, data):
        """Handle user leave events.

        Args:
            _ (str): Event name (unused)
            data (dict): User data from CyTube
        """
        username = data.get('name', '<unknown>')
        self.add_system_message(f'{username} has left', color='bright_red')
        self.render_users()

    async def handle_media_change(self, _, data):
        """Handle media change events.

        Args:
            _ (str): Event name (unused)
            data (dict): Media data from CyTube (can be uid or PlaylistItem)
        """
        if self.channel.playlist.current:
            title = self.channel.playlist.current.title
            self.add_system_message(f'Now playing: {title}', color='bright_blue')

    async def handle_login(self, _, data):
        """Handle successful login.

        Args:
            _ (str): Event name (unused)
            data: Bot instance (self)
        """
        self.status_message = f'Connected to {self.channel.name}'
        self.render_status()

    def render_screen(self):
        """Render the complete TUI layout.

        Layout:
            ┌────────────────────────────────────────────────────────┐
            │ Status Bar (channel, users, time)                      │
            ├────────────────────────────────────────────────────────┤
            │                                                         │
            │                                                         │
            │               Chat Area (scrollable)                    │
            │                                                         │
            │                                                         │
            ├────────────────────────────────────────────────────────┤
            │ Input Line: >                                          │
            └────────────────────────────────────────────────────────┘

            User List (right side, 20 chars wide):
            ┌──────────────────────┐
            │ Users (15)           │
            │ ~owner               │
            │ @moderator           │
            │ +user1               │
            │  guest               │
            └──────────────────────┘
        """
        print(self.term.clear)
        self.render_status()
        self.render_chat()
        self.render_users()
        self.render_input()

    def render_status(self):
        """Render the status bar at the top of the screen."""
        with self.term.location(0, 0):
            # Status bar background
            status_line = self.status_message.ljust(self.term.width)
            print(self.term.black_on_cyan(status_line), end='', flush=True)

    def render_chat(self):
        """Render the chat history area with scrolling support."""
        # Calculate dimensions
        chat_height = self.term.height - 3  # Leave room for status, separator, input
        user_list_width = 22
        chat_width = self.term.width - user_list_width - 1

        # Get visible messages based on scroll offset
        total_messages = len(self.chat_history)
        start_idx = max(0, total_messages - chat_height - self.scroll_offset)
        end_idx = total_messages - self.scroll_offset
        visible_messages = list(self.chat_history)[start_idx:end_idx]

        # Render separator line
        with self.term.location(0, 1):
            print(self.term.bright_black('─' * (chat_width)), end='', flush=True)

        # Render chat messages
        for i, msg_data in enumerate(visible_messages):
            line_num = 2 + i

            with self.term.location(0, line_num):
                # Clear the line
                print(' ' * chat_width, end='')

            with self.term.location(0, line_num):
                timestamp = msg_data['timestamp']
                username = msg_data['username']
                message = msg_data['message']
                prefix = msg_data['prefix']
                color = msg_data['color']

                # Format: [HH:MM:SS] <username> message
                # or:      [HH:MM:SS] [PM] <username> message
                time_str = self.term.bright_black(f'[{timestamp}]')

                # Get the color function from terminal
                color_func = getattr(self.term, color, self.term.white)

                if prefix:
                    username_str = f'{prefix} {color_func(f"<{username}>")} '
                else:
                    username_str = f'{color_func(f"<{username}>")} '

                # Calculate max message width
                prefix_len = len(f'[{timestamp}] ')
                if prefix:
                    prefix_len += len(f'{prefix} ')
                prefix_len += len(f'<{username}> ')

                max_msg_width = chat_width - prefix_len

                # Truncate message if needed
                if len(message) > max_msg_width:
                    message = message[:max_msg_width - 3] + '...'

                print(f'{time_str} {username_str}{message}', end='', flush=True)

        # Clear any remaining lines
        for i in range(len(visible_messages), chat_height):
            line_num = 2 + i
            with self.term.location(0, line_num):
                print(' ' * chat_width, end='', flush=True)

    def render_users(self):
        """Render the user list on the right side of the screen."""
        if not self.channel or not self.channel.userlist:
            return

        user_list_width = 22
        user_list_x = self.term.width - user_list_width
        chat_height = self.term.height - 3

        # Header
        with self.term.location(user_list_x, 1):
            user_count = len(self.channel.userlist)
            header = f' Users ({user_count}) '
            header = header.ljust(user_list_width - 1)
            print(self.term.black_on_bright_white(header), end='', flush=True)

        # Vertical separator
        for i in range(2, self.term.height - 1):
            with self.term.location(user_list_x - 1, i):
                print(self.term.bright_black('│'), end='', flush=True)

        # Sort users by rank (descending) then by name
        sorted_users = sorted(
            self.channel.userlist.values(),
            key=lambda u: (-u.rank, u.name.lower())
        )

        # Render users
        for i, user in enumerate(sorted_users[:chat_height - 1]):
            line_num = 2 + i
            with self.term.location(user_list_x, line_num):
                # Get rank symbol
                rank_symbol = self.RANK_SYMBOLS.get(int(user.rank), ' ')

                # Get username color
                color = self.get_username_color(user.name)
                color_func = getattr(self.term, color, self.term.white)

                # Format: @username or  username
                user_str = f'{rank_symbol}{user.name}'

                # Truncate if too long
                max_width = user_list_width - 2
                if len(user_str) > max_width:
                    user_str = user_str[:max_width - 1] + '…'

                # Highlight leader with bold
                if self.channel.userlist.leader == user:
                    user_str = self.term.bold(user_str)

                # Dim AFK users
                if user.afk:
                    user_str = self.term.dim(user_str)

                print(f' {color_func(user_str)}'.ljust(user_list_width - 1), end='', flush=True)

        # Clear remaining lines
        for i in range(len(sorted_users), chat_height - 1):
            line_num = 2 + i
            with self.term.location(user_list_x, line_num):
                print(' ' * (user_list_width - 1), end='', flush=True)

    def render_input(self):
        """Render the input line at the bottom of the screen."""
        input_y = self.term.height - 1
        user_list_width = 22
        input_width = self.term.width - user_list_width - 1

        with self.term.location(0, input_y):
            # Clear the line
            print(' ' * input_width, end='')

        with self.term.location(0, input_y):
            # Input prompt
            prompt = self.term.bright_white('> ')
            print(prompt, end='', flush=True)

            # Calculate visible portion of input
            prompt_len = 2  # "> "
            max_input_width = input_width - prompt_len

            if len(self.input_buffer) > max_input_width:
                # Show the end of the input if it's too long
                visible_input = self.input_buffer[-(max_input_width):]
            else:
                visible_input = self.input_buffer

            print(visible_input, end='', flush=True)

    async def handle_input(self):
        """Handle keyboard input in an async loop.

        This is the main input loop that processes user keyboard input,
        including regular typing, special keys, and commands.
        """
        with self.term.cbreak(), self.term.hidden_cursor():
            while self.running:
                key = self.term.inkey(timeout=0.1)

                if not key:
                    await asyncio.sleep(0.01)
                    continue

                # Handle special keys
                if key.name == 'KEY_ENTER':
                    await self.process_command()
                elif key.name == 'KEY_TAB':
                    self.handle_tab_completion()
                elif key.name == 'KEY_BACKSPACE' or key.name == 'KEY_DELETE':
                    if self.input_buffer:
                        self.input_buffer = self.input_buffer[:-1]
                        # Reset tab completion on edit
                        self.tab_completion_matches = []
                        self.render_input()
                elif key.name == 'KEY_UP':
                    # Check for Ctrl+Up (scroll)
                    if hasattr(key, 'code') and key.code in (566, 567):  # Ctrl+Up codes
                        self.scroll_up()
                    else:
                        self.navigate_history_up()
                elif key.name == 'KEY_DOWN':
                    # Check for Ctrl+Down (scroll)
                    if hasattr(key, 'code') and key.code in (525, 526):  # Ctrl+Down codes
                        self.scroll_down()
                    else:
                        self.navigate_history_down()
                elif key.name == 'KEY_PGUP':
                    self.scroll_up()
                elif key.name == 'KEY_PGDOWN':
                    self.scroll_down()
                elif key.name == 'KEY_ESCAPE':
                    # Could be used for commands/menus in the future
                    pass
                elif key.is_sequence:
                    # Ignore other special sequences
                    pass
                else:
                    # Regular character input
                    self.input_buffer += key
                    # Reset tab completion on new input
                    self.tab_completion_matches = []
                    self.render_input()

    def handle_tab_completion(self):
        """Handle tab completion for usernames and emotes.

        Tab completion works for:
        - Usernames after '@' (e.g., @ali<TAB> -> @alice)
        - Emotes after ':' (e.g., :smi<TAB> -> :smile:)
        
        Pressing Tab multiple times cycles through matches.
        """
        if not self.input_buffer:
            return

        # If we have existing matches, cycle through them
        if self.tab_completion_matches:
            self.tab_completion_index = (self.tab_completion_index + 1) % len(self.tab_completion_matches)
            match = self.tab_completion_matches[self.tab_completion_index]
            
            # Replace from the prefix to the end
            prefix_len = len(self.tab_completion_prefix)
            self.input_buffer = self.input_buffer[:prefix_len] + match
            self.render_input()
            return

        # Find what we're trying to complete
        cursor_pos = len(self.input_buffer)
        
        # Look for @ or : before cursor
        last_at = self.input_buffer.rfind('@')
        last_colon = self.input_buffer.rfind(':')
        
        completion_type = None
        start_pos = -1
        
        # Determine completion type based on which symbol is closer to cursor
        if last_at > last_colon and last_at >= 0:
            # Username completion
            completion_type = 'username'
            start_pos = last_at
        elif last_colon >= 0:
            # Emote completion
            completion_type = 'emote'
            start_pos = last_colon
        
        if completion_type is None or start_pos == -1:
            return
        
        # Extract the partial text after the symbol
        partial = self.input_buffer[start_pos + 1:cursor_pos]
        
        # Get matches based on type
        matches = []
        if completion_type == 'username':
            matches = self._get_username_matches(partial)
        elif completion_type == 'emote':
            matches = self._get_emote_matches(partial)
        
        if not matches:
            return
        
        # Store matches and prefix for cycling
        self.tab_completion_matches = matches
        self.tab_completion_index = 0
        self.tab_completion_prefix = self.input_buffer[:start_pos + 1]
        
        # Apply first match
        match = matches[0]
        self.input_buffer = self.tab_completion_prefix + match
        self.render_input()

    def _get_username_matches(self, partial):
        """Get list of usernames matching the partial string.

        Args:
            partial (str): Partial username to match

        Returns:
            list: List of matching usernames
        """
        if not self.channel or not self.channel.userlist:
            return []
        
        partial_lower = partial.lower()
        matches = []
        
        for username in self.channel.userlist.keys():
            if username.lower().startswith(partial_lower):
                matches.append(username)
        
        # Sort matches alphabetically
        matches.sort(key=str.lower)
        return matches

    def _get_emote_matches(self, partial):
        """Get list of emotes matching the partial string.

        Args:
            partial (str): Partial emote name to match

        Returns:
            list: List of matching emotes (with trailing :)
        """
        # Common emotes - in a real implementation, this would come from channel config
        common_emotes = [
            'smile', 'sad', 'laugh', 'angry', 'heart', 'thumbsup', 'thumbsdown',
            'thinking', 'wave', 'party', 'fire', 'cool', 'eyes', 'shrug',
            'check', 'cross', 'question', 'exclamation', 'star', 'sparkles'
        ]
        
        partial_lower = partial.lower()
        matches = []
        
        for emote in common_emotes:
            if emote.startswith(partial_lower):
                # Add trailing : for complete emote
                matches.append(emote + ':')
        
        return matches

    def navigate_history_up(self):
        """Navigate backward in command history (up arrow)."""
        if not self.input_history:
            return

        if self.history_pos == -1:
            # Save current input before navigating
            self._temp_input = self.input_buffer
            self.history_pos = len(self.input_history) - 1
        elif self.history_pos > 0:
            self.history_pos -= 1

        if 0 <= self.history_pos < len(self.input_history):
            self.input_buffer = self.input_history[self.history_pos]
            self.render_input()

    def navigate_history_down(self):
        """Navigate forward in command history (down arrow)."""
        if not self.input_history or self.history_pos == -1:
            return

        self.history_pos += 1

        if self.history_pos >= len(self.input_history):
            # Restore temporary input or clear
            self.input_buffer = getattr(self, '_temp_input', '')
            self.history_pos = -1
        else:
            self.input_buffer = self.input_history[self.history_pos]

        self.render_input()

    def scroll_up(self):
        """Scroll chat history up (Page Up)."""
        max_scroll = max(0, len(self.chat_history) - (self.term.height - 3))
        self.scroll_offset = min(self.scroll_offset + 10, max_scroll)
        self.render_chat()
        self.render_input()

    def scroll_down(self):
        """Scroll chat history down (Page Down)."""
        self.scroll_offset = max(0, self.scroll_offset - 10)
        self.render_chat()
        self.render_input()

    async def process_command(self):
        """Process the current input buffer as a command or message.

        Commands start with '/' and are handled specially. Regular messages
        are sent to the chat.

        Commands:
            /help - Show available commands
            /pm <user> <message> - Send private message
            /me <action> - Send action message
            /quit - Exit the application
            /clear - Clear chat history
            /scroll - Toggle auto-scroll
        """
        if not self.input_buffer.strip():
            return

        # Add to history
        self.input_history.append(self.input_buffer)
        self.history_pos = -1

        # Parse command
        text = self.input_buffer.strip()
        self.input_buffer = ''
        self.render_input()

        try:
            if text.startswith('/'):
                await self.handle_slash_command(text)
            else:
                # Regular chat message
                await self.chat(text)
        except Exception as e:
            self.add_system_message(f'Error: {e}', color='bright_red')

    async def handle_slash_command(self, text):
        """Handle slash commands.

        Args:
            text (str): The command text starting with '/'
        """
        parts = text[1:].split(None, 1)
        if not parts:
            return

        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ''

        if command == 'help':
            self.show_help()
        elif command == 'pm':
            await self.handle_pm_command(args)
        elif command == 'me':
            await self.chat(f'/me {args}')
        elif command == 'quit' or command == 'exit':
            self.running = False
        elif command == 'clear':
            self.chat_history.clear()
            self.render_screen()
        elif command == 'scroll':
            self.scroll_offset = 0
            self.render_chat()
            self.render_input()
        else:
            self.add_system_message(f'Unknown command: /{command}', color='bright_red')

    async def handle_pm_command(self, args):
        """Handle /pm command.

        Args:
            args (str): Arguments in format "<username> <message>"
        """
        parts = args.split(None, 1)
        if len(parts) < 2:
            self.add_system_message('Usage: /pm <username> <message>', color='bright_red')
            return

        username, message = parts
        await self.pm(username, message)
        self.add_chat_line(
            username,
            message,
            prefix='[PM->]',
            color_override='bright_magenta'
        )

    def show_help(self):
        """Display help information about available commands."""
        help_lines = [
            'Available Commands:',
            '/help - Show this help',
            '/pm <user> <msg> - Send private message',
            '/me <action> - Send action message',
            '/clear - Clear chat history',
            '/scroll - Scroll to bottom',
            '/quit - Exit',
            '',
            'Keybindings:',
            'Enter - Send message',
            'Up/Down - Navigate history',
            'PgUp/PgDn - Scroll chat',
        ]

        for line in help_lines:
            self.add_system_message(line, color='bright_cyan')

    async def run_tui(self):
        """Run the TUI main loop.

        This creates the asyncio tasks for both the bot connection and
        the input handling, managing their lifecycle.
        """
        self.running = True

        # Initial screen render
        self.render_screen()

        # Create tasks
        input_task = asyncio.create_task(self.handle_input())
        bot_task = asyncio.create_task(self.run())

        try:
            # Wait for either task to complete
            done, pending = await asyncio.wait(
                [input_task, bot_task],
                return_when=asyncio.FIRST_COMPLETED
            )

            # Cancel remaining tasks
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        except Exception as e:
            self.add_system_message(f'Fatal error: {e}', color='bright_red')
            self.logger.exception('Fatal error in TUI')
        finally:
            self.running = False
            # Close chat log file
            if hasattr(self, 'chat_log_file'):
                try:
                    self.chat_log_file.close()
                except Exception as e:
                    self.logger.error(f'Error closing chat log: {e}')


async def run_tui_bot():
    """Run the TUI bot with proper async handling.

    This is the main entry point that loads configuration, creates the bot
    instance, and starts the TUI loop.
    """
    # Load configuration
    conf, kwargs = get_config()

    # Disable database tracking for TUI (keep it lightweight)
    kwargs['enable_db'] = False

    # Create bot instance
    bot = TUIBot(**kwargs)

    try:
        # Run the TUI
        await bot.run_tui()
    except KeyboardInterrupt:
        bot.running = False
    except (CytubeError, SocketIOError) as ex:
        print(f'\nConnection error: {ex}', file=sys.stderr)
    finally:
        # Cleanup terminal
        print(bot.term.normal)
        print(bot.term.clear)
        print('Goodbye!')


def main():
    """Main entry point for the TUI bot.

    Returns:
        int: Exit code (0 for success, 1 for error)
    """
    try:
        asyncio.run(run_tui_bot())
        return 0
    except KeyboardInterrupt:
        return 0
    except Exception as e:
        print(f'\nFatal error: {e}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
