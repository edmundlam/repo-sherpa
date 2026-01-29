import os
import yaml
import threading
import subprocess
import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class MultiRepoBot:
    def __init__(self, config_path):
        load_dotenv()
        self.config = yaml.safe_load(open(config_path))
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.apps = {}
        self.handlers = {}
        self.thread_sessions = {}  # Maps thread_ts -> Claude session_id
        self._setup_bots()

    def _setup_bots(self):
        """Initialize each bot from config"""
        for bot_name, bot_config in self.config['bots'].items():
            # Load tokens from environment
            bot_token_key = f"{bot_name.upper()}_BOT_TOKEN"
            app_token_key = f"{bot_name.upper()}_APP_TOKEN"

            bot_token = os.getenv(bot_token_key)
            app_token = os.getenv(app_token_key)

            if not bot_token or not app_token:
                logger.warning(f"Missing tokens for {bot_name}, skipping...")
                continue

            # Create Slack App instance
            app = App(token=bot_token)

            # Register event handler
            app.event("app_mention")(self._make_app_mention_handler(bot_name, bot_config))

            self.apps[bot_name] = {
                'app': app,
                'config': bot_config
            }

            logger.info(f"Configured bot: {bot_name} (repo: {bot_config['repo_path']})")

    def _make_app_mention_handler(self, bot_name, bot_config):
        """Create a handler closure with bot_name and bot_config in scope"""
        def handler(event, say, client):
            thread_ts = event.get('thread_ts') or event['ts']
            channel = event.get('channel')

            logger.info(f"[{bot_name}] Request received - channel: {channel}, thread: {thread_ts}")

            # Add reaction to indicate we're working on it
            try:
                client.reactions_add(
                    channel=channel,
                    timestamp=event['ts'],
                    name='hourglass_flowing_sand'
                )
                logger.debug(f"[{bot_name}] Added hourglass reaction to {event['ts']}")
            except Exception as e:
                logger.warning(f"[{bot_name}] Failed to add reaction: {e}")

            # Submit job to executor for async processing
            self.executor.submit(self.process_request, bot_name, event, say, client)

        return handler

    def fetch_thread_context(self, bot_app, channel, thread_ts):
        """Fetch all messages in a thread"""
        try:
            result = bot_app.client.conversations_replies(
                channel=channel,
                ts=thread_ts
            )
            messages = result['messages']
            logger.debug(f"Fetched {len(messages)} messages from thread {thread_ts}")
            return messages
        except Exception as e:
            logger.error(f"Error fetching thread context: {e}")
            return []

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

    def process_request(self, bot_name, event, say, client):
        """Process a Slack mention and respond using Claude Code"""
        config = self.apps[bot_name]['config']
        thread_ts = event.get('thread_ts') or event['ts']
        channel = event['channel']
        start_time = time.time()

        logger.info(f"[{bot_name}] Processing request - thread: {thread_ts}")

        try:
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

            if session_id:
                logger.info(f"[{bot_name}] Resuming session {session_id[:8]}...")
            else:
                logger.info(f"[{bot_name}] Starting new session")

            # Build Claude Code command
            cmd = ['claude', '-p', prompt, '--output-format', 'json']
            if session_id:
                cmd.extend(['--resume', session_id])

            # Run Claude Code
            claude_start = time.time()
            result = subprocess.run(
                cmd,
                cwd=config['repo_path'],
                capture_output=True,
                text=True,
                timeout=config['timeout']
            )
            claude_duration = time.time() - claude_start

            # Parse JSON response
            output = json.loads(result.stdout)

            # Store session_id for future turns in this thread
            self.thread_sessions[thread_ts] = output['session_id']

            # Calculate response length for logging
            response_length = len(output['result'])
            total_duration = time.time() - start_time

            logger.info(
                f"[{bot_name}] Response sent - "
                f"Claude: {claude_duration:.2f}s, "
                f"Total: {total_duration:.2f}s, "
                f"Chars: {response_length}, "
                f"Session: {output['session_id'][:8]}..."
            )

            # Post response to Slack thread
            say(
                text=output['result'],
                thread_ts=thread_ts
            )

            # Remove the hourglass reaction
            try:
                self.apps[bot_name]['app'].client.reactions_remove(
                    channel=channel,
                    timestamp=event['ts'],
                    name='hourglass_flowing_sand'
                )
                logger.debug(f"[{bot_name}] Removed hourglass reaction from {event['ts']}")
            except Exception as e:
                logger.warning(f"[{bot_name}] Failed to remove reaction: {e}")

        except subprocess.TimeoutExpired:
            logger.error(f"[{bot_name}] Request timed out after {config['timeout']}s")
            say(
                text="Request timed out - the task took too long to complete.",
                thread_ts=thread_ts
            )
        except json.JSONDecodeError as e:
            logger.error(f"[{bot_name}] JSON decode error: {e}")
            say(
                text=f"Error parsing Claude response: {str(e)}",
                thread_ts=thread_ts
            )
        except Exception as e:
            logger.error(f"[{bot_name}] Unexpected error: {e}", exc_info=True)
            say(
                text=f"Error processing request: {str(e)}",
                thread_ts=thread_ts
            )

    def start(self):
        """Start all bot handlers"""
        threads = []
        for bot_name, bot_data in self.apps.items():
            app_token_key = f"{bot_name.upper()}_APP_TOKEN"
            app_token = os.getenv(app_token_key)

            handler = SocketModeHandler(bot_data['app'], app_token)

            # Start handler in a separate thread
            thread = threading.Thread(target=handler.start, daemon=True)
            thread.start()
            threads.append(thread)
            logger.info(f"Started handler for: {bot_name}")

        logger.info("All bots started, listening for mentions...")

        # Keep main thread alive
        try:
            for thread in threads:
                thread.join()
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            logger.info(f"Active sessions: {len(self.thread_sessions)}")
