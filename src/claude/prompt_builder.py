"""Prompt formatting from Slack thread context."""

import logging

logger = logging.getLogger(__name__)


class PromptBuilder:
    """Builds prompts for Claude from Slack thread history."""

    @staticmethod
    def build(messages: list[dict], repo_path: str) -> str:
        """Format Slack thread history into a prompt for Claude.

        Args:
            messages: List of Slack message dicts
            repo_path: Path to the git repository

        Returns:
            Formatted prompt string
        """
        if not messages:
            return ""

        if len(messages) == 1:
            # First message in thread - just return the question
            return messages[0]["text"]

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
