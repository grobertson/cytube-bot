#!/bin/bash
# CyTube Bot Daemon Controller
# Usage: ./cytube_daemon.sh {start|stop|restart|status|foreground} [config.json]

ACTION=$1
CONFIG=${2:-config.json}

if [ -z "$ACTION" ]; then
    echo "Usage: $0 {start|stop|restart|status|foreground} [config.json]"
    exit 1
fi

python3 cytube_daemon.py "$ACTION" "$CONFIG"
