"""Session ID management for thread continuity."""

import logging

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages thread_ts -> session_id mappings for conversation continuity."""

    def __init__(self) -> None:
        """Initialize empty session storage."""
        self._sessions: dict[str, str] = {}

    def get_session(self, thread_ts: str) -> str | None:
        """Retrieve session_id for a thread.

        Args:
            thread_ts: Slack thread timestamp

        Returns:
            Session ID if exists, None otherwise
        """
        return self._sessions.get(thread_ts)

    def set_session(self, thread_ts: str, session_id: str) -> None:
        """Store session_id for a thread.

        Args:
            thread_ts: Slack thread timestamp
            session_id: Claude session ID
        """
        self._sessions[thread_ts] = session_id
