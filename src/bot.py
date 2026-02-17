import sys
from pathlib import Path

# Add project root to path to resolve import conflicts
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
import random
import time
from concurrent.futures import ThreadPoolExecutor

import yaml
from dotenv import load_dotenv

from src.claude.cli_wrapper import ClaudeCLIError, ClaudeCLIWrapper
from src.claude.prompt_builder import PromptBuilder
from src.sessions.manager import SessionManager
from src.slack.app_manager import SlackAppManager
from src.slack.messaging import SlackMessaging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class MultiRepoBot:
    """Orchestrates multiple Slack bots for repository assistance."""

    def __init__(self, config_path: str) -> None:
        """Initialize bot from configuration file.

        Args:
            config_path: Path to bot_config.yaml
        """
        load_dotenv()
        with Path(config_path).open() as f:
            self.config = yaml.safe_load(f)
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.app_manager = SlackAppManager(self.config)
        self.thread_sessions = SessionManager()
        self._setup_bots()

    def _setup_bots(self) -> None:
        """Initialize each bot from config."""
        for bot_name, bot_config in self.config["bots"].items():
            handler = self._make_app_mention_handler(bot_name, bot_config)
            self.app_manager.setup_bot(bot_name, bot_config, handler)

    def _make_app_mention_handler(self, bot_name: str, bot_config: dict):
        """Create a handler closure with bot_name and bot_config in scope.

        Args:
            bot_name: Bot name from config
            bot_config: Bot-specific configuration

        Returns:
            Event handler function
        """

        def handler(event, say, client):
            thread_ts = event.get("thread_ts") or event["ts"]
            channel = event.get("channel")

            logger.info(f"[{bot_name}] Request received - channel: {channel}, thread: {thread_ts}")

            # Randomly select and add one reaction to indicate we're working on it
            emojis = bot_config.get("processing_emojis", ["hourglass_flowing_sand"])
            selected_emoji = random.choice(emojis)

            messaging = SlackMessaging(self.app_manager.apps[bot_name]["app"])
            messaging.add_reaction(channel, event["ts"], selected_emoji)

            # Submit job to executor for async processing
            self.executor.submit(self.process_request, bot_name, event, say, client, selected_emoji)

        return handler

    def process_request(self, bot_name: str, event: dict, say: callable, client: any, emoji: str) -> None:
        """Process a Slack mention and respond using Claude Code.

        Args:
            bot_name: Bot name
            event: Slack event dict
            say: Slack say function
            client: Slack client
            emoji: Selected emoji for cleanup
        """
        config = self.app_manager.apps[bot_name]["config"]
        thread_ts = event.get("thread_ts") or event["ts"]
        channel = event["channel"]
        start_time = time.time()

        logger.info(f"[{bot_name}] Processing request - thread: {thread_ts}")

        messaging = SlackMessaging(self.app_manager.apps[bot_name]["app"])

        try:
            # Fetch thread context from Slack
            messages = messaging.fetch_thread_context(channel, thread_ts)

            # Get context settings from config
            context_config = config.get("context", {})
            max_history = context_config.get("max_history", 100)

            # Get session metadata for this thread
            session_metadata = self.thread_sessions.get_session_metadata(thread_ts)
            session_id = None
            last_message_ts = None

            if session_metadata:
                session_id = session_metadata["session_id"]
                last_message_ts = session_metadata.get("last_message_ts")
                logger.info(
                    f"[{bot_name}] Resuming session {session_id[:8]}... (last response: {last_message_ts or 'unknown'})"
                )
            else:
                logger.info(f"[{bot_name}] Starting new session")

            # Format prompt from thread history with filtering
            logger.info(f"[{bot_name}] Building prompt... message = {messages[-1]['text'][:50]}...")
            prompt = PromptBuilder.build(
                messages, config["repo_path"], last_message_ts=last_message_ts, max_history=max_history
            )

            # Invoke Claude CLI
            claude_start = time.time()
            claude = ClaudeCLIWrapper(
                repo_path=config["repo_path"],
                timeout=config["timeout"],
                max_turns=config.get("max_turns", 40),
                allowed_tools=config.get("allowed_tools", []),
            )
            output = claude.invoke(prompt, session_id)
            claude_duration = time.time() - claude_start

            # Store session metadata for future turns in this thread
            # Use the current message timestamp as our "last response" marker
            self.thread_sessions.update_session(thread_ts, output["session_id"], event["ts"])

            # Calculate response length for logging
            response_length = len(output["result"])
            total_duration = time.time() - start_time

            logger.info(
                f"[{bot_name}] Response sent - "
                f"Claude: {claude_duration:.2f}s, "
                f"Total: {total_duration:.2f}s, "
                f"Chars: {response_length}, "
                f"Session: {output['session_id'][:8]}..."
            )

            # Post response to Slack thread
            messaging.post_message(say, output["result"], thread_ts)

            # Add success reaction
            messaging.add_reaction(channel, event["ts"], "white_check_mark")

        except TimeoutError:
            logger.error(f"[{bot_name}] Request timed out after {config['timeout']}s")
            error_msg = "Request timed out - the task took too long to complete."
            messaging.post_message(say, error_msg, thread_ts)
            messaging.add_reaction(channel, event["ts"], "x")
        except ClaudeCLIError as e:
            logger.error(f"[{bot_name}] Claude CLI error: {e}", exc_info=True)
            error_msg = f"Error parsing Claude response: {str(e)}"
            messaging.post_message(say, error_msg, thread_ts)
            messaging.add_reaction(channel, event["ts"], "x")
        except Exception as e:
            logger.error(f"[{bot_name}] Unexpected error: {e}", exc_info=True)
            error_msg = f"Error processing request: {str(e)}"
            messaging.post_message(say, error_msg, thread_ts)
            messaging.add_reaction(channel, event["ts"], "x")

    def start(self) -> None:
        """Start all bot handlers."""
        threads = self.app_manager.start_handlers()

        # Keep main thread alive
        try:
            for thread in threads:
                thread.join()
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            logger.info(f"Active sessions: {len(self.thread_sessions._sessions)}")
