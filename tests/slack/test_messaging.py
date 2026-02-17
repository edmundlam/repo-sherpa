from unittest.mock import MagicMock, Mock

from src.slack.messaging import SlackMessaging


def test_add_reaction_success():
    mock_app = Mock()
    mock_app.client.reactions_add = MagicMock()
    messaging = SlackMessaging(mock_app)

    result = messaging.add_reaction("C123", "123.456", "eyes")
    assert result is True
    mock_app.client.reactions_add.assert_called_once_with(channel="C123", timestamp="123.456", name="eyes")


def test_add_reaction_failure():
    mock_app = Mock()
    mock_app.client.reactions_add = MagicMock(side_effect=Exception("Failed"))
    messaging = SlackMessaging(mock_app)

    result = messaging.add_reaction("C123", "123.456", "eyes")
    assert result is False


def test_remove_reaction_success():
    mock_app = Mock()
    mock_app.client.reactions_remove = MagicMock()
    messaging = SlackMessaging(mock_app)

    result = messaging.remove_reaction("C123", "123.456", "eyes")
    assert result is True
    mock_app.client.reactions_remove.assert_called_once_with(channel="C123", timestamp="123.456", name="eyes")


def test_post_message_calls_say():
    mock_app = Mock()
    messaging = SlackMessaging(mock_app)

    mock_say = Mock()
    messaging.post_message(mock_say, "Test message", "123.456")

    mock_say.assert_called_once()
    call_kwargs = mock_say.call_args.kwargs
    assert call_kwargs["text"] == "Test message"
    assert call_kwargs["thread_ts"] == "123.456"
    assert "blocks" in call_kwargs


def test_fetch_thread_context():
    mock_app = Mock()
    mock_app.client.conversations_replies = MagicMock(return_value={"messages": [{"text": "msg1"}, {"text": "msg2"}]})
    messaging = SlackMessaging(mock_app)

    messages = messaging.fetch_thread_context("C123", "123.456")

    assert len(messages) == 2
    mock_app.client.conversations_replies.assert_called_once_with(channel="C123", ts="123.456")


def test_fetch_thread_context_error():
    mock_app = Mock()
    mock_app.client.conversations_replies = MagicMock(side_effect=Exception("API Error"))
    messaging = SlackMessaging(mock_app)

    messages = messaging.fetch_thread_context("C123", "123.456")
    assert messages == []
