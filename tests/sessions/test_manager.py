import pytest
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
