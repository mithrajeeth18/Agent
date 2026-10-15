"""Host operating-system detection and shell command construction."""

from __future__ import annotations

import platform
import shutil
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class PlatformInfo:
    """Details needed to execute shell commands without using an LLM."""

    os_name: str
    shell_name: str
    shell_prefix: tuple[str, ...]
    python_executable: str


def detect_platform(system_name: str | None = None) -> PlatformInfo:
    """Detect the host platform and choose its supported shell deterministically."""
    system = system_name or platform.system()
    if system == "Darwin":
        return PlatformInfo("macOS", "/bin/zsh", ("/bin/zsh", "-c"), sys.executable)
    if system == "Windows":
        powershell = shutil.which("powershell") or shutil.which("pwsh")
        if powershell:
            return PlatformInfo("Windows", powershell, (powershell, "-NoProfile", "-Command"), sys.executable)
        return PlatformInfo("Windows", "cmd.exe", ("cmd.exe", "/d", "/s", "/c"), sys.executable)
    return PlatformInfo(system or "Unknown", "/bin/sh", ("/bin/sh", "-c"), sys.executable)


def shell_command(command: str, info: PlatformInfo) -> list[str]:
    """Return the argument list used to invoke *command* using the selected shell."""
    return [*info.shell_prefix, command]
