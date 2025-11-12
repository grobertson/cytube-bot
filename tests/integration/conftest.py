"""
Shared fixtures for integration tests.

Integration tests validate multi-component workflows with minimal mocking.
Uses real Bot, Database, and Shell instances to test realistic interactions.
"""

import pytest
import time
from unittest.mock import MagicMock, AsyncMock
from common.database import BotDatabase
from common.shell import Shell
from lib.bot import Bot


@pytest.fixture
def integration_db(tmp_path):
    """Real database for integration testing."""
    db_path = str(tmp_path / "integration_test.db")
    db = BotDatabase(db_path)
    yield db
    # Only close if not already closed
    try:
        if db.conn:
            db.close()
    except:
        pass  # Already closed


@pytest.fixture
def integration_bot(integration_db):
    """Bot instance with real database but mocked socket."""
    bot = Bot(
        domain="cytu.be",
        channel="test_integration",
        user="IntegrationTestBot",
        restart_delay=5,
        response_timeout=10
    )
    
    # Connect bot to integration database
    bot.db = integration_db
    
    # Mock socket to prevent actual network connection
    bot.socket = MagicMock()
    bot.socket.connected = True
    
    # Set up start time for uptime calculations
    bot.start_time = time.time()
    bot.connect_time = time.time()
    bot.server = "cytu.be"
    
    # Create mock channel with userlist and playlist
    bot.channel = MagicMock()
    bot.channel.name = "test_integration"
    
    # Create userlist mock with proper attributes
    bot.channel.userlist = MagicMock()
    bot.channel.userlist._users = {}
    bot.channel.userlist.count = 0
    bot.channel.userlist.leader = None
    bot.channel.userlist.__contains__ = lambda self, name: name in self._users
    bot.channel.userlist.__getitem__ = lambda self, name: self._users[name]
    bot.channel.userlist.__setitem__ = lambda self, name, user: self._users.__setitem__(name, user)
    bot.channel.userlist.__len__ = lambda self: len(self._users)
    
    bot.channel.playlist = MagicMock()
    bot.channel.playlist.queue = []
    bot.channel.playlist.current = None
    bot.channel.playlist.__len__ = lambda self: len(self.queue)
    
    # Mock usercount tracking
    bot.channel.usercount = MagicMock()
    bot.channel.usercount.chatcount = 0
    bot.channel.usercount.usercount = 0
    
    # Create bot user
    bot.user = MagicMock()
    bot.user.name = "IntegrationTestBot"
    bot.user.rank = 3.0
    bot.user.afk = False
    
    yield bot
    
    # Cleanup
    if bot.db:
        bot.db = None


@pytest.fixture
def integration_shell(integration_bot):
    """Shell instance connected to integration bot."""
    # Enable PM command interface
    shell = Shell("enabled", integration_bot)
    yield shell
    # No explicit close needed for PM-only shell


@pytest.fixture
def moderator_user():
    """Mock moderator user (rank >= 2.0)."""
    user = MagicMock()
    user.name = "ModUser"
    user.rank = 2.5
    user.afk = False
    user.muted = False
    return user


@pytest.fixture
def regular_user():
    """Mock regular user (rank < 2.0)."""
    user = MagicMock()
    user.name = "RegularUser"
    user.rank = 1.0
    user.afk = False
    user.muted = False
    return user


@pytest.fixture
def admin_user():
    """Mock admin user (rank = 5.0)."""
    user = MagicMock()
    user.name = "AdminUser"
    user.rank = 5.0
    user.afk = False
    user.muted = False
    return user
