import os
from unittest.mock import Mock, patch

from src.slack.app_manager import SlackAppManager


def test_app_manager_initialization():
    config = {"backend": {"repo_path": "/path/to/repo", "timeout": 300}}
    manager = SlackAppManager(config)
    assert manager.config == config
    assert manager.apps == {}


def test_setup_bot_creates_app():
    config = {"backend": {"repo_path": "/path/to/repo", "timeout": 300}}
    manager = SlackAppManager(config)

    mock_handler = Mock()
    with patch.dict(
        os.environ, {"BACKEND_BOT_TOKEN": "xoxb-test", "BACKEND_APP_TOKEN": "xapp-test"}
    ), patch("src.slack.app_manager.App") as mock_app_class:
        mock_app_instance = Mock()
        mock_app_class.return_value = mock_app_instance
        app = manager.setup_bot("backend", config["backend"], mock_handler)

    assert "backend" in manager.apps
    assert manager.apps["backend"]["app"] == mock_app_instance
    assert manager.apps["backend"]["config"] == config["backend"]
    mock_app_instance.event.assert_called_once_with("app_mention")


def test_setup_bot_missing_tokens_skips():
    config = {"backend": {"repo_path": "/path", "timeout": 300}}
    manager = SlackAppManager(config)

    with patch.dict(os.environ, {}, clear=False):
        app = manager.setup_bot("backend", config["backend"], Mock())

    assert "backend" not in manager.apps
    assert app is None


def test_start_handlers():
    config = {"backend": {"repo_path": "/path", "timeout": 300}}
    manager = SlackAppManager(config)

    mock_app = Mock()
    manager.apps["backend"] = {"app": mock_app, "config": config["backend"]}

    with patch.dict(os.environ, {"BACKEND_APP_TOKEN": "xapp-test"}):
        with patch("src.slack.app_manager.SocketModeHandler") as mock_handler_class:
            with patch("threading.Thread") as mock_thread:
                mock_thread_instance = Mock()
                mock_thread.return_value = mock_thread_instance
                threads = manager.start_handlers()

                assert len(threads) == 1
                mock_thread_instance.start.assert_called_once()
