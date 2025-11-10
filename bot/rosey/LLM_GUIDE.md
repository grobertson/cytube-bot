# LLM Integration Guide

## Overview

Rosey v2.0.0 includes built-in support for Large Language Model (LLM) integration, allowing the bot to have intelligent conversations with users in the channel.

## Supported Providers

### Ollama (Local Inference)

**Best for:**
- Privacy-conscious deployments
- No API costs
- Full control over the model
- Offline operation

**Requirements:**
- [Ollama](https://ollama.ai/) installed and running
- A downloaded model (e.g., `llama3`, `mistral`, `phi`)

**Setup:**
```bash
# Install Ollama (see https://ollama.ai)
# Pull a model
ollama pull llama3

# Verify it's running
ollama list
```

### OpenRouter (Remote API)

**Best for:**
- No local GPU requirements
- Access to multiple models (Claude, GPT-4, etc.)
- Quick setup
- Pay-per-use pricing

**Requirements:**
- OpenRouter API key from [openrouter.ai](https://openrouter.ai)
- Internet connection

## Configuration

### Basic Setup

Add the `llm` section to your `config.json`:

```json
{
  "llm": {
    "enabled": true,
    "provider": "ollama",
    "system_prompt_file": "prompt.md",
    "max_context_messages": 10,
    "temperature": 0.7,
    "max_tokens": 500
  }
}
```

### Ollama Configuration

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

**Available Models:**
- `llama3` - Meta's Llama 3 (recommended)
- `mistral` - Mistral AI's model
- `phi` - Microsoft's Phi model (smaller, faster)
- See `ollama list` for all downloaded models

### OpenRouter Configuration

```json
{
  "llm": {
    "enabled": true,
    "provider": "openrouter",
    "openrouter": {
      "api_key": "sk-or-v1-...",
      "model": "anthropic/claude-3-haiku",
      "site_url": "https://your-channel.com",
      "site_name": "My CyTube Channel"
    }
  }
}
```

**Popular Models:**
- `anthropic/claude-3-haiku` - Fast, affordable Claude
- `anthropic/claude-3-sonnet` - Balanced performance
- `openai/gpt-3.5-turbo` - OpenAI's GPT-3.5
- `meta-llama/llama-3-8b` - Open source Llama 3
- See [OpenRouter models](https://openrouter.ai/models) for full list

## Configuration Parameters

### Core Settings

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enabled` | bool | false | Enable/disable LLM features |
| `provider` | string | "ollama" | Provider to use: "ollama" or "openrouter" |
| `system_prompt_file` | string | "prompt.md" | Path to personality prompt file |
| `max_context_messages` | int | 10 | Number of message pairs to remember |
| `temperature` | float | 0.7 | Creativity (0.0=deterministic, 1.0=creative) |
| `max_tokens` | int | 500 | Maximum response length |

### System Prompt

The `prompt.md` file defines Rosey's personality. Edit this to customize how the bot responds:

```markdown
You are Rosey, a helpful and friendly chat bot in a CyTube channel.

Your personality:
- Friendly and enthusiastic
- Knowledgeable about movies and videos
- Occasionally makes puns
- Never uses offensive language

Keep responses concise (1-3 sentences).
```

## Testing

Before integrating with the bot, test your LLM setup:

```bash
cd bot/rosey
python test_llm.py
```

This will verify:
- Provider connectivity
- Model availability
- Basic generation
- Conversation context

## Usage in Bot Code

### Basic Integration

```python
from bot.rosey.llm import LLMClient

# Initialize
llm_config = config.get('llm', {})
if llm_config.get('enabled'):
    llm_client = LLMClient(llm_config)
    await llm_client.__aenter__()

# In message handler
async def on_chat_message(event, data):
    username = data['username']
    message = data['msg']
    
    if message.startswith('!ai '):
        prompt = message[4:]
        response = await llm_client.chat(username, prompt)
        await bot.chat(response)
```

### Context Management

The client automatically maintains conversation history per user:

```python
# Each user has separate context
await llm_client.chat("alice", "What's your name?")
await llm_client.chat("alice", "What did I ask?")  # Remembers previous

await llm_client.chat("bob", "Hi!")  # Bob has different context

# Clear a user's context
llm_client.clear_conversation("alice")
```

## Performance Tips

### Ollama
- Use smaller models (`phi`, `mistral`) for faster responses
- GPU acceleration highly recommended
- Consider response timeout for channel usability

### OpenRouter
- `haiku` models are fastest and cheapest
- Set appropriate `max_tokens` to control costs
- Monitor usage at [openrouter.ai/activity](https://openrouter.ai/activity)

## Privacy & Safety

### Data Handling
- **Ollama**: All data stays local, nothing sent externally
- **OpenRouter**: Messages sent to their API (see their privacy policy)

### Content Filtering
- Implement rate limiting to prevent spam
- Add profanity filters if needed
- Monitor conversations for appropriate behavior
- Consider moderator-only access initially

### Cost Management
- Set `max_tokens` conservatively
- Implement per-user rate limits
- Monitor OpenRouter billing

## Troubleshooting

### Ollama Issues

**"Connection refused"**
- Ensure Ollama is running: `ollama serve`
- Check base_url matches Ollama's endpoint

**"Model not found"**
- Pull the model: `ollama pull llama3`
- Verify with: `ollama list`

**Slow responses**
- Use a smaller model
- Enable GPU acceleration
- Reduce `max_tokens`

### OpenRouter Issues

**"Invalid API key"**
- Verify key at [openrouter.ai/keys](https://openrouter.ai/keys)
- Check for typos in config.json

**"Rate limited"**
- Implement exponential backoff
- Add rate limiting per user
- Consider upgrading plan

**High costs**
- Switch to cheaper models (haiku, gpt-3.5-turbo)
- Reduce `max_tokens`
- Limit usage to moderators

## Next Steps

1. **Test the integration**: Run `test_llm.py`
2. **Customize personality**: Edit `prompt.md`
3. **Integrate with bot**: Add LLM calls to message handlers
4. **Monitor usage**: Watch for performance and costs
5. **Iterate**: Adjust based on user feedback

## Future Enhancements

- **Multiple personalities**: Different prompts for different contexts
- **Tool use**: Let Rosey control playlist, kick users, etc.
- **Memory**: Long-term memory beyond conversation context
- **Voice**: TTS integration for voice chat
- **Vision**: Image analysis for uploaded media
