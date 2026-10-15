"""Local command policy for the coding agent."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SafetyDecision:
    """The policy outcome for a proposed action."""

    allowed: bool
    requires_confirmation: bool = False
    reason: str = ""


_DENY_PATTERNS = (
    (r"\b(shutdown|reboot|halt|poweroff)\b", "system power commands are not allowed"),
    (r"\b(diskutil\s+erase|format\s+[a-z]:|mkfs\.)", "disk formatting commands are not allowed"),
    (r"\b(reg(?:\.exe)?\s+(add|delete)|regedit)\b", "registry modifications are not allowed"),
    (r"\b(keychain|security\s+find-|credential|/etc/shadow)\b", "credential access is not allowed"),
    (r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f?\s+(/|~)(?:\s|$)", "recursive deletion outside the workspace is not allowed"),
)
_CONFIRM_PATTERNS = (
    (r"\b(rm|rmdir|del|erase|Remove-Item)\b", "delete operation"),
    (r"\b(pip|npm|brew|winget|choco)\s+(install|add)\b", "package installation"),
    (r"\b(curl|wget|Invoke-WebRequest|git\s+clone)\b", "network download"),
)
_WORKSPACE_ESCAPE_PATTERNS = (
    (r"(?:^|[\s'\"])\.\.(?:/|\\)", "paths using .. are outside the workspace policy"),
    (r"(?:^|[\s'\"])[~/]", "home-directory or absolute paths are outside the workspace policy"),
    (r"\bcd\s+(?:\.\.|/|~)", "changing outside the workspace is not allowed"),
)


def review_shell_command(command: str, workspace: Path) -> SafetyDecision:
    """Classify a shell command; the caller prompts before confirmed operations."""
    normalized = command.strip()
    for pattern, reason in _DENY_PATTERNS:
        if re.search(pattern, normalized, flags=re.IGNORECASE):
            return SafetyDecision(False, reason=reason)
    for pattern, reason in _WORKSPACE_ESCAPE_PATTERNS:
        if re.search(pattern, normalized, flags=re.IGNORECASE):
            return SafetyDecision(False, reason=reason)
    for pattern, reason in _CONFIRM_PATTERNS:
        if re.search(pattern, normalized, flags=re.IGNORECASE):
            return SafetyDecision(True, requires_confirmation=True, reason=reason)
    return SafetyDecision(True)


def is_within_workspace(path: Path, workspace: Path) -> bool:
    """Return whether a path resolves inside the configured workspace."""
    try:
        path.resolve().relative_to(workspace.resolve())
    except ValueError:
        return False
    return True
