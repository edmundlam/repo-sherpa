import os
import yaml
import threading
import subprocess
import json
from concurrent.futures import ThreadPoolExecutor
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv


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
                print(f"Warning: Missing tokens for {bot_name}, skipping...")
                continue

            # Create Slack App instance
            app = App(token=bot_token)

            # Register event handler
            app.event("app_mention")(self._make_app_mention_handler(bot_name, bot_config))

            self.apps[bot_name] = {
                'app': app,
                'config': bot_config
            }

            print(f"Configured bot: {bot_name}")

    def _make_app_mention_handler(self, bot_name, bot_config):
        """Create a handler closure with bot_name and bot_config in scope"""
        def handler(event, say, client):
            # Extract thread_ts (use event['ts'] if no thread exists)
            thread_ts = event.get('thread_ts') or event['ts']

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
            return result['messages']
        except Exception as e:
            print(f"Error fetching thread context: {e}")
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

            # Build Claude Code command
            cmd = ['claude', '-p', prompt, '--output-format', 'json']
            if session_id:
                cmd.extend(['--resume', session_id])

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
            print(f"Started handler for: {bot_name}")

        # Keep main thread alive
        try:
            for thread in threads:
                thread.join()
        except KeyboardInterrupt:
            print("\nShutting down...")
