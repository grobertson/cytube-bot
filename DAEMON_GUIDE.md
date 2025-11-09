# CyTube Bot Daemon Guide

## Overview

The CyTube Bot Daemon provides a unified way to run both the bot and web server together as a single managed process. It supports start/stop/restart operations with proper PID file management and logging.

## Features

- **Unified Startup**: Bot and web server start together with one command
- **Process Management**: PID file tracking for reliable start/stop/restart
- **Graceful Shutdown**: SIGTERM handling for clean shutdowns
- **Logging**: Configurable logging to file with rotation support
- **Cross-Platform**: Works on Windows, Linux, and macOS
- **Status Monitoring**: Check if daemon is running
- **Foreground Mode**: Run in terminal for development/debugging

## Quick Start

### Start the Daemon

```bash
# Linux/Mac
python3 cytube_daemon.py start config.json

# Windows
python cytube_daemon.py start config.json

# Or use the helper scripts
./cytube_daemon.sh start config.json          # Linux/Mac
cytube_daemon.bat start config.json           # Windows
```

### Check Status

```bash
python3 cytube_daemon.py status
```

### Stop the Daemon

```bash
python3 cytube_daemon.py stop
```

### Restart the Daemon

```bash
python3 cytube_daemon.py restart config.json
```

## Usage

### Command Syntax

```
cytube_daemon.py {start|stop|restart|status|foreground} [config] [options]
```

### Commands

- **start**: Start daemon in background
- **stop**: Stop running daemon
- **restart**: Stop and then start daemon
- **status**: Check if daemon is running
- **foreground**: Run in foreground (no daemonization, logs to console)

### Arguments

- **config**: Path to bot configuration JSON file (default: `config.json`)

### Options

- `--pid-file PATH`: Path to PID file (default: `cytube_bot.pid`)
- `--log-file PATH`: Path to log file (default: `cytube_bot.log`)

## Configuration

The daemon uses your existing bot `config.json` with these additional optional keys:

```json
{
  "domain": "https://cytu.be",
  "channel": ["YourChannel", "password"],
  "user": ["BotName", "password"],
  "database": "bot_data.db",
  "web_host": "0.0.0.0",
  "web_port": 5000,
  ...
}
```

### Configuration Keys

- **web_host**: Web server bind address (default: `0.0.0.0` - all interfaces)
- **web_port**: Web server port (default: `5000`)
- **database**: Database file path (default: `bot_data.db`)

## Examples

### Development Mode

Run in foreground with console output for development:

```bash
python3 cytube_daemon.py foreground config.json
```

This is equivalent to the old way of running bot and web server separately, but unified.

### Production Mode

Run as background daemon for production:

```bash
# Start
python3 cytube_daemon.py start config.json

# Check logs
tail -f cytube_bot.log

# Check status
python3 cytube_daemon.py status

# Stop when needed
python3 cytube_daemon.py stop
```

### Custom PID and Log Files

```bash
python3 cytube_daemon.py start config.json \
  --pid-file /var/run/cytube.pid \
  --log-file /var/log/cytube.log
```

### Multiple Bot Instances

Run multiple bots by using different PID and log files:

```bash
# Bot 1
python3 cytube_daemon.py start bot1_config.json \
  --pid-file bot1.pid \
  --log-file bot1.log

# Bot 2  
python3 cytube_daemon.py start bot2_config.json \
  --pid-file bot2.pid \
  --log-file bot2.log
```

## Platform-Specific Notes

### Linux/macOS

On Unix-like systems, the daemon uses the double-fork method to properly detach from the terminal and run in the background.

**Daemonization Process:**
1. Fork to create child process
2. Parent exits, child becomes session leader
3. Fork again to prevent reacquiring terminal
4. Redirect stdin/stdout/stderr to /dev/null
5. Write PID file and run main process

### Windows

Windows doesn't support Unix-style forking, so the daemon runs differently:

**Background Execution Options:**

1. **Use pythonw.exe** (recommended for manual start):
   ```cmd
   pythonw cytube_daemon.py start config.json
   ```
   This runs without a console window.

2. **Use Task Scheduler** (recommended for auto-start):
   - Create a new task
   - Trigger: At startup or at user logon
   - Action: Start program `pythonw.exe`
   - Arguments: `cytube_daemon.py start config.json`
   - Start in: Your bot directory

3. **Use NSSM** (Non-Sucking Service Manager):
   ```cmd
   nssm install CyTubeBot "C:\Python\pythonw.exe" "cytube_daemon.py foreground config.json"
   nssm start CyTubeBot
   ```

## Logging

### Log Format

```
2025-11-09 10:30:15,123 - CyTubeDaemon - INFO - Starting bot main loop
2025-11-09 10:30:15,456 - CyTubeDaemon - INFO - Starting web server on 0.0.0.0:5000
```

### Log Levels

The daemon logs at INFO level by default. All bot and web server logs are included.

### Log Rotation

For production, use `logrotate` (Linux) or similar tools:

**/etc/logrotate.d/cytube-bot:**
```
/path/to/cytube_bot.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 username groupname
    postrotate
        python3 /path/to/cytube_daemon.py restart config.json > /dev/null 2>&1 || true
    endscript
}
```

## Troubleshooting

### Daemon Won't Start

**Check if already running:**
```bash
python3 cytube_daemon.py status
```

**Check for stale PID file:**
```bash
rm cytube_bot.pid
python3 cytube_daemon.py start config.json
```

**Check logs for errors:**
```bash
tail -n 50 cytube_bot.log
```

### Daemon Won't Stop

**Force kill:**
```bash
kill -9 $(cat cytube_bot.pid)
rm cytube_bot.pid
```

### Web Server Not Accessible

**Check if port is in use:**
```bash
# Linux/Mac
lsof -i :5000

# Windows
netstat -ano | findstr :5000
```

**Check firewall:**
```bash
# Linux (ufw)
sudo ufw allow 5000/tcp

# Linux (firewalld)
sudo firewall-cmd --add-port=5000/tcp --permanent
sudo firewall-cmd --reload
```

### Permission Denied

**Make scripts executable (Linux/Mac):**
```bash
chmod +x cytube_daemon.py cytube_daemon.sh
```

**Run as different user (Linux):**
```bash
sudo -u botuser python3 cytube_daemon.py start config.json
```

## System Integration

### Systemd Service (Linux)

Create `/etc/systemd/system/cytube-bot.service`:

```ini
[Unit]
Description=CyTube Bot
After=network.target

[Service]
Type=forking
User=botuser
WorkingDirectory=/home/botuser/cytube-bot
ExecStart=/usr/bin/python3 cytube_daemon.py start config.json
ExecStop=/usr/bin/python3 cytube_daemon.py stop
PIDFile=/home/botuser/cytube-bot/cytube_bot.pid
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable cytube-bot
sudo systemctl start cytube-bot
sudo systemctl status cytube-bot
```

### Windows Service (NSSM)

1. Download NSSM from https://nssm.cc/download
2. Install as service:
   ```cmd
   nssm install CyTubeBot
   ```
3. GUI will open - configure:
   - Path: `C:\Python\pythonw.exe`
   - Startup directory: `C:\cytube-bot`
   - Arguments: `cytube_daemon.py foreground config.json`
   - Log on: Set appropriate user account

4. Start service:
   ```cmd
   nssm start CyTubeBot
   ```

### Docker Container

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python3", "cytube_daemon.py", "foreground", "config.json"]
```

**Build and run:**
```bash
docker build -t cytube-bot .
docker run -d -p 5000:5000 -v $(pwd)/config.json:/app/config.json cytube-bot
```

## Security Considerations

### File Permissions

Protect sensitive files:
```bash
chmod 600 config.json  # Configuration with passwords
chmod 644 bot_data.db   # Database
chmod 644 cytube_bot.log  # Logs
chmod 644 cytube_bot.pid  # PID file
```

### Running as Non-Root

Never run as root in production. Create a dedicated user:
```bash
sudo useradd -r -s /bin/false cytube
sudo chown -R cytube:cytube /path/to/cytube-bot
sudo -u cytube python3 cytube_daemon.py start config.json
```

### Firewall Configuration

Only expose necessary ports:
```bash
# Allow web interface
sudo ufw allow from 192.168.1.0/24 to any port 5000

# Or restrict to localhost only (use reverse proxy)
# Set web_host: "127.0.0.1" in config.json
```

## Migration from Old Setup

### Before (Separate Processes)

```bash
# Terminal 1
python bot.py config.json

# Terminal 2
python web/status_server.py config.json
```

### After (Unified Daemon)

```bash
# Single command
python3 cytube_daemon.py start config.json

# Or foreground for testing
python3 cytube_daemon.py foreground config.json
```

### Configuration Changes

No changes required! The daemon uses your existing `config.json`.

Optionally add:
```json
{
  "web_host": "0.0.0.0",
  "web_port": 5000
}
```

## Best Practices

1. **Use foreground mode during development**
   ```bash
   python3 cytube_daemon.py foreground config.json
   ```

2. **Monitor logs regularly**
   ```bash
   tail -f cytube_bot.log
   ```

3. **Set up log rotation** for long-running production bots

4. **Use systemd or equivalent** for automatic startup and restart on failure

5. **Run as dedicated user** with minimal permissions

6. **Keep PID and log files** in the bot directory or standard locations (`/var/run`, `/var/log`)

7. **Test stop/restart** before deploying to production

8. **Use version control** for configuration files (excluding sensitive data)

## Support

For issues with the daemon:
1. Check logs: `tail -n 100 cytube_bot.log`
2. Check status: `python3 cytube_daemon.py status`
3. Try foreground mode: `python3 cytube_daemon.py foreground config.json`
4. Check GitHub issues or open a new one

## See Also

- [README.md](README.md) - Main project documentation
- [QUICKSTART.md](QUICKSTART.md) - Getting started guide
- [API_TOKENS.md](API_TOKENS.md) - API authentication
- [PM_GUIDE.md](PM_GUIDE.md) - Interactive shell guide
