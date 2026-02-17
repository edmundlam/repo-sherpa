# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

repo-sherpa is a multi-bot Slack service that provides AI-powered assistance for git repositories. Each bot instance serves a specific repository and maintains conversation context within Slack threads. The system integrates with Claude Code CLI to answer questions about codebases.

**Architecture**: Multi-bot system with ThreadPoolExecutor-based async processing, Slack Socket Mode for real-time communication, and session-aware conversation management.

## Development Commands

```bash
# Install dependencies (requires Python 3.13)
make install
# or
uv sync

# Run the bot service
make run
# or
uv run python src/main.py

# Run tests
make test
# or
uv run pytest

# Run linter and formatter (auto-fixes issues)
make lint
# or
uv run ruff check --fix && uv run ruff format

# Clean virtual environment
make clean
```

**Python Version**: Requires Python >=3.13 (see `.python-version`)

## Architecture

### Multi-Bot System

The application runs multiple independent bot instances from a single process.
The codebase is organized into domain modules:

**`src/bot.py`**: MultiRepoBot orchestrator - coordinates components, manages ThreadPoolExecutor
**`src/slack/`**: Slack integration (app setup, messaging, reactions)
**`src/claude/`**: Claude CLI wrapper and prompt formatting
**`src/sessions/`**: Thread session management

Each bot instance is configured in `bot_config.yaml`:

```yaml
bots:
  backend:
    repo_path: "/path/to/repo"
    timeout: 300
    processing_emojis:
      - eyes
      - robot_face
```

Each bot requires its own Slack app with environment variables:
- `{BOT_NAME}_BOT_TOKEN` - Bot user OAuth token (xoxb-*)
- `{BOT_NAME}_APP_TOKEN` - App-level token for Socket Mode (xapp-*)

### Request Flow

```
Slack @mention
  ↓
Add emoji reaction (visual feedback)
  ↓
Submit to ThreadPoolExecutor (async)
  ↓
Fetch thread context from Slack API
  ↓
Format prompt (conversation history + repo path)
  ↓
Invoke Claude Code CLI in repo directory
  ↓
Parse JSON response, store session_id
  ↓
Post response to Slack thread
  ↓
Remove emoji reaction
```

### Key Components

**`src/bot.py:32` - MultiRepoBot class**:
- Orchestrates all components and coordinates request flow
- `executor`: ThreadPoolExecutor (max_workers=10) for concurrent request handling
- `app_manager`: SlackAppManager instance for bot lifecycle
- `thread_sessions`: SessionManager instance for conversation continuity
- `_make_app_mention_handler()`: Closure pattern captures bot-specific config per handler
- `process_request()`: Main request processing logic

**`src/slack/app_manager.py`**: SlackAppManager - handles Slack app setup and lifecycle

**`src/slack/messaging.py`**: SlackMessaging - wraps Slack API calls (reactions, messages, thread context)

**`src/claude/cli_wrapper.py`**: ClaudeCLIWrapper - invokes Claude Code CLI subprocess

**`src/claude/prompt_builder.py`**: PromptBuilder - formats conversation history into prompts

**`src/sessions/manager.py`**: SessionManager - maps thread_ts → session_id for multi-turn conversations

**`src/main.py`**: Simple entry point that instantiates and starts MultiRepoBot

### Session Management

The system maintains Claude Code session IDs per Slack thread, enabling multi-turn conversations:
- First message in thread: New Claude session started
- Subsequent messages: Resumes existing session using `--resume session_id`
- Thread IDs extracted from `event['thread_ts']` (fallback to `event['ts']`)

### Configuration Files

- **`bot_config.yaml`**: Bot definitions, repository paths, timeouts, max_turns, allowed_tools, emoji reactions
- **`.env`**: Slack tokens (gitignored, see `.env.example` for template)
- **`docs/setup.md`**: Complete Slack app setup instructions

## Implementation Patterns

### Closure Pattern for Handlers

Each bot gets its own event handler closure that captures bot_name and config:

```python
def _make_app_mention_handler(self, bot_name, bot_config):
    def handler(event, say, client):
        # bot_name and bot_config are captured in closure
        # ...
    return handler
```

### Thread-Safe Async Processing

Requests run in background threads via ThreadPoolExecutor. The Slack event returns immediately with an emoji reaction, then the actual processing happens asynchronously.

### Error Handling

Three error categories are explicitly handled:
- **Timeout**: Configurable per-bot (default 300s)
- **JSON parsing**: Claude CLI output is JSON format
- **General exceptions**: Caught with logging and user-friendly Slack response

## Testing

Local testing requires:
1. Identify the repository paths to serve
2. Set up Slack apps per `docs/setup.md`
3. Configure `bot_config.yaml` with repo paths
4. Add tokens to `.env`
5. Run with `make run`
6. Test by mentioning bot in Slack channel

## Important Notes

- **Socket Mode**: Used instead of HTTP mode (no public endpoint needed)
- **Session IDs**: Stored in-memory only - lost on restart
- **Emoji reactions**: Randomly selected from configurable list for visual feedback
- **Thread context**: Full conversation history fetched from Slack API for each request
- **Claude Code CLI**: Must be installed and available in PATH
- **Logging**: Comprehensive logging with timestamps at INFO level
