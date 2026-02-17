from src.sessions.manager import SessionManager


def test_session_manager_initially_empty():
    manager = SessionManager()
    assert manager.get_session("thread_123") is None


def test_set_and_get_session():
    manager = SessionManager()
    manager.set_session("thread_123", "session_abc")
    assert manager.get_session("thread_123") == "session_abc"


def test_multiple_sessions():
    manager = SessionManager()
    manager.set_session("thread_1", "session_a")
    manager.set_session("thread_2", "session_b")
    assert manager.get_session("thread_1") == "session_a"
    assert manager.get_session("thread_2") == "session_b"


def test_overwrite_session():
    manager = SessionManager()
    manager.set_session("thread_1", "session_a")
    manager.set_session("thread_1", "session_b")
    assert manager.get_session("thread_1") == "session_b"


def test_get_session_metadata():
    """Test retrieving full session metadata."""
    manager = SessionManager()
    manager.update_session("thread_123", "session_abc", "1234567890.123456")

    metadata = manager.get_session_metadata("thread_123")
    assert metadata is not None
    assert metadata["session_id"] == "session_abc"
    assert metadata["last_message_ts"] == "1234567890.123456"


def test_get_session_metadata_returns_none_for_nonexistent():
    """Test that get_session_metadata returns None for non-existent sessions."""
    manager = SessionManager()
    assert manager.get_session_metadata("nonexistent") is None


def test_update_session():
    """Test updating session with full metadata."""
    manager = SessionManager()
    manager.update_session("thread_123", "session_abc", "1234567890.123456")

    # Verify metadata was stored
    metadata = manager.get_session_metadata("thread_123")
    assert metadata["session_id"] == "session_abc"
    assert metadata["last_message_ts"] == "1234567890.123456"

    # Verify get_session_id still works
    assert manager.get_session_id("thread_123") == "session_abc"


def test_backwards_compatible_set_session():
    """Test that old set_session method still works (creates empty timestamp)."""
    manager = SessionManager()
    manager.set_session("thread_123", "session_abc")

    metadata = manager.get_session_metadata("thread_123")
    assert metadata["session_id"] == "session_abc"
    assert metadata["last_message_ts"] == ""  # Empty string for backwards compat


def test_update_session_overwrites():
    """Test that update_session overwrites existing metadata."""
    manager = SessionManager()
    manager.update_session("thread_123", "session_a", "1000000000.000001")
    manager.update_session("thread_123", "session_b", "2000000000.000002")

    metadata = manager.get_session_metadata("thread_123")
    assert metadata["session_id"] == "session_b"
    assert metadata["last_message_ts"] == "2000000000.000002"
