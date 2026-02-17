from src.claude.prompt_builder import PromptBuilder


def test_single_message_returns_as_is():
    messages = [{"text": "How does auth work?"}]
    result = PromptBuilder.build(messages, "/path/to/repo")
    assert result == "How does auth work?"


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
