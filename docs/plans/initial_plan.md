# repo-sherpa Implementation Plan

## Overview
Build a containerized Slack bot that can serve multiple repositories. Start with a simple echo implementation, then integrate Claude Code.

## Phase 1: Basic Infrastructure (Milestone 1)

### 1.1 Project Setup
- [ ] Create project directory: `mkdir repo-sherpa && cd repo-sherpa`
- [ ] Initialize uv project: `uv init --name repo-sherpa --python 3.11`
- [ ] Initialize git repository: `git init`
- [ ] Create source directory structure:
  ```
  repo-sherpa/
  ├── src/
  │   ├── __init__.py
  │   ├── main.py
  │   └── bot.py
  ├── bot_config.yaml
  ├── pyproject.toml  (created by uv init)
  ├── Dockerfile
  ├── .env.example
  └── README.md
  ```
- [ ] Create src directory: `mkdir src && touch src/__init__.py`

### 1.2 Dependencies
Add dependencies using uv:
```bash
uv add slack-bolt pyyaml python-dotenv
```

This will update your `pyproject.toml` automatically. The dependencies section should look like:
```toml
dependencies = [
    "slack-bolt>=1.18.0",
    "pyyaml>=6.0.1",
    "python-dotenv>=1.0.0",
]
```

### 1.3 Slack App Setup (per bot)
For each bot you want to create:
1. [ ] Go to api.slack.com/apps → Create New App → From scratch
2. [ ] Enable Socket Mode (Settings → Socket Mode → Enable)
3. [ ] Create App-Level Token with `connections:write` scope (save as `SLACK_APP_TOKEN`)
4. [ ] Add Bot Token Scopes (OAuth & Permissions):
   - `app_mentions:read`
   - `channels:history`
   - `chat:write`
5. [ ] Subscribe to bot events (Event Subscriptions):
   - `app_mention`
6. [ ] Install app to workspace (OAuth & Permissions → Install to Workspace)
7. [ ] Save Bot User OAuth Token (save as `SLACK_BOT_TOKEN`)

### 1.4 Configuration File
Create `bot_config.yaml`:
```yaml
bots:
  backend_bot:
    repo_path: "/repos/backend"
    timeout: 300
    
  frontend_bot:
    repo_path: "/repos/frontend"
    timeout: 180
```

Create `.env.example`:
```
BACKEND_BOT_TOKEN=xoxb-your-token-here
BACKEND_APP_TOKEN=xapp-your-token-here
FRONTEND_BOT_TOKEN=xoxb-your-token-here
FRONTEND_APP_TOKEN=xapp-your-token-here
```

## Phase 2: Echo Implementation (Milestone 2)

### 2.1 Core Bot Logic
Create the bot implementation across multiple files:

**Step 1: Basic structure in `src/bot.py`**
```python
import os
import yaml
import threading
from concurrent.futures import ThreadPoolExecutor
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

class MultiRepoBot:
    def __init__(self, config_path):
        self.config = yaml.safe_load(open(config_path))
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.apps = {}
        self._setup_bots()
    
    def _setup_bots(self):
        # Initialize each bot
        pass
    
    def start(self):
        # Start all bot handlers
        pass
```

**Create `src/main.py` as entry point:**
```python
from bot import MultiRepoBot

if __name__ == "__main__":
    bot = MultiRepoBot('bot_config.yaml')
    bot.start()
```

**Future module structure** (you can add these as needed):
- `src/slack_handler.py` - Slack event handling logic
- `src/claude_runner.py` - Claude Code subprocess management
- `src/config.py` - Configuration loading and validation
- `src/utils.py` - Helper functions

**Step 2: Implement bot setup**
- [ ] Load tokens from environment variables
- [ ] Create Slack App instance for each bot
- [ ] Register `app_mention` event handler
- [ ] Create SocketModeHandler for each bot

**Step 3: Implement event handler**
- [ ] Extract thread_ts (use event['ts'] if no thread exists)
- [ ] Submit job to executor for async processing
- [ ] Return immediately (don't block Slack)

**Step 4: Implement thread context fetching**
```python
def fetch_thread_context(self, bot_app, channel, thread_ts):
    """Fetch all messages in a thread"""
    result = bot_app.client.conversations_replies(
        channel=channel,
        ts=thread_ts
    )
    return result['messages']
```

**Step 5: Implement echo subprocess**
```python
def process_request(self, bot_name, event, say):
    config = self.apps[bot_name]['config']
    thread_ts = event.get('thread_ts') or event['ts']
    
    # Fetch thread context
    messages = self.fetch_thread_context(...)
    
    # Run echo subprocess
    result = subprocess.run(
        ['echo', f"Repo: {config['repo_path']}, Messages: {len(messages)}"],
        cwd=config['repo_path'],
        capture_output=True,
        text=True,
        timeout=config['timeout']
    )
    
    # Post response
    say(
        text=result.stdout.strip(),
        thread_ts=thread_ts
    )
```

### 2.2 Testing Echo Implementation
- [ ] Create test repo directories: `mkdir -p /tmp/repos/backend /tmp/repos/frontend`
- [ ] Update bot_config.yaml to point to test repos
- [ ] Load environment variables: `source .env`
- [ ] Run bot: `python src/main.py` or `uv run python src/main.py`
- [ ] Test in Slack:
  - [ ] Mention bot in channel → Should see "Repo: /tmp/repos/backend, Messages: 1"
  - [ ] Reply in thread → Should see "Messages: 2"
  - [ ] Mention other bot → Should see different repo path

### 2.3 Error Handling
Add basic error handling:
- [ ] Wrap subprocess in try/except
- [ ] Handle subprocess timeout
- [ ] Handle missing thread context
- [ ] Post error messages back to Slack thread

## Phase 3: Containerization (Milestone 3)

### 3.1 Create Dockerfile
```dockerfile
FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy project files
COPY pyproject.toml /app/
COPY src/ /app/src/
WORKDIR /app

# Install dependencies
RUN uv pip install --system --no-cache .

# Repos will be mounted
VOLUME ["/repos"]

CMD ["python", "src/main.py"]
```

### 3.2 Build and Test
- [ ] Build image: `docker build -t repo-sherpa:echo .`
- [ ] Test locally:
  ```bash
  docker run \
    --env-file .env \
    -v ./bot_config.yaml:/app/bot_config.yaml \
    -v /path/to/repos:/repos:ro \
    repo-sherpa:echo
  ```
- [ ] Verify bot responds correctly in Slack

### 3.3 Docker Compose (Optional)
Create `docker-compose.yml` for easier local dev:
```yaml
version: '3.8'
services:
  repo-sherpa:
    build: .
    env_file: .env
    volumes:
      - ./bot_config.yaml:/app/bot_config.yaml
      - /path/to/repos:/repos:ro
```

Run with: `docker-compose up`

## Phase 4: Claude Code Integration (Milestone 4)

### 4.1 Update Dockerfile
Add Claude Code CLI installation:
```dockerfile
FROM python:3.11-slim

# Install Claude Code CLI
RUN curl -L [claude-code-install-url] | sh

# ... rest of Dockerfile
```

### 4.2 Modify process_request
Replace echo with Claude Code invocation:
- [ ] Format thread context into prompt
- [ ] Build Claude Code command
- [ ] Handle Claude Code output/errors
- [ ] Stream or chunk long responses if needed

**Prompt formatting strategy:**
```python
def format_prompt(self, messages, current_question):
    """Format thread history for Claude"""
    if len(messages) == 1:
        # First message in thread
        return current_question
    
    # Build context from thread history
    context = "Previous conversation:\n"
    for msg in messages[:-1]:
        role = "Bot" if msg.get('bot_id') else "User"
        context += f"{role}: {msg['text']}\n"
    
    context += f"\nCurrent question: {current_question}\n"
    context += f"Repository: You are working in the repo at {repo_path}"
    
    return context
```

### 4.3 Testing with Claude Code
- [ ] Test single question → Claude Code response
- [ ] Test multi-turn conversation → Claude maintains context
- [ ] Test concurrent requests to different bots
- [ ] Test error cases (timeout, Claude Code failure)

## Phase 5: Production Readiness (Milestone 5)

### 5.1 Logging
- [ ] Add structured logging (consider `structlog`)
- [ ] Log all invocations with timing
- [ ] Log errors with context

### 5.2 Monitoring (Optional)
- [ ] Add metrics (request count, latency, errors)
- [ ] Add health check endpoint
- [ ] Consider prometheus-client if needed

### 5.3 Documentation
- [ ] Update README with setup instructions
- [ ] Document bot configuration options
- [ ] Document deployment steps
- [ ] Add troubleshooting guide

### 5.4 Security Review
- [ ] Ensure repos mounted read-only (unless write needed)
- [ ] Review subprocess security (resource limits)
- [ ] Ensure secrets not logged
- [ ] Review error messages (no sensitive data exposed)

## Testing Checklist

### Functional Tests
- [ ] Bot responds to mentions
- [ ] Thread context properly retrieved
- [ ] Multiple bots work independently
- [ ] Concurrent requests handled correctly
- [ ] Errors handled gracefully

### Edge Cases
- [ ] Very long threads (50+ messages)
- [ ] Rapid-fire mentions
- [ ] Bot mentioned twice before first response
- [ ] Invalid repo paths
- [ ] Subprocess timeout
- [ ] Network issues with Slack

## Deployment Options

### Option 1: Single Server
```bash
docker run -d \
  --name repo-sherpa \
  --restart unless-stopped \
  --env-file .env \
  -v ./bot_config.yaml:/app/bot_config.yaml \
  -v /path/to/repos:/repos:ro \
  repo-sherpa:latest
```

### Option 2: Docker Compose
Use docker-compose.yml for easier management

### Option 3: Kubernetes (if needed)
Create deployment manifest for k8s cluster

## Success Criteria

**Milestone 1 Complete:** Can load config, connect to Slack, receive events

**Milestone 2 Complete:** Echo implementation works, shows repo path and message count

**Milestone 3 Complete:** Running in container, responding correctly

**Milestone 4 Complete:** Claude Code integration working, handles multi-turn conversations

**Milestone 5 Complete:** Documented, monitored, ready for production use

## Next Steps After Implementation

1. Add rate limiting per user/channel
2. Add admin commands (restart bot, clear context, etc.)
3. Add support for slash commands
4. Consider adding file upload support
5. Add cost tracking for Claude API usage
6. Build web dashboard for monitoring