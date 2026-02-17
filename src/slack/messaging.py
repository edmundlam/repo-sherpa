"""Slack messaging and reaction utilities."""

import logging
from slack_bolt import App


logger = logging.getLogger(__name__)


class SlackMessaging:
    """Handles Slack API interactions for messages and reactions."""

    def __init__(self, app: App) -> None:
        """Initialize messaging wrapper.

        Args:
            app: Slack Bolt App instance
        """
        self.app = app
        self.client = app.client

    def add_reaction(self, channel: str, timestamp: str, emoji: str) -> bool:
        """Add emoji reaction to a message.

        Args:
            channel: Slack channel ID
            timestamp: Message timestamp
            emoji: Emoji name (without colons)

        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.reactions_add(
                channel=channel,
                timestamp=timestamp,
                name=emoji
            )
            logger.info(f"Added {emoji} reaction to {timestamp}")
            return True
        except Exception as e:
            logger.warning(f"Failed to add {emoji} reaction: {e}")
            return False

    def remove_reaction(self, channel: str, timestamp: str, emoji: str) -> bool:
        """Remove emoji reaction from a message.

        Args:
            channel: Slack channel ID
            timestamp: Message timestamp
            emoji: Emoji name (without colons)

        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.reactions_remove(
                channel=channel,
                timestamp=timestamp,
                name=emoji
            )
            logger.info(f"Removed {emoji} reaction from {timestamp}")
            return True
        except Exception as e:
            logger.warning(f"Failed to remove {emoji} reaction: {e}")
            return False

    def post_message(self, say: callable, text: str, thread_ts: str) -> None:
        """Post message to Slack thread with mrkdwn formatting.

        Args:
            say: Slack Bolt say function
            text: Message text
            thread_ts: Thread timestamp
        """
        say(
            text=text,
            thread_ts=thread_ts,
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": text
                    }
                }
            ]
        )

    def fetch_thread_context(self, channel: str, thread_ts: str) -> list[dict]:
        """Fetch all messages in a thread.

        Args:
            channel: Slack channel ID
            thread_ts: Thread timestamp

        Returns:
            List of message dicts, empty list on error
        """
        try:
            result = self.client.conversations_replies(
                channel=channel,
                ts=thread_ts
            )
            messages = result["messages"]
            logger.debug(f"Fetched {len(messages)} messages from thread {thread_ts}")
            return messages
        except Exception as e:
            logger.error(f"Error fetching thread context: {e}")
            return []
