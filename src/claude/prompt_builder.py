"""Prompt formatting from Slack thread context."""

import logging

logger = logging.getLogger(__name__)


class PromptBuilder:
    """Builds prompts for Claude from Slack thread history."""

    @staticmethod
    def build(
        messages: list[dict],
        repo_path: str,
        last_message_ts: str | None = None,
        max_history: int | None = None,
    ) -> str:
        """Format Slack thread history into a prompt for Claude.

        Args:
            messages: List of Slack message dicts
            repo_path: Path to the git repository
            last_message_ts: Only include messages after this timestamp (for session resume)
            max_history: Maximum number of messages to include (safety cap)

        Returns:
            Formatted prompt string
        """
        if not messages:
            return ""

        # Filter messages to only include new ones since last response
        if last_message_ts:
            # Parse Slack timestamp (format: "1234567890.123456")
            try:
                last_ts_float = float(last_message_ts)
                messages = [m for m in messages if float(m.get("ts", "0")) > last_ts_float]
                logger.debug(f"Filtered to {len(messages)} messages since ts={last_message_ts}")
            except (ValueError, TypeError):
                logger.warning(f"Invalid last_message_ts: {last_message_ts}, using full context")

        # Apply max_history cap
        if max_history and len(messages) > max_history:
            messages = messages[-max_history:]
            logger.debug(f"Capped to last {max_history} messages")

        # Handle empty result after filtering
        if not messages:
            logger.warning("No messages after filtering, falling back to full thread context")
            return f"You are working in the repository at: {repo_path}"

        if len(messages) == 1:
            # Single message - just return the question
            return f"{messages[0]['text']}\n\nYou are working in the repository at: {repo_path}"

        # Build context from thread history
        context = "Previous conversation:\n"
        for msg in messages[:-1]:
            role = "Assistant" if msg.get("bot_id") else "User"
            context += f"{role}: {msg['text']}\n"

        # Add current question
        current_question = messages[-1]["text"]
        context += f"\nCurrent question: {current_question}\n"
        context += f"\nYou are working in the repository at: {repo_path}"

        return context
