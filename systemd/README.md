# Systemd Service Files

This directory contains systemd service files for running the CyTube bot and web server as system services on Linux.

## Files

- `cytube-bot.service` - Bot service
- `cytube-web.service` - Web status server service

## Installation

1. **Copy service files to systemd directory:**
   ```bash
   sudo cp systemd/*.service /etc/systemd/system/
   ```

2. **Create log directory:**
   ```bash
   sudo mkdir -p /var/log/cytube-bot
   sudo chown botuser:botuser /var/log/cytube-bot
   ```

3. **Edit service files** to match your setup:
   - Change `User` to your username
   - Update `WorkingDirectory` to your bot installation path
   - Modify paths to Python interpreter if needed
   - Update config file path in bot service

4. **Reload systemd:**
   ```bash
   sudo systemctl daemon-reload
   ```

5. **Enable services to start on boot:**
   ```bash
   sudo systemctl enable cytube-bot
   sudo systemctl enable cytube-web
   ```

6. **Start services:**
   ```bash
   sudo systemctl start cytube-bot
   sudo systemctl start cytube-web
   ```

## Usage

### Check status
```bash
sudo systemctl status cytube-bot
sudo systemctl status cytube-web
```

### View logs
```bash
sudo journalctl -u cytube-bot -f
sudo journalctl -u cytube-web -f
```

Or check log files directly:
```bash
tail -f /var/log/cytube-bot/bot.log
tail -f /var/log/cytube-bot/web.log
```

### Stop services
```bash
sudo systemctl stop cytube-bot
sudo systemctl stop cytube-web
```

### Restart services
```bash
sudo systemctl restart cytube-bot
sudo systemctl restart cytube-web
```

### Disable services
```bash
sudo systemctl disable cytube-bot
sudo systemctl disable cytube-web
```

## Notes

- The web service requires the bot service (`Requires=cytube-bot.service`)
- Both services will automatically restart on failure
- Logs are appended to files in `/var/log/cytube-bot/`
- Services run as the specified user (change `User=` in the service files)
