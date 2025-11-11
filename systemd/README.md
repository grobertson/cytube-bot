# Systemd Service Files

This directory contains systemd service files for running the CyTube bot and web server as system services on Linux.

## Files

- `cytube-bot.service` - Bot service (supports LLM integration)
- `cytube-web.service` - Web status server service

## Quick Start

For a basic bot without LLM features, follow the standard installation below.

For **LLM-enabled bots** (Rosey with OpenAI/Ollama/OpenRouter), see the [LLM Configuration Guide](#llm-integration-setup) section.

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
   - **Update bot script and config file paths in `cytube-bot.service`**:
     ```
     ExecStart=/usr/bin/python3 bots/YOUR_BOT/bot.py bots/YOUR_BOT/config.json
     ```
   - Update web server options in `cytube-web.service` if needed

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

## LLM Integration Setup

If you're running a bot with LLM features (like Rosey with OpenAI, Ollama, or OpenRouter), follow these additional steps:

### 1. Configure LLM in config.json

All LLM configuration is managed through your bot's `config.json` file. **Do not use environment variables** in the systemd service file.

**Example OpenAI configuration:**
```json
{
  "llm": {
    "enabled": true,
    "provider": "openai",
    "openai": {
      "api_key": "sk-YOUR_API_KEY_HERE",
      "model": "gpt-4o-mini"
    },
    "triggers": {
      "enabled": true,
      "direct_mention": true,
      "commands": ["!ai", "!ask"]
    }
  }
}
```

**Example Ollama configuration (local):**
```json
{
  "llm": {
    "enabled": true,
    "provider": "ollama",
    "ollama": {
      "base_url": "http://localhost:11434",
      "model": "llama3"
    }
  }
}
```

**Example Ollama configuration (remote GPU server):**
```json
{
  "llm": {
    "enabled": true,
    "provider": "ollama",
    "ollama": {
      "base_url": "http://192.168.1.100:11434",
      "model": "llama3:70b"
    }
  }
}
```

For complete configuration options, see `docs/LLM_CONFIGURATION.md`.

### 2. Secure Your Configuration

API keys and sensitive data should be protected:

```bash
# Set restrictive permissions on config file
chmod 600 bot/rosey/config.json
chown botuser:botuser bot/rosey/config.json

# Verify permissions
ls -l bot/rosey/config.json
# Should show: -rw------- 1 botuser botuser
```

### 3. Install LLM Dependencies

Ensure required Python packages are installed:

```bash
# For OpenAI provider
pip install "openai>=1.0.0"

# For all providers (includes aiohttp)
pip install -r requirements.txt
```

### 4. Remote Ollama Setup

If using a remote Ollama server (e.g., GPU server separate from bot):

**On GPU Server:**
```bash
# Install and start Ollama
curl https://ollama.ai/install.sh | sh
ollama serve

# Pull models
ollama pull llama3
ollama pull llama3:70b  # Larger model for GPU server
```

**On Bot Server:**
- Update `config.json` with remote `base_url`
- Ensure firewall allows connection to port 11434
- Test connection: `curl http://GPU_SERVER_IP:11434/api/tags`

### 5. Start Bot with LLM

```bash
# Start the bot service
sudo systemctl start cytube-bot

# Check logs for LLM initialization
sudo journalctl -u cytube-bot -f | grep -i llm
```

You should see log messages like:
```
LLM enabled: provider=openai, model=gpt-4o-mini
LLM initialization successful
```

### Troubleshooting LLM Issues

**Bot fails to start:**
- Check `journalctl -u cytube-bot -xe` for errors
- Verify API key is correct in config.json
- Ensure config.json has valid JSON syntax

**OpenAI errors:**
- Verify API key starts with `sk-`
- Check OpenAI account has credits
- Test with curl: `curl https://api.openai.com/v1/models -H "Authorization: Bearer YOUR_KEY"`

**Ollama connection errors:**
- Verify Ollama is running: `systemctl status ollama` or `curl http://localhost:11434`
- Check model is pulled: `ollama list`
- For remote: test network connectivity: `telnet GPU_SERVER_IP 11434`

**Bot connects but LLM doesn't respond:**
- Check trigger configuration in config.json
- Verify user mentions bot name or uses configured commands
- Enable debug logging: `"log_level": "DEBUG"` in config.json
