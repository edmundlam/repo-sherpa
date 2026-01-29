import os
import yaml
import threading
import subprocess
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

    def process_request(self, bot_name, event, say, client):
        """Process a bot mention request"""
        config = self.apps[bot_name]['config']
        thread_ts = event.get('thread_ts') or event['ts']
        channel = event['channel']

        try:
            # Fetch thread context
            messages = self.fetch_thread_context(
                self.apps[bot_name]['app'],
                channel,
                thread_ts
            )

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

        except subprocess.TimeoutExpired:
            say(
                text=f"Error: Request timed out after {config['timeout']} seconds",
                thread_ts=thread_ts
            )
        except Exception as e:
            say(
                text=f"Error: {str(e)}",
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
