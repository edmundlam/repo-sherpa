"""Slack app setup and lifecycle management."""

import logging
import os
import threading

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

logger = logging.getLogger(__name__)


class SlackAppManager:
    """Manages Slack app instances and Socket Mode handlers."""

    def __init__(self, config: dict) -> None:
        """Initialize app manager.

        Args:
            config: Bot configuration dict
        """
        self.config = config
        self.apps: dict[str, dict] = {}

    def setup_bot(self, bot_name: str, bot_config: dict, handler: callable) -> App | None:
        """Initialize a bot with its event handler.

        Args:
            bot_name: Bot name from config
            bot_config: Bot-specific configuration
            handler: Event handler callable

        Returns:
            App instance if successful, None if tokens missing
        """
        # Load tokens from environment
        bot_token_key = f"{bot_name.upper()}_BOT_TOKEN"
        app_token_key = f"{bot_name.upper()}_APP_TOKEN"

        bot_token = os.getenv(bot_token_key)
        app_token = os.getenv(app_token_key)

        if not bot_token or not app_token:
            logger.warning(f"Missing tokens for {bot_name}, skipping...")
            return None

        # Create Slack App instance
        app = App(token=bot_token)

        # Register event handler
        app.event("app_mention")(handler)

        self.apps[bot_name] = {"app": app, "config": bot_config}

        logger.info(f"Configured bot: {bot_name} (repo: {bot_config['repo_path']})")
        return app

    def start_handlers(self) -> list[threading.Thread]:
        """Start Socket Mode handlers for all configured bots.

        Returns:
            List of handler threads
        """
        threads = []
        for bot_name, bot_data in self.apps.items():
            app_token_key = f"{bot_name.upper()}_APP_TOKEN"
            app_token = os.getenv(app_token_key)

            handler = SocketModeHandler(bot_data["app"], app_token)

            # Start handler in a separate thread
            thread = threading.Thread(target=handler.start, daemon=True)
            thread.start()
            threads.append(thread)
            logger.info(f"Started handler for: {bot_name}")

        logger.info("All bots started, listening for mentions...")
        return threads
