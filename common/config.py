#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import json
import logging

from lib import SocketIO, set_proxy


class RobustFileHandler(logging.FileHandler):
    """FileHandler that gracefully handles flush errors on Windows"""

    def flush(self):
        """Flush the stream, catching OSError on Windows file handles"""
        try:
            super().flush()
        except OSError as e:
            # Windows can sometimes fail to flush with "Invalid argument"
            # This typically happens when the file handle is in an
            # inconsistent state. We log it but don't crash.
            if e.errno == 22:  # EINVAL
                # Silently ignore invalid argument errors
                pass
            else:
                raise


def configure_logger(logger,
                     log_file=None,
                     log_format=None,
                     log_level=logging.INFO):
    """Configure a logger with a file or stream handler

    Args:
        logger: Logger instance or logger name string
        log_file: File path string or file-like object (None for stderr)
        log_format: Format string for log messages
        log_level: Logging level (e.g., logging.INFO, logging.DEBUG)

    Returns:
        Configured logger instance
    """
    # Create file handler if path string, otherwise stream handler
    if isinstance(log_file, str):
        # Append mode with UTF-8 encoding and error handling for Windows
        # Use RobustFileHandler to catch flush errors
        handler = RobustFileHandler(
            log_file,
            mode='a',
            encoding='utf-8',
            errors='replace'  # Replace problematic chars
        )
    else:
        handler = logging.StreamHandler(log_file)  # Default to stderr if None

    # Create and attach formatter
    formatter = logging.Formatter(log_format)

    # Get logger by name if string provided
    if isinstance(logger, str):
        logger = logging.getLogger(logger)

    # Configure the logger
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(log_level)

    return logger


def configure_proxy(conf):
    """Configure SOCKS proxy from config dictionary

    Args:
        conf: Configuration dictionary containing optional 'proxy' key
              Format: "host:port" or just "host" (default port 1080)
    """
    proxy = conf.get('proxy', None)
    if not proxy:
        return

    # Parse proxy address - split on last colon
    proxy = proxy.rsplit(':', 1)
    if len(proxy) == 1:
        # No port specified, use default SOCKS port
        addr, port = proxy[0], 1080
    else:
        # Port was specified
        addr, port = proxy[0], int(proxy[1])

    # Set the global proxy configuration
    set_proxy(addr, port)


def get_config():
    """Load and parse configuration from JSON file specified in command line

    Returns:
        Tuple of (conf, kwargs) where:
            conf: Full configuration dictionary from JSON file
            kwargs: Bot initialization parameters extracted from config

    Exits:
        Exits with status 1 if incorrect number of arguments
    """
    # Validate command line arguments
    if len(sys.argv) != 2:
        print('usage: %s <config file>' % sys.argv[0], file=sys.stderr)
        sys.exit(1)

    # Load JSON configuration file
    with open(sys.argv[1], 'r') as fp:
        conf = json.load(fp)

    # Extract connection retry settings
    retry = conf.get('retry', 0)  # Number of connection retries
    retry_delay = conf.get('retry_delay', 1)  # Seconds between retries

    # Parse log level from string to logging constant
    log_level = getattr(logging, conf.get('log_level', 'info').upper())

    # Configure root logger with basic settings
    logging.basicConfig(
        level=log_level,
        format='[%(asctime).19s] [%(name)s] [%(levelname)s] %(message)s'
    )

    # Configure SOCKS proxy if specified in config
    configure_proxy(conf)

    # Return full config and extracted bot parameters
    return conf, {
        'domain': conf['domain'],  # CyTube server domain (required)
        'user': conf.get('user', None),  # Bot username/credentials (optional)
        'channel': conf.get('channel', None),  # Channel name/password (optional)
        'response_timeout': conf.get('response_timeout', 0.1),  # Socket.IO response timeout
        'restart_delay': conf.get('restart_delay', None),  # Delay before reconnect on error
        'socket_io': lambda url, loop: SocketIO.connect(
            url,
            retry=retry,
            retry_delay=retry_delay,
            loop=loop
        )
    }
