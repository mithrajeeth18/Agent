"""Execution of validated local actions."""

from __future__ import annotations

import subprocess
import time
import re
import shlex
from pathlib import Path
from typing import Callable

from platform_utils import PlatformInfo, detect_platform, shell_command
from safety import is_within_workspace, review_shell_command
from schemas import Action, ExecutionResult


class ActionExecutor:
    """Run one approved action inside a configurable workspace."""

    def __init__(self, workspace: Path, platform_info: PlatformInfo | None = None, timeout: int = 120) -> None:
        self.workspace = workspace.resolve()
        self.platform = platform_info or detect_platform()
        self.timeout = timeout

    def execute(self, action: Action, confirm: Callable[[str], bool] | None = None) -> ExecutionResult:
        """Execute one action and return all observable process details."""
        if action.type == "none":
            return ExecutionResult(exit_code=0)
        if action.type == "write_file":
            return self._write_file(action)
        return self._run_shell(action.command, confirm)

    def _write_file(self, action: Action) -> ExecutionResult:
        target = (self.workspace / action.path).resolve() if not Path(action.path).is_absolute() else Path(action.path).resolve()
        if not is_within_workspace(target, self.workspace):
            return ExecutionResult(exit_code=None, blocked=True, block_reason="write_file target is outside the workspace")
        started = time.monotonic()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(action.content, encoding="utf-8")
        return ExecutionResult(exit_code=0, stdout=f"Wrote {target.relative_to(self.workspace)}", duration=time.monotonic() - started)

    def _run_shell(self, command: str, confirm: Callable[[str], bool] | None) -> ExecutionResult:
        command = self._normalize_python_command(command)
        policy_command = self._command_for_policy(command)
        policy = review_shell_command(policy_command, self.workspace)
        if not policy.allowed:
            return ExecutionResult(exit_code=None, blocked=True, block_reason=policy.reason)
        if policy.requires_confirmation and (confirm is None or not confirm(policy.reason)):
            return ExecutionResult(exit_code=None, blocked=True, block_reason=f"confirmation required: {policy.reason}")
        started = time.monotonic()
        try:
            process = subprocess.run(
                shell_command(command, self.platform), cwd=self.workspace, capture_output=True,
                text=True, encoding="utf-8", errors="replace", timeout=self.timeout, check=False,
            )
            return ExecutionResult(exit_code=process.returncode, stdout=process.stdout, stderr=process.stderr, duration=time.monotonic() - started)
        except subprocess.TimeoutExpired as error:
            return ExecutionResult(exit_code=None, stdout=error.stdout or "", stderr=error.stderr or "", timed_out=True, duration=time.monotonic() - started)

    def _normalize_python_command(self, command: str) -> str:
        """Use the current interpreter when a command starts with python/python3."""
        stripped = command.strip()
        own_python = re.escape(self.platform.python_executable)
        match = re.match(rf"^(?:{own_python}|python(?:3(?:\.\d+)?)?)\b", stripped)
        if not match:
            return command
        executable = self.platform.python_executable
        if self.platform.os_name != "Windows":
            executable = shlex.quote(executable)
        return f"{executable}{stripped[match.end():]}"

    def _command_for_policy(self, command: str) -> str:
        """Hide only the executor's own interpreter path from the path-escape policy."""
        if command.startswith(self.platform.python_executable):
            return f"python3{command[len(self.platform.python_executable):]}"
        quoted = shlex.quote(self.platform.python_executable)
        if command.startswith(quoted):
            return f"python3{command[len(quoted):]}"
        return command
