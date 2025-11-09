#!/bin/bash
# Start the CyTube Bot
# Usage: ./run_bot.sh <config_file>

if [ -z "$1" ]; then
    echo "Error: Config file required"
    echo ""
    echo "Usage: ./run_bot.sh <config_file>"
    echo "Example: ./run_bot.sh bots/echo/config.json"
    echo ""
    exit 1
fi

if [ ! -f "$1" ]; then
    echo "Error: Config file not found: $1"
    echo ""
    exit 1
fi

echo "Starting CyTube Bot with config: $1"
echo ""
echo "Press Ctrl+C to stop the bot"
echo ""

python3 -m lib.bot "$1"
