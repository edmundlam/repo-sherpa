# repo-sherpa

A multi-bot Slack service that provides AI-powered assistance for git repositories. Each bot instance serves a specific repository and maintains conversation context within Slack threads, integrating with Claude Code CLI for intelligent codebase analysis.

## Overview

repo-sherpa enables teams to interact (in read-only fashion) with their codebases directly through Slack. Mention a bot in any channel, ask questions about code, and receive AI-powered responses that understand your entire repository context.

### Key Features

- **Multi-Bot Architecture**: Run multiple bot instances from a single process, each serving different repositories
- **Session Awareness**: Maintains conversation context within Slack threads for multi-turn discussions
- **Async Processing**: ThreadPoolExecutor-based concurrent request handling with visual feedback via emoji reactions
- **Slack Socket Mode**: No public endpoint required—runs entirely from your network
- **Claude Code Integration**: Leverages Claude Code CLI for powerful codebase understanding
- **Configurable Timeouts**: Per-bot timeout limits for long-running analysis tasks

## Quick Start

### Prerequisites

- Python 3.13 or higher
- Claude Code CLI installed and available in PATH
- Slack workspace with admin access (to create apps)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/repo-sherpa.git
cd repo-sherpa

# Install dependencies
make install
# or
uv sync
```

### Configuration

1. **Set up Slack apps** (one per bot):
   - Follow the [Slack App Setup Guide](docs/setup.md)
   - You'll get Bot Tokens (`xoxb-*`) and App Tokens (`xapp-*`)

2. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your Slack tokens
   ```

3. **Configure bots** in `bot_config.yaml`:
   ```yaml
   bots:
     backend:
       repo_path: "/path/to/your/backend/repo"
       timeout: 300
       processing_emojis:
         - eyes
         - robot_face
   ```

### Running

```bash
make run
# or
uv run python src/main.py
```

## Usage

Once running, interact with your bots in Slack:

```
@backend-bot How does the authentication system work?
```

The bot will:
1. Add an emoji reaction to show it's working
2. Process your request asynchronously
3. Respond in the thread with analysis from your codebase
4. Remove the emoji when complete

### Multi-Turn Conversations

repo-sherpa maintains session context per thread. Follow-up questions in the same thread remember previous context:

```
@backend-bot How does the authentication system work?
[Bot responds with detailed explanation]

@backend-bot Show me the token validation logic
[Bot responds with specific code references, remembering the context]
```

## Architecture

```mermaid
graph TB
    A[Slack @mention] --> B[Emoji Reaction Added]
    B --> C[ThreadPoolExecutor]
    C --> D[Fetch Thread Context]
    D --> E[Format Prompt]
    E --> F[Claude Code CLI]
    F --> G[Parse Response]
    G --> H[Post to Slack]
    H --> I[Remove Emoji]
```

**Key Components:**

- **`MultiRepoBot`** (`src/bot.py`): Core orchestrator managing multiple bot instances
- **Thread-Safe Async Processing**: Requests handled concurrently via ThreadPoolExecutor
- **Session Management**: Maps Slack thread timestamps to Claude session IDs
- **Closure Pattern Handlers**: Each bot gets its own event handler closure

For detailed architecture documentation, see [docs/architecture.md](docs/architecture.md).

## Documentation

- **[Architecture Guide](docs/architecture.md)**: System design, request flow, and component details
- **[Slack App Setup](docs/setup.md)**: Step-by-step Slack app configuration
- **[Development Guide](docs/development.md)**: Local development, testing, and contributing
- **[Deployment Guide](docs/deployment.md)**: Production deployment and configuration

## Configuration Reference

### bot_config.yaml

```yaml
bots:
  bot_name:
    repo_path: "/absolute/path/to/repository"  # Required: Path to git repo
    timeout: 300                               # Optional: Timeout in seconds (default: 300)
    max_turns: 40                              # Optional: Max Claude turns (default: 40)
    allowed_tools:                             # Optional: Tools for Claude (empty = defaults)
      - Read
      - Grep
      - Ls
      - Find
      - "Bash(git log)"
      - "Bash(git show)"
      - "Bash(git diff)"
      - "Bash(git blame)"
    processing_emojis:                         # Optional: List of emoji reactions
      - eyes
      - robot_face
```

**Configuration Options:**

- `repo_path`: Absolute path to the git repository the bot will serve
- `timeout`: Maximum seconds to wait for Claude CLI response (default: 300)
- `max_turns`: Maximum number of Claude turns before timing out (default: 40)
- `allowed_tools`: List of tools Claude Code can use. Built-in tools (Read, Grep, Ls, Find) are always available. Add `Bash(...)` entries to allow git commands and other utilities
- `processing_emojis`: Emoji reactions randomly selected for visual feedback

### Environment Variables

```bash
# One pair per bot (BOT_NAME must match bot_config.yaml keys, uppercased)
BOT_NAME_BOT_TOKEN=xoxb-your-bot-token
BOT_NAME_APP_TOKEN=xapp-your-app-token
```

## Requirements

- Python >=3.13
- Claude Code CLI (installed and in PATH)
- slack-bolt >=1.27.0
- python-dotenv >=1.2.1
- pyyaml >=6.0.3

## Troubleshooting

### Bot doesn't respond to mentions
- Verify bot is invited to the channel: `/invite @YourBotName`
- Check tokens in `.env` match your Slack app configuration
- Ensure Socket Mode is enabled in Slack app settings

### Claude Code CLI not found
- Verify Claude Code CLI is installed: `claude --version`
- Check it's in your PATH: `which claude`
- Restart your terminal after installation

### Session context lost between messages
- Ensure messages are in the same thread
- Check that the bot hasn't been restarted (sessions are in-memory)

See [docs/setup.md#troubleshooting](docs/setup.md#troubleshooting) for more details.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please see [docs/development.md](docs/development.md) for guidelines.

## Support

For issues, questions, or contributions, please [open an issue](https://github.com/yourusername/repo-sherpa/issues) on GitHub.
