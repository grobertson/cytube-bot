#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from lib.bot import Bot
from lib.channel import Channel
from lib.user import User
from lib.playlist import PlaylistItem
from lib.error import LoginError, SocketIOError, Kicked, ChannelPermissionError
from lib.socket_io import SocketIO, SocketIOResponse


@pytest.fixture
def mock_socket():
    """Mock SocketIO instance"""
    socket = AsyncMock(spec=SocketIO)
    socket.emit = AsyncMock()
    socket.close = AsyncMock()
    socket.on = Mock()
    return socket


@pytest.fixture
def mock_socket_io_connect(mock_socket):
    """Mock SocketIO.connect coroutine"""
    async def connect(url, loop=None):
        return mock_socket
    return connect


@pytest.fixture
def mock_get():
    """Mock HTTP GET coroutine"""
    async def get(url):
        if 'socketconfig' in url:
            return json.dumps({
                'servers': [{'url': 'http://test-server.com'}]
            })
        return '{"error": "unknown url"}'
    return get


@pytest.fixture
def bot_simple():
    """Simple bot instance without DB"""
    return Bot(
        'http://test.com',
        'testchannel',
        user='testbot',
        enable_db=False
    )


@pytest.fixture
def bot_with_mocks(mock_socket_io_connect, mock_get):
    """Bot with mocked dependencies"""
    bot = Bot(
        'http://test.com',
        'testchannel',
        user='testbot',
        get=mock_get,
        socket_io=mock_socket_io_connect,
        enable_db=False
    )
    return bot


class TestBotInit:
    """Test Bot initialization"""

    def test_init_minimal(self):
        """Create bot with minimal parameters"""
        bot = Bot('http://test.com', 'testchannel', enable_db=False)
        assert bot.domain == 'http://test.com'
        assert bot.channel.name == 'testchannel'
        assert bot.channel.password is None
        assert bot.user.name == ''
        assert bot.user.password is None

    def test_init_with_channel_password(self):
        """Create bot with channel password"""
        bot = Bot('http://test.com', ('channel', 'pass123'), enable_db=False)
        assert bot.channel.name == 'channel'
        assert bot.channel.password == 'pass123'

    def test_init_with_user_guest(self):
        """Create bot with guest username"""
        bot = Bot('http://test.com', 'channel', user='guestuser', enable_db=False)
        assert bot.user.name == 'guestuser'
        assert bot.user.password is None

    def test_init_with_user_registered(self):
        """Create bot with registered user credentials"""
        bot = Bot('http://test.com', 'channel', user=('botuser', 'secret'), enable_db=False)
        assert bot.user.name == 'botuser'
        assert bot.user.password == 'secret'

    def test_init_restart_delay(self):
        """Create bot with custom restart_delay"""
        bot = Bot('http://test.com', 'channel', restart_delay=10, enable_db=False)
        assert bot.restart_delay == 10

    def test_init_no_restart(self):
        """Create bot with restart disabled (None)"""
        bot = Bot('http://test.com', 'channel', restart_delay=None, enable_db=False)
        assert bot.restart_delay is None

    def test_init_response_timeout(self):
        """Create bot with custom response_timeout"""
        bot = Bot('http://test.com', 'channel', response_timeout=0.5, enable_db=False)
        assert bot.response_timeout == 0.5

    def test_init_channel_instance(self):
        """Bot creates Channel instance"""
        bot = Bot('http://test.com', 'channel', enable_db=False)
        assert isinstance(bot.channel, Channel)
        assert bot.channel.name == 'channel'

    def test_init_user_instance(self):
        """Bot creates User instance"""
        bot = Bot('http://test.com', 'channel', user='test', enable_db=False)
        assert isinstance(bot.user, User)
        assert bot.user.name == 'test'

    def test_init_default_values(self):
        """Bot has correct default values"""
        bot = Bot('http://test.com', 'channel', enable_db=False)
        assert bot.server is None
        assert bot.socket is None
        assert bot.connect_time is None
        assert isinstance(bot.handlers, dict)
        assert bot.start_time is not None

    def test_init_auto_registers_event_handlers(self):
        """Bot auto-registers _on_* methods as event handlers"""
        bot = Bot('http://test.com', 'channel', enable_db=False)
        # Check that some _on_* methods are registered
        assert 'rank' in bot.handlers
        assert 'userlist' in bot.handlers
        assert 'addUser' in bot.handlers
        assert 'kick' in bot.handlers
        assert len(bot.handlers['rank']) > 0
        assert len(bot.handlers['userlist']) > 0


class TestBotEventSystem:
    """Test Bot event system (on/trigger)"""

    def test_on_registers_handler(self, bot_simple):
        """on() registers event handler"""
        handler = Mock()
        bot_simple.on('test_event', handler)
        assert handler in bot_simple.handlers['test_event']

    def test_on_registers_multiple_handlers(self, bot_simple):
        """on() can register multiple handlers for same event"""
        handler1 = Mock()
        handler2 = Mock()
        bot_simple.on('test_event', handler1, handler2)
        assert handler1 in bot_simple.handlers['test_event']
        assert handler2 in bot_simple.handlers['test_event']

    def test_on_returns_self(self, bot_simple):
        """on() returns self for chaining"""
        handler = Mock()
        result = bot_simple.on('test', handler)
        assert result is bot_simple

    def test_on_duplicate_handler_warning(self, bot_simple):
        """on() warns but doesn't add duplicate handler"""
        handler = Mock()
        bot_simple.on('test', handler)
        # Second call should not add duplicate (checked in implementation)
        bot_simple.on('test', handler)
        # Handler should only be in list once
        assert bot_simple.handlers['test'].count(handler) == 1

    @pytest.mark.asyncio
    async def test_trigger_calls_async_handler(self, bot_simple):
        """trigger() calls async handler"""
        handler = AsyncMock()
        bot_simple.on('test_event', handler)
        await bot_simple.trigger('test_event', {'data': 'value'})
        handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_trigger_calls_sync_handler(self, bot_simple):
        """trigger() calls sync handler"""
        handler = Mock()
        bot_simple.on('test_event', handler)
        await bot_simple.trigger('test_event', {'data': 'value'})
        handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_trigger_passes_data(self, bot_simple):
        """trigger() passes event and data to handler"""
        handler = AsyncMock()
        bot_simple.on('test_event', handler)
        data = {'key': 'value'}
        await bot_simple.trigger('test_event', data)
        handler.assert_called_with('test_event', data)

    @pytest.mark.asyncio
    async def test_trigger_calls_multiple_handlers(self, bot_simple):
        """trigger() calls all registered handlers"""
        handler1 = AsyncMock(return_value=None)  # Don't stop iteration
        handler2 = AsyncMock(return_value=None)
        bot_simple.on('test_event', handler1, handler2)
        await bot_simple.trigger('test_event', {})
        assert handler1.call_count == 1
        assert handler2.call_count == 1

    @pytest.mark.asyncio
    async def test_trigger_nonexistent_event(self, bot_simple):
        """trigger() with no handlers does nothing (no error)"""
        # Should not raise
        await bot_simple.trigger('nonexistent_event', {})


class TestBotConnection:
    """Test Bot connection methods"""

    @pytest.mark.asyncio
    async def test_disconnect_when_connected(self, bot_with_mocks, mock_socket):
        """disconnect() closes socket when connected"""
        bot_with_mocks.socket = mock_socket
        bot_with_mocks.server = 'http://test-server.com'
        await bot_with_mocks.disconnect()
        mock_socket.close.assert_called_once()
        assert bot_with_mocks.socket is None
        assert bot_with_mocks.user.rank == -1

    @pytest.mark.asyncio
    async def test_disconnect_when_not_connected(self, bot_with_mocks):
        """disconnect() when not connected does nothing"""
        bot_with_mocks.socket = None
        await bot_with_mocks.disconnect()
        # Should not raise, just return

    @pytest.mark.asyncio
    async def test_connect_success(self, bot_with_mocks, mock_socket):
        """connect() establishes connection"""
        await bot_with_mocks.connect()
        assert bot_with_mocks.socket is mock_socket
        # Server URL will have /socket.io/ appended
        assert 'http://test-server.com' in bot_with_mocks.server
        assert bot_with_mocks.connect_time is not None

    @pytest.mark.asyncio
    async def test_connect_calls_get_socket_config(self, bot_with_mocks, mock_get):
        """connect() calls get_socket_config when server is None"""
        bot_with_mocks.server = None
        await bot_with_mocks.connect()
        # Server should be set from socket config
        assert bot_with_mocks.server is not None

    @pytest.mark.asyncio
    async def test_connect_disconnects_first(self, bot_with_mocks, mock_socket):
        """connect() disconnects existing connection first"""
        old_socket = AsyncMock()
        bot_with_mocks.socket = old_socket
        bot_with_mocks.server = 'http://test-server.com'
        await bot_with_mocks.connect()
        old_socket.close.assert_called_once()


class TestBotLogin:
    """Test Bot login methods"""

    @pytest.mark.asyncio
    async def test_login_success(self, bot_with_mocks, mock_socket):
        """login() succeeds with valid credentials"""
        mock_socket.emit = AsyncMock(side_effect=[
            ('joinChannel', {}),  # joinChannel response
            ('login', {'success': True})  # login response
        ])
        bot_with_mocks.socket = mock_socket
        bot_with_mocks.server = 'http://test-server.com'
        
        await bot_with_mocks.login()
        
        assert mock_socket.emit.call_count == 2

    @pytest.mark.asyncio
    async def test_login_invalid_channel_password(self, bot_with_mocks, mock_socket):
        """login() raises LoginError for invalid channel password"""
        mock_socket.emit = AsyncMock(return_value=('needPassword', {}))
        bot_with_mocks.socket = mock_socket
        bot_with_mocks.server = 'http://test-server.com'
        
        with pytest.raises(LoginError, match='invalid channel password'):
            await bot_with_mocks.login()

    @pytest.mark.asyncio
    async def test_login_no_user(self, mock_socket_io_connect, mock_get):
        """login() succeeds with no user (anonymous)"""
        bot = Bot('http://test.com', 'channel', get=mock_get, 
                  socket_io=mock_socket_io_connect, enable_db=False)
        mock_socket = await mock_socket_io_connect('url')
        mock_socket.emit = AsyncMock(return_value=('joinChannel', {}))
        bot.socket = mock_socket
        bot.server = 'http://test-server.com'
        
        await bot.login()
        # Should only call joinChannel, not login
        assert mock_socket.emit.call_count == 1

    @pytest.mark.asyncio
    async def test_login_guest_rate_limit_retry(self, bot_with_mocks, mock_socket):
        """login() retries after guest login rate limit"""
        # First login fails with rate limit, second succeeds
        mock_socket.emit = AsyncMock(side_effect=[
            ('joinChannel', {}),
            ('login', {'success': False, 'error': 'guest logins restricted for 2 seconds.'}),
            ('login', {'success': True})
        ])
        bot_with_mocks.socket = mock_socket
        bot_with_mocks.server = 'http://test-server.com'
        
        with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            await bot_with_mocks.login()
            mock_sleep.assert_called_once()
            # Should have called emit 3 times
            assert mock_socket.emit.call_count == 3


class TestBotUserEvents:
    """Test Bot user-related event handlers"""

    @pytest.mark.asyncio
    async def test_on_rank(self, bot_simple):
        """_on_rank updates bot user rank"""
        await bot_simple.trigger('rank', 3.0)
        assert bot_simple.user.rank == 3.0

    @pytest.mark.asyncio
    async def test_on_userlist(self, bot_simple):
        """_on_userlist populates userlist"""
        users = [
            {'name': 'user1', 'rank': 1.0},
            {'name': 'user2', 'rank': 2.0}
        ]
        await bot_simple.trigger('userlist', users)
        assert len(bot_simple.channel.userlist) == 2
        assert 'user1' in bot_simple.channel.userlist
        assert 'user2' in bot_simple.channel.userlist

    @pytest.mark.asyncio
    async def test_on_addUser(self, bot_simple):
        """_on_addUser adds user to userlist"""
        user_data = {'name': 'newuser', 'rank': 1.0}
        await bot_simple.trigger('addUser', user_data)
        assert 'newuser' in bot_simple.channel.userlist
        assert bot_simple.channel.userlist['newuser'].rank == 1.0

    @pytest.mark.asyncio
    async def test_on_addUser_self(self, bot_simple):
        """_on_addUser with bot's own name updates bot user"""
        bot_simple.user.name = 'testbot'
        user_data = {'name': 'testbot', 'rank': 2.0, 'meta': {'afk': False}}
        await bot_simple.trigger('addUser', user_data)
        assert bot_simple.user.rank == 2.0
        assert 'testbot' in bot_simple.channel.userlist

    @pytest.mark.asyncio
    async def test_on_userLeave(self, bot_simple):
        """_on_userLeave removes user from userlist"""
        # Add user first
        await bot_simple.trigger('addUser', {'name': 'leavinguser', 'rank': 1.0})
        assert 'leavinguser' in bot_simple.channel.userlist
        
        # Remove user
        await bot_simple.trigger('userLeave', {'name': 'leavinguser'})
        assert 'leavinguser' not in bot_simple.channel.userlist

    @pytest.mark.asyncio
    async def test_on_userLeave_nonexistent(self, bot_simple):
        """_on_userLeave with nonexistent user logs error but doesn't crash"""
        # Should not raise
        await bot_simple.trigger('userLeave', {'name': 'nonexistent'})

    @pytest.mark.asyncio
    async def test_on_setUserMeta(self, bot_simple):
        """_on_setUserMeta updates user metadata"""
        await bot_simple.trigger('addUser', {'name': 'user1', 'rank': 1.0})
        await bot_simple.trigger('setUserMeta', {'name': 'user1', 'meta': {'afk': True, 'muted': False}})
        # Meta will contain all fields from update
        assert bot_simple.channel.userlist['user1'].meta['afk'] is True

    @pytest.mark.asyncio
    async def test_on_setUserMeta_blank_name(self, bot_simple):
        """_on_setUserMeta with blank name does nothing"""
        # Should not raise
        await bot_simple.trigger('setUserMeta', {'name': '', 'meta': {}})

    @pytest.mark.asyncio
    async def test_on_setUserRank(self, bot_simple):
        """_on_setUserRank updates user rank"""
        await bot_simple.trigger('addUser', {'name': 'user1', 'rank': 1.0})
        await bot_simple.trigger('setUserRank', {'name': 'user1', 'rank': 3.0})
        assert bot_simple.channel.userlist['user1'].rank == 3.0

    @pytest.mark.asyncio
    async def test_on_setUserRank_blank_name(self, bot_simple):
        """_on_setUserRank with blank name does nothing"""
        # Should not raise
        await bot_simple.trigger('setUserRank', {'name': '', 'rank': 2.0})

    @pytest.mark.asyncio
    async def test_on_setAFK(self, bot_simple):
        """_on_setAFK updates user AFK status"""
        await bot_simple.trigger('addUser', {'name': 'user1', 'rank': 1.0})
        await bot_simple.trigger('setAFK', {'name': 'user1', 'afk': True})
        assert bot_simple.channel.userlist['user1'].afk is True

    @pytest.mark.asyncio
    async def test_on_setLeader(self, bot_simple):
        """_on_setLeader updates userlist leader"""
        # Add user first so leader lookup works
        await bot_simple.trigger('addUser', {'name': 'leader_user', 'rank': 3.0})
        await bot_simple.trigger('setLeader', 'leader_user')
        assert bot_simple.channel.userlist.leader.name == 'leader_user'

    @pytest.mark.asyncio
    async def test_on_usercount(self, bot_simple):
        """_on_usercount updates userlist count"""
        await bot_simple.trigger('usercount', 42)
        assert bot_simple.channel.userlist.count == 42


class TestBotPlaylistEvents:
    """Test Bot playlist-related event handlers"""

    @pytest.mark.asyncio
    async def test_on_queue(self, bot_simple):
        """_on_queue adds item to playlist"""
        item = {
            'uid': 1,
            'temp': False,
            'queueby': 'user',
            'media': {'type': 'yt', 'id': 'test', 'title': 'Test', 'seconds': 100}
        }
        await bot_simple.trigger('queue', {'after': None, 'item': item})
        assert len(bot_simple.channel.playlist.queue) == 1
        assert bot_simple.channel.playlist.queue[0].uid == 1

    @pytest.mark.asyncio
    async def test_on_delete(self, bot_simple):
        """_on_delete removes item from playlist"""
        # Add item first
        item = {
            'uid': 1,
            'temp': False,
            'queueby': 'user',
            'media': {'type': 'yt', 'id': 'test', 'title': 'Test', 'seconds': 100}
        }
        await bot_simple.trigger('queue', {'after': None, 'item': item})
        
        # Delete item
        await bot_simple.trigger('delete', {'uid': 1})
        assert len(bot_simple.channel.playlist.queue) == 0

    @pytest.mark.asyncio
    async def test_on_setTemp(self, bot_simple):
        """_on_setTemp updates item temp flag"""
        item = {
            'uid': 1,
            'temp': False,
            'queueby': 'user',
            'media': {'type': 'yt', 'id': 'test', 'title': 'Test', 'seconds': 100}
        }
        await bot_simple.trigger('queue', {'after': None, 'item': item})
        await bot_simple.trigger('setTemp', {'uid': 1, 'temp': True})
        assert bot_simple.channel.playlist.queue[0].temp is True

    @pytest.mark.asyncio
    async def test_on_moveVideo(self, bot_simple):
        """_on_moveVideo moves playlist item"""
        # Add two items
        for i in range(1, 3):
            item = {
                'uid': i,
                'temp': False,
                'queueby': 'user',
                'media': {'type': 'yt', 'id': f'v{i}', 'title': f'Video {i}', 'seconds': 100}
            }
            await bot_simple.trigger('queue', {'after': None, 'item': item})
        
        # Move item 1 after item 2 (moves to end)
        await bot_simple.trigger('moveVideo', {'from': 1, 'after': 2})
        assert bot_simple.channel.playlist.queue[0].uid == 2
        assert bot_simple.channel.playlist.queue[1].uid == 1

    @pytest.mark.asyncio
    async def test_on_setCurrent(self, bot_simple):
        """_on_setCurrent sets current playlist item"""
        item = {
            'uid': 1,
            'temp': False,
            'queueby': 'user',
            'media': {'type': 'yt', 'id': 'test', 'title': 'Test', 'seconds': 100}
        }
        await bot_simple.trigger('queue', {'after': None, 'item': item})
        await bot_simple.trigger('setCurrent', 1)
        assert bot_simple.channel.playlist.current.uid == 1

    @pytest.mark.asyncio
    async def test_on_setPlaylistMeta(self, bot_simple):
        """_on_setPlaylistMeta updates playlist time"""
        await bot_simple.trigger('setPlaylistMeta', {'rawTime': 300})
        assert bot_simple.channel.playlist.time == 300

    @pytest.mark.asyncio
    async def test_on_mediaUpdate(self, bot_simple):
        """_on_mediaUpdate updates playback state"""
        await bot_simple.trigger('mediaUpdate', {'paused': False, 'currentTime': 45})
        assert bot_simple.channel.playlist.paused is False
        assert bot_simple.channel.playlist.current_time == 45


class TestBotChannelEvents:
    """Test Bot channel-related event handlers"""

    @pytest.mark.asyncio
    async def test_on_setMotd(self, bot_simple):
        """_on_setMotd updates channel MOTD"""
        await bot_simple.trigger('setMotd', 'Welcome to the channel!')
        assert bot_simple.channel.motd == 'Welcome to the channel!'

    @pytest.mark.asyncio
    async def test_on_channelCSSJS(self, bot_simple):
        """_on_channelCSSJS updates channel CSS and JS"""
        data = {
            'css': 'body { color: red; }',
            'js': 'console.log("test");'
        }
        await bot_simple.trigger('channelCSSJS', data)
        assert bot_simple.channel.css == 'body { color: red; }'
        assert bot_simple.channel.js == 'console.log("test");'

    @pytest.mark.asyncio
    async def test_on_channelOpts(self, bot_simple):
        """_on_channelOpts updates channel options"""
        opts = {'allow_voteskip': True, 'max_queue': 50}
        await bot_simple.trigger('channelOpts', opts)
        assert bot_simple.channel.options == opts

    @pytest.mark.asyncio
    async def test_on_setPermissions(self, bot_simple):
        """_on_setPermissions updates channel permissions"""
        perms = {'chat': 0.0, 'queue': 1.0}
        await bot_simple.trigger('setPermissions', perms)
        assert bot_simple.channel.permissions == perms

    @pytest.mark.asyncio
    async def test_on_emoteList(self, bot_simple):
        """_on_emoteList updates channel emotes"""
        emotes = [{'name': 'Kappa', 'image': 'kappa.png'}]
        await bot_simple.trigger('emoteList', emotes)
        assert bot_simple.channel.emotes == emotes

    @pytest.mark.asyncio
    async def test_on_drinkCount(self, bot_simple):
        """_on_drinkCount updates drink counter"""
        await bot_simple.trigger('drinkCount', 42)
        assert bot_simple.channel.drink_count == 42

    @pytest.mark.asyncio
    async def test_on_voteskip(self, bot_simple):
        """_on_voteskip updates voteskip counts"""
        await bot_simple.trigger('voteskip', {'count': 3, 'need': 5})
        assert bot_simple.channel.voteskip_count == 3
        assert bot_simple.channel.voteskip_need == 5


class TestBotErrorHandling:
    """Test Bot error events and exception handling"""

    @pytest.mark.asyncio
    async def test_on_needPassword(self, bot_simple):
        """_on_needPassword raises LoginError"""
        with pytest.raises(LoginError, match='invalid channel password'):
            await bot_simple.trigger('needPassword', True)

    @pytest.mark.asyncio
    async def test_on_needPassword_false(self, bot_simple):
        """_on_needPassword with False doesn't raise"""
        # Should not raise
        await bot_simple.trigger('needPassword', False)

    @pytest.mark.asyncio
    async def test_on_kick(self, bot_simple):
        """_on_kick raises Kicked exception"""
        with pytest.raises(Kicked):
            await bot_simple.trigger('kick', 'You have been kicked')

    @pytest.mark.asyncio
    async def test_on_noflood(self, bot_simple):
        """_on_noflood logs error"""
        # Should not raise, just log
        await bot_simple.trigger('noflood', {'msg': 'Rate limited'})

    @pytest.mark.asyncio
    async def test_on_errorMsg(self, bot_simple):
        """_on_errorMsg logs error"""
        # Should not raise, just log
        await bot_simple.trigger('errorMsg', {'msg': 'Error occurred'})

    @pytest.mark.asyncio
    async def test_on_queueFail(self, bot_simple):
        """_on_queueFail logs playlist error"""
        # Should not raise, just log
        await bot_simple.trigger('queueFail', {'msg': 'Queue failed'})


class TestBotEdgeCases:
    """Test Bot edge cases and special conditions"""

    def test_constants_defined(self):
        """Bot has expected class constants"""
        assert Bot.SOCKET_CONFIG_URL is not None
        assert Bot.SOCKET_IO_URL is not None
        assert Bot.GUEST_LOGIN_LIMIT is not None
        assert Bot.MUTED is not None
        assert isinstance(Bot.EVENT_LOG_LEVEL, dict)

    def test_event_log_levels(self):
        """Bot defines custom log levels for events"""
        import logging
        assert Bot.EVENT_LOG_LEVEL.get('mediaUpdate') == logging.DEBUG
        assert Bot.EVENT_LOG_LEVEL_DEFAULT == logging.INFO

    @pytest.mark.asyncio
    async def test_userlist_cleared_on_new_userlist(self, bot_simple):
        """userlist event clears existing users first"""
        # Add users
        await bot_simple.trigger('addUser', {'name': 'user1', 'rank': 1.0})
        await bot_simple.trigger('addUser', {'name': 'user2', 'rank': 1.0})
        assert len(bot_simple.channel.userlist) == 2
        
        # New userlist should replace
        new_users = [{'name': 'user3', 'rank': 1.0}]
        await bot_simple.trigger('userlist', new_users)
        assert len(bot_simple.channel.userlist) == 1
        assert 'user3' in bot_simple.channel.userlist
        assert 'user1' not in bot_simple.channel.userlist

    def test_to_sequence_channel_conversion(self):
        """Bot converts channel tuple to Channel with password"""
        bot = Bot('http://test.com', ('channel', 'pass'), enable_db=False)
        assert bot.channel.name == 'channel'
        assert bot.channel.password == 'pass'

    def test_to_sequence_user_conversion(self):
        """Bot converts user tuple to User with password"""
        bot = Bot('http://test.com', 'channel', user=('user', 'pass'), enable_db=False)
        assert bot.user.name == 'user'
        assert bot.user.password == 'pass'

    def test_restart_delay_negative(self):
        """Bot with negative restart_delay doesn't reconnect"""
        bot = Bot('http://test.com', 'channel', restart_delay=-1, enable_db=False)
        assert bot.restart_delay == -1

    def test_multiple_bots_independent(self):
        """Multiple Bot instances are independent"""
        bot1 = Bot('http://test1.com', 'channel1', enable_db=False)
        bot2 = Bot('http://test2.com', 'channel2', enable_db=False)
        
        assert bot1.domain != bot2.domain
        assert bot1.channel.name != bot2.channel.name
        assert bot1.channel is not bot2.channel
        assert bot1.handlers is not bot2.handlers

    @pytest.mark.asyncio
    async def test_channelCSSJS_missing_fields(self, bot_simple):
        """_on_channelCSSJS handles missing CSS/JS fields"""
        # Only CSS provided
        await bot_simple.trigger('channelCSSJS', {'css': 'body {}'})
        assert bot_simple.channel.css == 'body {}'
        assert bot_simple.channel.js == ''
        
        # Only JS provided
        await bot_simple.trigger('channelCSSJS', {'js': 'console.log(1);'})
        assert bot_simple.channel.js == 'console.log(1);'

    @pytest.mark.asyncio
    async def test_mediaUpdate_missing_fields(self, bot_simple):
        """_on_mediaUpdate handles missing fields with defaults"""
        await bot_simple.trigger('mediaUpdate', {})
        assert bot_simple.channel.playlist.paused is True
        assert bot_simple.channel.playlist.current_time == 0

    @pytest.mark.asyncio
    async def test_voteskip_missing_fields(self, bot_simple):
        """_on_voteskip handles missing fields with defaults"""
        await bot_simple.trigger('voteskip', {})
        assert bot_simple.channel.voteskip_count == 0
        assert bot_simple.channel.voteskip_need == 0

    @pytest.mark.asyncio
    async def test_setPlaylistMeta_missing_field(self, bot_simple):
        """_on_setPlaylistMeta handles missing rawTime"""
        await bot_simple.trigger('setPlaylistMeta', {})
        assert bot_simple.channel.playlist.time == 0
