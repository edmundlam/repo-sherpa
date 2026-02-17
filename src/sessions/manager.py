"""Session ID management for thread continuity."""

import logging

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages thread_ts -> session metadata mappings for conversation continuity."""

    def __init__(self) -> None:
        """Initialize empty session storage."""
        self._sessions: dict[str, dict] = {}

    def get_session_metadata(self, thread_ts: str) -> dict | None:
        """Retrieve full session metadata for a thread.

        Args:
            thread_ts: Slack thread timestamp

        Returns:
            Dict with 'session_id' and 'last_message_ts' if exists, None otherwise
        """
        return self._sessions.get(thread_ts)

    def get_session_id(self, thread_ts: str) -> str | None:
        """Retrieve only session_id for a thread (backwards compatible).

        Args:
            thread_ts: Slack thread timestamp

        Returns:
            Session ID if exists, None otherwise
        """
        metadata = self._sessions.get(thread_ts)
        return metadata["session_id"] if metadata else None

    def get_session(self, thread_ts: str) -> str | None:
        """Retrieve session_id for a thread (deprecated: use get_session_id).

        Args:
            thread_ts: Slack thread timestamp

        Returns:
            Session ID if exists, None otherwise
        """
        return self.get_session_id(thread_ts)

    def update_session(self, thread_ts: str, session_id: str, last_message_ts: str) -> None:
        """Store or update session metadata for a thread.

        Args:
            thread_ts: Slack thread timestamp
            session_id: Claude session ID
            last_message_ts: Timestamp of last message we responded to
        """
        self._sessions[thread_ts] = {
            "session_id": session_id,
            "last_message_ts": last_message_ts,
        }

    def set_session(self, thread_ts: str, session_id: str) -> None:
        """Store session_id for a thread (deprecated: use update_session).

        Args:
            thread_ts: Slack thread timestamp
            session_id: Claude session ID
        """
        # For backwards compatibility, create metadata with empty timestamp
        self.update_session(thread_ts, session_id, "")
