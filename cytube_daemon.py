#!/usr/bin/env python3
"""
CyTube Bot Daemon

Unified daemon process that runs the bot and web server together.
Supports start/stop/restart/status operations with PID file management.
Cross-platform: Works on both Windows and Unix-like systems.
"""

import sys
import os
import signal
import time
import argparse
import logging
import asyncio
import threading
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from lib.bot import Bot  # noqa: E402
from common.config import get_config  # noqa: E402
from common.database import BotDatabase  # noqa: E402
from web.status_server import app, init_database  # noqa: E402


class CyTubeDaemon:
    """Daemon manager for CyTube bot and web server."""
    
    def __init__(self, config_file, pid_file=None, log_file=None):
        """
        Initialize daemon.
        
        Args:
            config_file: Path to bot configuration JSON file
            pid_file: Path to PID file (default: cytube_bot.pid)
            log_file: Path to log file (default: cytube_bot.log)
        """
        self.config_file = config_file
        self.pid_file = pid_file or 'cytube_bot.pid'
        self.log_file = log_file or 'cytube_bot.log'
        self.bot = None
        self.web_thread = None
        self.shutdown_event = threading.Event()
        
    def setup_logging(self, daemon_mode=False):
        """Configure logging for daemon or foreground mode."""
        if daemon_mode:
            # Daemon mode: log to file only
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(self.log_file),
                ]
            )
        else:
            # Foreground mode: log to console and file
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.StreamHandler(sys.stdout),
                    logging.FileHandler(self.log_file),
                ]
            )
        
        self.logger = logging.getLogger('CyTubeDaemon')
        
    def write_pid(self):
        """Write current process ID to PID file."""
        pid = os.getpid()
        with open(self.pid_file, 'w') as f:
            f.write(str(pid))
        self.logger.info(f'PID {pid} written to {self.pid_file}')
        
    def read_pid(self):
        """Read PID from PID file."""
        try:
            with open(self.pid_file, 'r') as f:
                return int(f.read().strip())
        except (FileNotFoundError, ValueError):
            return None
            
    def remove_pid(self):
        """Remove PID file."""
        try:
            os.remove(self.pid_file)
            self.logger.info(f'Removed PID file {self.pid_file}')
        except FileNotFoundError:
            # It's safe to ignore if the PID file does not exist
            pass
            
    def is_running(self):
        """Check if daemon is currently running."""
        pid = self.read_pid()
        if pid is None:
            return False
            
        # Check if process exists
        try:
            os.kill(pid, 0)  # Signal 0 just checks if process exists
            return True
        except (OSError, ProcessLookupError):
            # Process doesn't exist, clean up stale PID file
            self.remove_pid()
            return False
            
    def start_web_server(self, db, bot, host='0.0.0.0', port=5000):
        """Start Flask web server in background thread."""
        def run_server():
            try:
                self.logger.info(
                    f'Starting web server on {host}:{port}'
                )
                app = create_app(db, bot)
                app.run(host=host, port=port, debug=False, use_reloader=False)
            except Exception as e:
                self.logger.error(f'Web server error: {e}')
                
        self.web_thread = threading.Thread(
            target=run_server,
            daemon=True,
            name='WebServer'
        )
        self.web_thread.start()
        
    def signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        signal_names = {
            signal.SIGTERM: 'SIGTERM',
            signal.SIGINT: 'SIGINT'
        }
        self.logger.info(
            f'Received {signal_names.get(signum, signum)}, shutting down...'
        )
        self.shutdown_event.set()
        
    def run(self, daemon_mode=False):
        """
        Run the bot and web server.
        
        Args:
            daemon_mode: If True, runs as background daemon
        """
        self.setup_logging(daemon_mode)
        
        if self.is_running():
            self.logger.error(
                f'Daemon already running (PID: {self.read_pid()})'
            )
            return 1
            
        if daemon_mode:
            self.daemonize()
            
        self.write_pid()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        
        try:
            # Load configuration
            self.logger.info(f'Loading config from {self.config_file}')
            config = get_config(self.config_file)
            
            # Initialize database
            db_path = config.get('database', 'bot_data.db')
            self.logger.info(f'Initializing database: {db_path}')
            db = Database(db_path)
            
            # Start web server in background
            web_host = config.get('web_host', '0.0.0.0')
            web_port = config.get('web_port', 5000)
            
            # Create bot
            self.logger.info('Initializing bot')
            self.bot = Bot(config, database=db)
            
            # Start web server
            self.start_web_server(db, self.bot, web_host, web_port)
            
            # Run bot in main thread
            self.logger.info('Starting bot main loop')
            asyncio.run(self.bot.run())
            
        except KeyboardInterrupt:
            self.logger.info('Keyboard interrupt received')
        except Exception as e:
            self.logger.error(f'Fatal error: {e}', exc_info=True)
            return 1
        finally:
            self.logger.info('Cleaning up...')
            self.remove_pid()
            
        return 0
        
    def daemonize(self):
        """
        Daemonize the current process (Unix only).
        
        On Windows, this does nothing - use 'pythonw.exe' or task scheduler
        instead for background execution.
        """
        if sys.platform == 'win32':
            self.logger.warning(
                'Daemonization not supported on Windows. '
                'Run with pythonw.exe or use Task Scheduler for '
                'background execution.'
            )
            return
            
        try:
            # First fork
            pid = os.fork()
            if pid > 0:
                # Parent process, exit
                sys.exit(0)
        except OSError as e:
            self.logger.error(f'First fork failed: {e}')
            sys.exit(1)
            
        # Decouple from parent environment
        os.chdir('/')
        os.setsid()
        os.umask(0)
        
        try:
            # Second fork
            pid = os.fork()
            if pid > 0:
                # Parent process, exit
                sys.exit(0)
        except OSError as e:
            self.logger.error(f'Second fork failed: {e}')
            sys.exit(1)
            
        # Redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        
        # Close stdin, stdout, stderr
        devnull_path = '/dev/null'
        with open(devnull_path, 'r') as devnull:
            os.dup2(devnull.fileno(), sys.stdin.fileno())
        with open(devnull_path, 'a+') as devnull:
            os.dup2(devnull.fileno(), sys.stdout.fileno())
        with open(devnull_path, 'a+') as devnull:
            os.dup2(devnull.fileno(), sys.stderr.fileno())
            
    def stop(self):
        """Stop the daemon."""
        pid = self.read_pid()
        if pid is None:
            self.logger.error('No PID file found, daemon not running')
            return 1
            
        self.logger.info(f'Stopping daemon (PID: {pid})')
        
        try:
            # Send SIGTERM for graceful shutdown
            os.kill(pid, signal.SIGTERM)
            
            # Wait for process to stop (max 10 seconds)
            for i in range(10):
                time.sleep(1)
                try:
                    os.kill(pid, 0)
                except (OSError, ProcessLookupError):
                    self.logger.info('Daemon stopped')
                    self.remove_pid()
                    return 0
                    
            # Still running, force kill
            self.logger.warning('Daemon did not stop gracefully, forcing...')
            os.kill(pid, signal.SIGKILL)
            time.sleep(1)
            self.remove_pid()
            return 0
            
        except (OSError, ProcessLookupError):
            self.logger.error(f'Process {pid} not found')
            self.remove_pid()
            return 1
            
    def restart(self):
        """Restart the daemon."""
        self.logger.info('Restarting daemon')
        if self.is_running():
            self.stop()
            time.sleep(2)
        return self.run(daemon_mode=True)
        
    def status(self):
        """Check daemon status."""
        pid = self.read_pid()
        if pid is None:
            print('Daemon is not running (no PID file)')
            return 1
            
        try:
            os.kill(pid, 0)
            print(f'Daemon is running (PID: {pid})')
            return 0
        except (OSError, ProcessLookupError):
            print(f'Daemon is not running (stale PID file: {pid})')
            self.remove_pid()
            return 1


def main():
    """Main entry point for daemon control."""
    parser = argparse.ArgumentParser(
        description='CyTube Bot Daemon Controller'
    )
    parser.add_argument(
        'action',
        choices=['start', 'stop', 'restart', 'status', 'foreground'],
        help='Daemon action to perform'
    )
    parser.add_argument(
        'config',
        nargs='?',
        default='config.json',
        help='Path to bot configuration file (default: config.json)'
    )
    parser.add_argument(
        '--pid-file',
        default='cytube_bot.pid',
        help='Path to PID file (default: cytube_bot.pid)'
    )
    parser.add_argument(
        '--log-file',
        default='cytube_bot.log',
        help='Path to log file (default: cytube_bot.log)'
    )
    
    args = parser.parse_args()
    
    daemon = CyTubeDaemon(
        args.config,
        pid_file=args.pid_file,
        log_file=args.log_file
    )
    
    if args.action == 'start':
        return daemon.run(daemon_mode=True)
    elif args.action == 'stop':
        daemon.setup_logging(daemon_mode=False)
        return daemon.stop()
    elif args.action == 'restart':
        daemon.setup_logging(daemon_mode=False)
        return daemon.restart()
    elif args.action == 'status':
        return daemon.status()
    elif args.action == 'foreground':
        return daemon.run(daemon_mode=False)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
