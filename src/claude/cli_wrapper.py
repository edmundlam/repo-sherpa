"""Claude CLI subprocess wrapper."""

import json
import logging
import subprocess


logger = logging.getLogger(__name__)


class ClaudeCLIError(Exception):
    """Raised when Claude CLI invocation fails."""
    pass


class ClaudeCLIWrapper:
    """Wraps Claude Code CLI subprocess execution."""

    def __init__(
        self,
        repo_path: str,
        timeout: int,
        max_turns: int,
        allowed_tools: list[str]
    ) -> None:
        """Initialize CLI wrapper.

        Args:
            repo_path: Path to git repository
            timeout: Request timeout in seconds
            max_turns: Maximum Claude turns
            allowed_tools: List of allowed tool names
        """
        self.repo_path = repo_path
        self.timeout = timeout
        self.max_turns = max_turns
        self.allowed_tools = allowed_tools

    def _build_command(self, prompt: str, session_id: str | None) -> list[str]:
        """Build Claude CLI command arguments.

        Args:
            prompt: User prompt
            session_id: Optional session ID to resume

        Returns:
            Command argument list
        """
        cmd = ["claude", "-p", prompt, "--output-format", "json"]
        cmd.extend(["--max-turns", str(self.max_turns)])

        if self.allowed_tools:
            cmd.extend(["--allowed-tools", ",".join(self.allowed_tools)])

        if session_id:
            cmd.extend(["--resume", session_id])

        return cmd

    def invoke(self, prompt: str, session_id: str | None) -> dict:
        """Invoke Claude CLI and parse response.

        Args:
            prompt: User prompt
            session_id: Optional session ID to resume

        Returns:
            Dict with 'result' and 'session_id' keys

        Raises:
            subprocess.TimeoutExpired: If CLI times out
            ClaudeCLIError: If JSON parsing fails
        """
        cmd = self._build_command(prompt, session_id)

        result = subprocess.run(
            cmd,
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            timeout=self.timeout
        )

        try:
            output = json.loads(result.stdout)
            return output
        except json.JSONDecodeError as e:
            logger.error(
                "Failed to parse Claude CLI response as JSON",
                exc_info=True,
                extra={
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode
                }
            )
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
            logger.error(f"Return code: {result.returncode}")
            raise ClaudeCLIError(f"Failed to parse Claude response: {e}") from e
