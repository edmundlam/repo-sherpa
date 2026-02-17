from src.claude.prompt_builder import PromptBuilder


def test_single_message_returns_as_is():
    messages = [{"text": "How does auth work?"}]
    result = PromptBuilder.build(messages, "/path/to/repo")
    # Single messages now include repo path for consistency
    assert result == "How does auth work?\n\nYou are working in the repository at: /path/to/repo"


def test_thread_with_history():
    messages = [
        {"text": "How does auth work?", "bot_id": None},
        {"text": "Auth uses JWT tokens", "bot_id": "B12345"},
        {"text": "What about refresh tokens?", "bot_id": None},
    ]
    result = PromptBuilder.build(messages, "/path/to/repo")
    assert "Previous conversation:" in result
    assert "User: How does auth work?" in result
    assert "Assistant: Auth uses JWT tokens" in result
    assert "Current question: What about refresh tokens?" in result
    assert "/path/to/repo" in result


def test_empty_messages():
    messages = []
    result = PromptBuilder.build(messages, "/path/to/repo")
    assert result == ""


def test_filtering_by_last_message_ts():
    """Test that only messages after last_message_ts are included."""
    messages = [
        {"text": "Old message 1", "ts": "1000000000.000001"},
        {"text": "Old message 2", "ts": "1000000000.000002"},
        {"text": "New message", "ts": "1000000000.000003"},
    ]
    result = PromptBuilder.build(messages, "/path/to/repo", last_message_ts="1000000000.000002")
    # Only the new message should be included
    assert "Old message 1" not in result
    assert "Old message 2" not in result
    assert "New message" in result
    assert "/path/to/repo" in result


def test_max_history_cap():
    """Test that max_history caps the number of messages."""
    messages = [{"text": f"Message {i}", "ts": f"1000000000.00000{i}"} for i in range(10)]
    result = PromptBuilder.build(messages, "/path/to/repo", max_history=3)
    # Only last 3 messages should be included
    assert "Message 0" not in result
    assert "Message 6" not in result
    assert "Message 7" in result
    assert "Message 8" in result
    assert "Message 9" in result


def test_filtering_and_max_history_combined():
    """Test that filtering and max_history work together."""
    messages = [{"text": f"Message {i}", "ts": f"1000000000.00000{i}"} for i in range(10)]
    # Filter to messages after index 4, then cap at 3
    result = PromptBuilder.build(messages, "/path/to/repo", last_message_ts="1000000000.000004", max_history=3)
    # Should include messages 5-9, capped at last 3 (7, 8, 9)
    assert "Message 4" not in result
    assert "Message 5" not in result
    assert "Message 6" not in result
    assert "Message 7" in result
    assert "Message 8" in result
    assert "Message 9" in result
