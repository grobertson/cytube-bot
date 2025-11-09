#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A command-based control shell for the CyTube bot"""
import asyncio
import logging
from lib import MediaLink


class Shell:
    '''Command-based control shell for the bot.'''
    logger = logging.getLogger(__name__)
    
    @staticmethod
    def format_duration(seconds):
        """Format seconds into human-readable duration"""
        if seconds < 0:
            return "Unknown"
        
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if secs > 0 or not parts:
            parts.append(f"{secs}s")
        
        return ' '.join(parts)
    
    WELCOME = """
================================================================
            CyTube Bot Control Shell
================================================================

Connected! Type 'help' for available commands, 'exit' to quit.

"""

    HELP_TEXT = """
Bot Commands:
───────────────────────────────
Info:
 help - Show commands
 info - Bot & channel
 status - Connection
 stats - Database stats

Users:
 users - List all
 user <name> - User info
 afk [on|off] - Set AFK

Chat:
 say <msg> - Chat msg
 pm <u> <msg> - Private msg

Playlist:
 playlist [n] - Show queue
 current - Now playing
 add <url> [t] - Add video
 remove <#> - Delete item
 move <#> <#> - Reorder
 jump <#> - Jump to
 next - Skip video

Control:
 pause - Pause vid
 kick <u> [r] - Kick user
 voteskip - Skip vote

Examples:
 say Hello everyone!
 add youtu.be/xyz yes
 playlist 5
 kick Bob Spamming
───────────────────────────────
"""

    def __init__(self, addr, bot, loop=None):
        ''' Initialize the shell server
        
        Args:
            addr: Address string in format "host:port" or None to disable shell
            bot: lib.Bot instance to interact with
            loop: asyncio event loop (optional, will create one if not provided)
        '''
        # If no address provided, disable the shell
        if addr is None:
            self.logger.warning('shell is disabled')
            self.host = None
            self.port = None
            self.loop = None
            self.bot = None
            self.server_coro = None
            return

        # Parse the address string into host and port
        self.host, self.port = addr.rsplit(':')
        self.port = int(self.port)
        
        # Get or create an event loop
        if loop is None:
            try:
                # Try to get the currently running event loop
                loop = asyncio.get_running_loop()
            except RuntimeError:
                # No loop running, create a new one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        self.loop = loop
        self.bot = bot

        # Create the server coroutine (not started yet)
        self.logger.info('starting shell at %s:%d', self.host, self.port)
        self.server_coro = asyncio.start_server(
            self.handle_connection,  # Handler for each connection
            self.host, self.port
        )
        self.server = None
        self.server_task = None

    @staticmethod
    async def write(writer, string):
        ''' Write a string to the client, converting line endings for telnet compatibility
        
        Args:
            writer: asyncio StreamWriter to write to
            string: String to send to the client
        '''
        # Convert LF to CRLF for better telnet compatibility (especially Windows)
        string = string.replace('\n', '\r\n')
        writer.write(string.encode('utf-8'))
        await writer.drain()  # Wait for data to be sent

    async def start(self):
        ''' Start the shell server (must be called from async context)
        
        This actually starts listening for connections after __init__ set up the coroutine.
        '''
        if self.server_coro is not None:
            self.server = await self.server_coro
            self.server_task = asyncio.create_task(self.server.wait_closed())
    
    def close(self):
        ''' Close the shell server and cancel any running tasks '''
        if self.server is not None:
            self.logger.info('closing shell server')
            self.server.close()
        if self.server_task is not None:
            self.logger.info('cancel shell task')
            self.server_task.cancel()

    async def handle_pm_command(self, event, data):
        """Handle commands sent via PM from moderators
        
        Args:
            event: Event name ('pm')
            data: PM data containing username, msg, etc.
            
        Returns:
            None - responses are sent back via PM
        """
        # Extract data from PM
        username = data.get('username', '')
        message = data.get('msg', '').strip()
        
        # Ignore empty messages
        if not message:
            return
        
        # Ignore PMs from ourselves (prevents infinite error loops)
        bot = self.bot
        if username == bot.user.name:
            self.logger.debug('Ignoring PM from self')
            return
        
        # Get the user object
        if not bot.channel or username not in bot.channel.userlist:
            self.logger.warning('PM from unknown user: %s', username)
            return
        
        user = bot.channel.userlist[username]
        
        # Check if user is a moderator (rank 2.0+)
        if user.rank < 2.0:
            self.logger.info('PM command from non-moderator %s: %s',
                           username, message)
            # Don't respond to non-moderators to avoid spam
            return
        
        self.logger.info('PM command from %s: %s', username, message)
        
        # Log PM command in database
        if bot.db:
            bot.db.log_user_action(username, 'pm_command', message)
        
        # Process the command
        try:
            result = await self.handle_command(message, bot)
            
            # Send response back via PM
            if result:
                # Split long responses into multiple messages
                max_length = 500
                lines = result.split('\n')
                current_chunk = []
                current_length = 0
                
                for line in lines:
                    line_length = len(line) + 1  # +1 for newline
                    if current_length + line_length > max_length and current_chunk:
                        # Send current chunk
                        response = '\n'.join(current_chunk)
                        await bot.pm(username, response)
                        current_chunk = [line]
                        current_length = line_length
                    else:
                        current_chunk.append(line)
                        current_length += line_length
                
                # Send remaining chunk
                if current_chunk:
                    response = '\n'.join(current_chunk)
                    await bot.pm(username, response)
            
        except Exception as e:
            self.logger.error('Error processing PM command: %s', e,
                            exc_info=True)
            try:
                await bot.pm(username, f"Error: {e}")
            except Exception:
                pass  # Don't fail if we can't send error message

    async def handle_command(self, cmd, bot):
        """Handle bot control commands
        
        Args:
            cmd: The command string to process
            bot: The bot instance to control
            
        Returns:
            String response
        """
        # Parse command and arguments
        parts = cmd.strip().split(None, 1)
        if not parts:
            return None
        
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        try:
            # === Connection & Info Commands ===
            if command == 'help':
                return self.HELP_TEXT
            
            elif command == 'info':
                return await self.cmd_info(bot)
            
            elif command == 'status':
                return await self.cmd_status(bot)
            
            elif command == 'stats':
                return await self.cmd_stats(bot)
            
            # === User Management ===
            elif command == 'users':
                return await self.cmd_users(bot)
            
            elif command == 'user':
                return await self.cmd_user(bot, args)
            
            elif command == 'afk':
                return await self.cmd_afk(bot, args)
            
            # === Chat Commands ===
            elif command == 'say':
                return await self.cmd_say(bot, args)
            
            elif command == 'pm':
                return await self.cmd_pm(bot, args)
            
            elif command == 'clear':
                return await self.cmd_clear(bot)
            
            # === Playlist Management ===
            elif command == 'playlist':
                return await self.cmd_playlist(bot, args)
            
            elif command == 'current':
                return await self.cmd_current(bot)
            
            elif command == 'add':
                return await self.cmd_add(bot, args)
            
            elif command == 'remove':
                return await self.cmd_remove(bot, args)
            
            elif command == 'move':
                return await self.cmd_move(bot, args)
            
            elif command == 'jump':
                return await self.cmd_jump(bot, args)
            
            elif command == 'next':
                return await self.cmd_next(bot)
            
            # === Channel Control ===
            elif command == 'pause':
                return await self.cmd_pause(bot)
            
            elif command == 'kick':
                return await self.cmd_kick(bot, args)
            
            elif command == 'voteskip':
                return await self.cmd_voteskip(bot)
            
            else:
                return f"Unknown command: {command}\nType 'help' for available commands"
                
        except Exception as e:
            self.logger.error('Command error: %s', e, exc_info=True)
            return f"Error: {e}"
    
    # === Command Implementations ===
    
    async def cmd_info(self, bot):
        """Show bot and channel information"""
        info = []
        info.append(f"Bot: {bot.user.name}")
        info.append(f"Rank: {bot.user.rank}")
        info.append(f"AFK: {'Yes' if bot.user.afk else 'No'}")
        if bot.channel:
            info.append(f"Channel: {bot.channel.name}")
            
            # Show both chat users and total connected viewers
            chat_users = len(bot.channel.userlist)
            total_viewers = bot.channel.userlist.count
            if total_viewers and total_viewers != chat_users:
                info.append(f"Users: {chat_users} in chat, "
                          f"{total_viewers} connected")
            else:
                info.append(f"Users: {chat_users}")
            
            if bot.channel.playlist:
                total = len(bot.channel.playlist.queue)
                info.append(f"Playlist: {total} items")
                # Calculate total playlist duration from queue items
                total_time = sum(item.duration for item in bot.channel.playlist.queue)
                if total_time > 0:
                    duration = self.format_duration(total_time)
                    info.append(f"Duration: {duration}")
                if bot.channel.playlist.current:
                    info.append(f"Now playing: "
                               f"{bot.channel.playlist.current.title}")
        return '\n'.join(info)
    
    async def cmd_status(self, bot):
        """Show connection status"""
        import time
        status = []
        
        # Bot uptime
        if hasattr(bot, 'start_time') and bot.start_time:
            uptime = time.time() - bot.start_time
            status.append(f"Uptime: {self.format_duration(uptime)}")
        
        # Connection status and duration
        status.append(f"Connected: {'Yes' if bot.socket else 'No'}")
        if bot.socket:
            status.append(f"Server: {bot.server}")
            if hasattr(bot, 'connect_time') and bot.connect_time:
                conn_duration = time.time() - bot.connect_time
                status.append(f"Conn time: {self.format_duration(conn_duration)}")
        
        if bot.channel:
            status.append(f"Channel: {bot.channel.name}")
            if bot.channel.userlist.leader:
                status.append(f"Leader: {bot.channel.userlist.leader.name}")
            if bot.channel.playlist:
                paused = bot.channel.playlist.paused
                status.append(f"Playback: {'Paused' if paused else 'Playing'}")
        return '\n'.join(status)
    
    async def cmd_stats(self, bot):
        """Show database statistics"""
        if not bot.db:
            return "Database tracking is not enabled"
        
        import datetime
        stats = []
        
        # Current viewer stats
        if bot.channel:
            chat_users = len(bot.channel.userlist)
            total_viewers = bot.channel.userlist.count
            if total_viewers and total_viewers != chat_users:
                stats.append(f"Current: {chat_users} in chat, "
                           f"{total_viewers} connected")
            else:
                stats.append(f"Current: {chat_users} users")
        
        # High water marks
        max_users, max_timestamp = bot.db.get_high_water_mark()
        if max_timestamp:
            dt = datetime.datetime.fromtimestamp(max_timestamp)
            date_str = dt.strftime('%Y-%m-%d %H:%M')
            stats.append(f"Peak (chat): {max_users} ({date_str})")
        else:
            stats.append(f"Peak (chat): {max_users}")
        
        max_connected, max_conn_timestamp = bot.db.get_high_water_mark_connected()
        if max_conn_timestamp:
            dt = datetime.datetime.fromtimestamp(max_conn_timestamp)
            date_str = dt.strftime('%Y-%m-%d %H:%M')
            stats.append(f"Peak (connected): {max_connected} ({date_str})")
        elif max_connected:
            stats.append(f"Peak (connected): {max_connected}")
        
        # Total users seen
        total_users = bot.db.get_total_users_seen()
        stats.append(f"Total seen: {total_users}")
        
        # Top chatters
        top_chatters = bot.db.get_top_chatters(5)
        if top_chatters:
            stats.append("\nTop chatters:")
            for i, (username, count) in enumerate(top_chatters, 1):
                stats.append(f"  {i}. {username}: {count} msg")
        
        return '\n'.join(stats)
    
    async def cmd_users(self, bot):
        """List all users in channel"""
        if not bot.channel or not bot.channel.userlist:
            return "No users information available"
        
        users = []
        for user in sorted(bot.channel.userlist.values(),
                          key=lambda u: u.rank, reverse=True):
            flags = []
            if user.afk:
                flags.append("AFK")
            if user.muted:
                flags.append("MUTED")
            if bot.channel.userlist.leader == user:
                flags.append("LEADER")
            
            flag_str = f" [{', '.join(flags)}]" if flags else ""
            users.append(f"  [{user.rank}] {user.name}{flag_str}")
        
        return f"Users in channel ({len(users)}):\n" + '\n'.join(users)
    
    async def cmd_user(self, bot, username):
        """Show detailed info about a user"""
        if not username:
            return "Usage: user <username>"
        
        if not bot.channel or username not in bot.channel.userlist:
            return f"User '{username}' not found"
        
        user = bot.channel.userlist[username]
        info = []
        info.append(f"User: {user.name}")
        info.append(f"Rank: {user.rank}")
        info.append(f"AFK: {'Yes' if user.afk else 'No'}")
        info.append(f"Muted: {'Yes' if user.muted else 'No'}")
        if user.ip:
            info.append(f"IP: {user.ip}")
            if user.uncloaked_ip:
                info.append(f"Uncloaked: {user.uncloaked_ip}")
        if user.aliases:
            info.append(f"Aliases: {', '.join(user.aliases)}")
        if bot.channel.userlist.leader == user:
            info.append("Status: LEADER")
        
        # Add database stats if available
        if bot.db:
            user_stats = bot.db.get_user_stats(username)
            if user_stats:
                info.append(f"\nChat msgs: {user_stats['total_chat_lines']}")
                conn_time = user_stats['total_time_connected']
                info.append(f"Time: {self.format_duration(conn_time)}")
        
        return '\n'.join(info)
    
    async def cmd_afk(self, bot, args):
        """Set bot AFK status"""
        if not args:
            return f"Current AFK status: {'On' if bot.user.afk else 'Off'}"
        
        args_lower = args.lower()
        if args_lower in ('on', 'yes', 'true', '1'):
            await bot.set_afk(True)
            return "AFK status: On"
        elif args_lower in ('off', 'no', 'false', '0'):
            await bot.set_afk(False)
            return "AFK status: Off"
        else:
            return "Usage: afk [on|off]"
    
    async def cmd_say(self, bot, message):
        """Send a chat message"""
        if not message:
            return "Usage: say <message>"
        
        await bot.chat(message)
        return f"Sent: {message}"
    
    async def cmd_pm(self, bot, args):
        """Send a private message"""
        parts = args.split(None, 1)
        if len(parts) < 2:
            return "Usage: pm <user> <message>"
        
        username, message = parts
        await bot.pm(username, message)
        return f"PM sent to {username}: {message}"
    
    async def cmd_clear(self, bot):
        """Clear chat"""
        await bot.clear_chat()
        return "Chat cleared"
    
    async def cmd_playlist(self, bot, args):
        """Show playlist"""
        if not bot.channel or not bot.channel.playlist:
            return "No playlist information available"
        
        # Parse optional limit argument
        limit = 10
        if args:
            try:
                limit = int(args)
            except ValueError:
                return "Usage: playlist [number]"
        
        queue = bot.channel.playlist.queue
        items = []
        for i, item in enumerate(queue[:limit], 1):
            marker = "► " if item == bot.channel.playlist.current else "  "
            duration = self.format_duration(item.duration)
            items.append(f"{marker}{i}. {item.title} ({duration})")
        
        result = f"Playlist ({len(queue)} items):\n" + '\n'.join(items)
        if len(queue) > limit:
            result += f"\n  ... and {len(queue) - limit} more"
        
        return result
    
    async def cmd_current(self, bot):
        """Show currently playing item"""
        if not bot.channel or not bot.channel.playlist:
            return "No playlist information available"
        
        current = bot.channel.playlist.current
        if not current:
            return "Nothing is currently playing"
        
        info = []
        info.append(f"Title: {current.title}")
        duration = self.format_duration(current.duration)
        info.append(f"Duration: {duration}")
        info.append(f"Queued by: {current.username}")
        info.append(f"URL: {current.link.url}")
        info.append(f"Temporary: {'Yes' if current.temp else 'No'}")
        
        paused = bot.channel.playlist.paused
        current_time = bot.channel.playlist.current_time
        info.append(f"Status: {'Paused' if paused else 'Playing'}")
        info.append(f"Position: {current_time}s")
        
        return '\n'.join(info)
    
    async def cmd_add(self, bot, args):
        """Add media to playlist"""
        parts = args.split()
        if not parts:
            return "Usage: add <url> [temp]  (temp: yes/no, default=yes)"
        
        url = parts[0]
        temp = True
        
        if len(parts) > 1:
            temp_arg = parts[1].lower()
            if temp_arg in ('no', 'false', '0', 'perm'):
                temp = False
        
        try:
            link = MediaLink.from_url(url)
            await bot.add_media(link, append=True, temp=temp)
            return f"Added: {url} ({'temporary' if temp else 'permanent'})"
        except Exception as e:
            return f"Failed to add media: {e}"
    
    async def cmd_remove(self, bot, args):
        """Remove item from playlist"""
        if not args:
            return "Usage: remove <position>"
        
        try:
            pos = int(args)
        except ValueError:
            return "Invalid position number"
        
        if not bot.channel or not bot.channel.playlist:
            return "No playlist available"
        
        queue = bot.channel.playlist.queue
        if pos < 1 or pos > len(queue):
            return f"Position must be between 1 and {len(queue)}"
        
        item = queue[pos - 1]
        await bot.remove_media(item)
        return f"Removed: {item.title}"
    
    async def cmd_move(self, bot, args):
        """Move playlist item"""
        parts = args.split()
        if len(parts) < 2:
            return "Usage: move <from_pos> <to_pos>"
        
        try:
            from_pos = int(parts[0])
            to_pos = int(parts[1])
        except ValueError:
            return "Invalid position numbers"
        
        if not bot.channel or not bot.channel.playlist:
            return "No playlist available"
        
        queue = bot.channel.playlist.queue
        if from_pos < 1 or from_pos > len(queue):
            return f"From position must be between 1 and {len(queue)}"
        if to_pos < 1 or to_pos > len(queue):
            return f"To position must be between 1 and {len(queue)}"
        
        from_item = queue[from_pos - 1]
        # After position in CyTube is the item before the target position
        after_item = queue[to_pos - 2] if to_pos > 1 else None
        
        if after_item:
            await bot.move_media(from_item, after_item)
        else:
            # Move to beginning - no "after" item
            return "Moving to beginning not yet supported"
        
        return f"Moved {from_item.title} from position {from_pos} to {to_pos}"
    
    async def cmd_jump(self, bot, args):
        """Jump to playlist item"""
        if not args:
            return "Usage: jump <position>"
        
        try:
            pos = int(args)
        except ValueError:
            return "Invalid position number"
        
        if not bot.channel or not bot.channel.playlist:
            return "No playlist available"
        
        queue = bot.channel.playlist.queue
        if pos < 1 or pos > len(queue):
            return f"Position must be between 1 and {len(queue)}"
        
        item = queue[pos - 1]
        await bot.set_current_media(item)
        return f"Jumped to: {item.title}"
    
    async def cmd_next(self, bot):
        """Skip to next item"""
        if not bot.channel or not bot.channel.playlist:
            return "No playlist available"
        
        current = bot.channel.playlist.current
        if not current:
            return "Nothing is currently playing"
        
        queue = bot.channel.playlist.queue
        try:
            current_idx = queue.index(current)
            if current_idx + 1 < len(queue):
                next_item = queue[current_idx + 1]
                await bot.set_current_media(next_item)
                return f"Skipped to: {next_item.title}"
            else:
                return "Already at last item"
        except ValueError:
            return "Current item not in queue"
    
    async def cmd_pause(self, bot):
        """Pause playback"""
        await bot.pause()
        return "Paused"
    
    async def cmd_kick(self, bot, args):
        """Kick a user"""
        parts = args.split(None, 1)
        if not parts:
            return "Usage: kick <user> [reason]"
        
        username = parts[0]
        reason = parts[1] if len(parts) > 1 else ""
        
        await bot.kick(username, reason)
        return f"Kicked {username}" + (f": {reason}" if reason else "")
    
    async def cmd_voteskip(self, bot):
        """Show voteskip status"""
        if not bot.channel:
            return "No channel information available"
        
        count = bot.channel.voteskip_count
        need = bot.channel.voteskip_need
        return f"Voteskip: {count}/{need}"

    async def handle_connection(self, reader, writer):
        ''' Handle a single client connection to the shell
        
        Args:
            reader: asyncio StreamReader for reading client input
            writer: asyncio StreamWriter for sending responses
        '''
        try:
            bot = self.bot

            self.logger.info('accepted shell connection')
            
            # Send welcome message
            await self.write(writer, self.WELCOME)
            await self.write(writer, "Type 'help' for commands\n")

            while True:
                # Show command prompt
                await self.write(writer, '> ')
                line = await reader.readline()
                
                # Check for EOF (connection closed)
                if not line:
                    break
                
                # Decode with error handling
                try:
                    line = line.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        line = line.decode('latin-1')
                    except Exception as e:
                        await self.write(writer,
                                        f'Error decoding input: {e}\n')
                        continue
                
                # Clean up the line
                cmd = line.strip()
                
                # Check for exit commands
                if cmd.lower() in ('exit', 'quit'):
                    self.logger.info('exiting shell')
                    await self.write(writer, '\nGoodbye!\n')
                    break

                # Skip empty commands
                if not cmd:
                    continue

                try:
                    # Process command
                    result = await self.handle_command(cmd, bot)
                    if result:
                        await self.write(writer, f'{result}\n')
                    
                except asyncio.CancelledError:
                    raise
                    
                except Exception as ex:
                    error_msg = f'Error: {ex}\n'
                    await self.write(writer, error_msg)
                    self.logger.error('Command error: %s', ex,
                                     exc_info=True)

        except (IOError, ConnectionResetError) as ex:
            self.logger.info('connection closed: %s', ex)
        except asyncio.CancelledError:
            self.logger.info('shell connection cancelled')
        except Exception as ex:
            self.logger.error('unexpected error in shell: %s', ex)
            self.logger.debug('traceback:', exc_info=True)
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except AttributeError:
                pass
            self.logger.info('closed shell connection')

