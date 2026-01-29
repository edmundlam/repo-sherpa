# Claude Code Headless Integration for repo-sherpa

## Summary

We're integrating Claude Code in headless mode to power the Slack bot. The key insight is that Claude Code can run non-interactively via the CLI and maintain conversation context through session IDs.

## Core Command Structure

The basic command is simpler than initially thought:

```bash
claude -p "<your prompt here>" --output-format json
```

Key flags:
- `-p` or `--print`: Run in non-interactive headless mode
- `--output-format json`: Return structured JSON output with metadata
- `--resume <session_id>`: Continue a previous conversation (optional)

## Session Management Strategy

**Approach:** Maintain an in-memory mapping of Slack thread IDs to Claude session IDs.

**Why use sessions?**
- Claude Code remembers files it's already read
- Maintains internal working memory across turns
- Potentially faster/cheaper for multi-turn conversations

**Trade-off accepted:**
- Session map is lost on container restart
- This is fine - we fetch full thread history from Slack anyway
- Worst case: Claude re-reads some files after restart

## Implementation

### Data Structure

```python
class MultiRepoBot:
    def __init__(self, config_path):
        self.config = yaml.safe_load(open(config_path))
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.apps = {}
        self.thread_sessions = {}  # Maps thread_ts -> session_id
        self._setup_bots()
```

### Main Processing Logic

```python
def process_request(self, bot_name, event, say):
    """Process a Slack mention and respond using Claude Code"""
    config = self.apps[bot_name]['config']
    thread_ts = event.get('thread_ts') or event['ts']
    channel = event['channel']
    
    # Fetch thread context from Slack
    messages = self.fetch_thread_context(
        self.apps[bot_name]['app'], 
        channel, 
        thread_ts
    )
    
    # Format prompt from thread history
    prompt = self.format_prompt(messages, config['repo_path'])
    
    # Check if we have an existing session for this thread
    session_id = self.thread_sessions.get(thread_ts)
    
    # Build Claude Code command
    cmd = ['claude', '-p', prompt, '--output-format', 'json']
    if session_id:
        cmd.extend(['--resume', session_id])
    
    try:
        # Run Claude Code
        result = subprocess.run(
            cmd,
            cwd=config['repo_path'],
            capture_output=True,
            text=True,
            timeout=config['timeout']
        )
        
        # Parse JSON response
        output = json.loads(result.stdout)
        
        # Store session_id for future turns in this thread
        self.thread_sessions[thread_ts] = output['session_id']
        
        # Post response to Slack thread
        say(
            text=output['result'],
            thread_ts=thread_ts
        )
        
    except subprocess.TimeoutExpired:
        say(
            text="Request timed out - the task took too long to complete.",
            thread_ts=thread_ts
        )
    except json.JSONDecodeError as e:
        say(
            text=f"Error parsing Claude response: {str(e)}",
            thread_ts=thread_ts
        )
    except Exception as e:
        say(
            text=f"Error processing request: {str(e)}",
            thread_ts=thread_ts
        )
```

### Prompt Formatting

```python
def format_prompt(self, messages, repo_path):
    """Format Slack thread history into a prompt for Claude"""
    if len(messages) == 1:
        # First message in thread - just return the question
        return messages[0]['text']
    
    # Build context from thread history
    context = "Previous conversation:\n"
    for msg in messages[:-1]:
        role = "Assistant" if msg.get('bot_id') else "User"
        context += f"{role}: {msg['text']}\n"
    
    # Add current question
    current_question = messages[-1]['text']
    context += f"\nCurrent question: {current_question}\n"
    context += f"\nYou are working in the repository at: {repo_path}"
    
    return context
```

## JSON Response Format

Claude Code returns JSON with this structure:

```json
{
  "type": "result",
  "subtype": "success",
  "total_cost_usd": 0.003,
  "is_error": false,
  "duration_ms": 1234,
  "duration_api_ms": 800,
  "num_turns": 6,
  "result": "The actual response text here...",
  "session_id": "abc123-def456-..."
}
```

We extract:
- `result`: The text to send back to Slack
- `session_id`: Store in our thread_sessions map for next turn

## Flow Diagram

```
User mentions bot in Slack
  ↓
Fetch all messages in thread
  ↓
Format into prompt with context
  ↓
Check if thread_sessions has session_id for this thread
  ↓
Run: claude -p <prompt> [--resume <session_id>] --output-format json
  ↓
Parse JSON response
  ↓
Store session_id in thread_sessions[thread_ts]
  ↓
Post result to Slack thread
```

## Notes & Considerations

**Why we don't need `--allowedTools`:**
- Read/Grep/basic tools are in the default toolset
- Only specify if you want to restrict or add tools (like MCP servers)

**Why we don't need `--permission-mode acceptEdits`:**
- Repos are mounted read-only anyway
- Claude won't be making edits in our use case
- If we later allow writes, then we'd add this flag

**Session cleanup:**
- Sessions naturally expire after some time
- Could add cleanup logic to remove old entries from thread_sessions
- Not critical since it's in-memory and gets wiped on restart anyway

**Concurrency:**
- ThreadPoolExecutor handles concurrent requests
- Each thread gets its own session_id
- No conflicts since thread_ts is unique per Slack thread

## Testing Strategy

1. **First iteration:** Replace echo subprocess with Claude Code command
2. **Test single turn:** Mention bot, verify response
3. **Test multi-turn:** Reply in thread, verify session_id is reused
4. **Test concurrent:** Mention multiple bots, verify independent sessions
5. **Test restart:** Restart bot, verify it rebuilds context from Slack history