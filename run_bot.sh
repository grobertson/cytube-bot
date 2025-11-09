#!/bin/bash
# Start a CyTube Bot
# Usage: ./run_bot.sh <bot_script> <config_file>

if [ -z "$1" ]; then
    echo "Error: Bot script required"
    echo ""
    echo "Usage: ./run_bot.sh <bot_script> <config_file>"
    echo "Example: ./run_bot.sh bots/echo/bot.py bots/echo/config.json"
    echo ""
    exit 1
fi

if [ -z "$2" ]; then
    echo "Error: Config file required"
    echo ""
    echo "Usage: ./run_bot.sh <bot_script> <config_file>"
    echo "Example: ./run_bot.sh bots/echo/bot.py bots/echo/config.json"
    echo ""
    exit 1
fi

if [ ! -f "$1" ]; then
    echo "Error: Bot script not found: $1"
    echo ""
    exit 1
fi

if [ ! -f "$2" ]; then
    echo "Error: Config file not found: $2"
    echo ""
    exit 1
fi

echo "Starting CyTube Bot: $1"
echo "Config: $2"
echo ""
echo "Press Ctrl+C to stop the bot"
echo ""

python3 "$1" "$2"
