#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from pathlib import Path
import logging
import asyncio
from functools import partial
from time import localtime, strftime

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from common import Shell, get_config, configure_logger
from lib.error import CytubeError, SocketIOError
from lib import Bot

def log_chat(logger, event, data):
    """Log a chat message or private message to the chat log

    Args:
        logger: Logger instance to write to
        event: Event name ('chatMsg' or 'pm')
        data: Event data dictionary containing time, username, msg, etc.
    """
    # Extract timestamp (milliseconds since epoch) and convert to local time
    time = data.get("time", 0)
    time = strftime("%d/%m/%Y %H:%m:%S", localtime(time // 1000))

    # Extract username and message
    user = data.get("username", "<no username>")
    msg = data.get("msg", "<no message>")

    # Format differently for private messages
    if event == "pm":
        logger.info(
            "[%s] %s -> %s: %s", time, user, data.get(
                "to", "<no username>"), msg
        )
    else:
        logger.info("[%s] %s: %s", time, user, msg)


def log_media(bot, logger, *_):
    """Log when a new media item starts playing

    Args:
        bot: Bot instance to query for current playlist state
        logger: Logger instance to write to
        *_: Unused event arguments (event name, data)
    """
    current = bot.channel.playlist.current
    if current is not None:
        logger.info(
            '%s: %s "%s"',
            current.username,  # Who queued the item
            current.link.url,  # Media URL
            current.title,  # Media title
        )


async def run_bot():
    """Run the bot with proper async handling

    This is the main async function that:
    1. Loads configuration
    2. Sets up loggers for chat and media
    3. Creates and starts the bot and shell
    4. Registers event handlers
    5. Runs the bot until cancelled
    """
    # Load configuration from command line argument
    conf, kwargs = get_config()

    # Create separate loggers for chat messages and media changes
    chat_logger = logging.getLogger("chat")
    media_logger = logging.getLogger("media")

    # Configure chat logger (separate file or stdout)
    configure_logger(
        chat_logger,
        log_file=conf.get("chat_log_file", None),
        log_format="%(message)s",  # Simple format, just the message
    )

    # Configure media logger (separate file or stdout)
    configure_logger(
        media_logger,
        log_file=conf.get("media_log_file", None),
        log_format="[%(asctime).19s] %(message)s",  # Include timestamp
    )

    # Create bot instance with configuration
    bot = Bot(**kwargs)

    # Create and start shell server if configured
    shell = Shell(conf.get("shell", None), bot)
    await shell.start()

    # Create partial functions with loggers bound
    log = partial(log_chat, chat_logger)
    log_m = partial(log_media, bot, media_logger)

    # Register event handlers
    bot.on("chatMsg", log)  # Log public chat messages
    bot.on("pm", log)  # Log private messages
    bot.on("setCurrent", log_m)  # Log media changes

    # Register PM command handler for moderators (if shell is enabled)
    if shell.bot is not None:
        bot.on("pm", shell.handle_pm_command)  # Handle mod commands via PM

    try:
        # Run the bot (blocks until cancelled or error)
        await bot.run()
    finally:
        # Always close the shell on exit
        shell.close()


def main():
    """Main entry point for the bot

    Runs the async bot and handles keyboard interrupt gracefully.

    Returns:
        0 on keyboard interrupt (normal exit)
        1 on error
    """
    try:
        # Run the async bot function
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        # User pressed Ctrl+C, exit cleanly
        return 0

    # If we get here without KeyboardInterrupt, something went wrong
    return 1


if __name__ == "__main__":
    sys.exit(main())
