import json
import subprocess
from unittest.mock import Mock, patch

import pytest

from src.claude.cli_wrapper import ClaudeCLIError, ClaudeCLIWrapper


def test_cli_wrapper_command_construction():
    wrapper = ClaudeCLIWrapper(repo_path="/path/to/repo", timeout=300, max_turns=40, allowed_tools=["Read", "Grep"])
    cmd = wrapper._build_command("test prompt", None)
    assert cmd == [
        "claude",
        "-p",
        "test prompt",
        "--output-format",
        "json",
        "--max-turns",
        "40",
        "--allowed-tools",
        "Read,Grep",
    ]


def test_cli_wrapper_with_session_resume():
    wrapper = ClaudeCLIWrapper(repo_path="/path/to/repo", timeout=300, max_turns=40, allowed_tools=[])
    cmd = wrapper._build_command("test prompt", "session_123")
    assert "--resume" in cmd
    assert "session_123" in cmd


def test_cli_wrapper_invoke_success():
    mock_result = Mock()
    mock_result.stdout = json.dumps({"result": "Response text", "session_id": "sess_123"})

    with patch("subprocess.run", return_value=mock_result) as mock_run:
        wrapper = ClaudeCLIWrapper("/path/to/repo", 300, 40, [])
        result = wrapper.invoke("test prompt", None)

        assert result["result"] == "Response text"
        assert result["session_id"] == "sess_123"
        mock_run.assert_called_once()


def test_cli_wrapper_timeout_propagates():
    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("claude", 300)):
        wrapper = ClaudeCLIWrapper("/path/to/repo", 300, 40, [])
        with pytest.raises(subprocess.TimeoutExpired):
            wrapper.invoke("test prompt", None)


def test_cli_wrapper_json_error():
    mock_result = Mock()
    mock_result.stdout = "invalid json"

    with patch("subprocess.run", return_value=mock_result):
        wrapper = ClaudeCLIWrapper("/path/to/repo", 300, 40, [])
        with pytest.raises(ClaudeCLIError):
            wrapper.invoke("test prompt", None)
