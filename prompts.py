"""Prompt templates used by the local coding agent."""

from __future__ import annotations

from platform_utils import PlatformInfo


DECISION_JSON = """{
  "agentic": true,
  "previous_step_ok": null,
  "reasoning": "short explanation",
  "skill_needed": {"type": "none", "action": ""},
  "action": {"type": "none", "command": "", "path": "", "content": ""},
  "done": false,
  "response": "short user-facing status"
}"""


def system_prompt(platform: PlatformInfo, workspace: str) -> str:
    """Create the invariant instruction sent with every model request."""
    return f"""You are a careful general-purpose coding and document agent.
Return STRICT JSON ONLY. Do not use Markdown fences or add commentary.

Your JSON must exactly match this shape:
{DECISION_JSON}

Rules:
- agentic is true only if the request needs more than one LLM call. A one-answer request is false.
- The first decision must include both classification and the first executable action when an action is needed.
- If a previous action result is present, set previous_step_ok based on that result. Correct failures before continuing.
- Prefer write_file to create textual files. Never use a shell command for file content creation when write_file works.
- Always verify created or modified work before done=true.
- An action with type none is required when done=true.
- For document work, select the appropriate skill type and prefer its supplied scripts.
- Use only syntax valid for the detected shell.
- Every shell command runs inside Workspace. Use relative paths only; never use `..`, `~`, or absolute paths.
- Do not type the Python executable path: use `python` or `python3`; the executor maps it to the detected interpreter.

Runtime:
- OS: {platform.os_name}
- Shell: {platform.shell_name}
- Python executable: {platform.python_executable}
- Workspace: {workspace}
"""


def repair_prompt(raw_response: str, validation_error: str) -> str:
    """Ask the model to repair a malformed decision without changing its intent."""
    return f"""Your prior response was not valid for the required AgentDecision JSON schema.
Validation error: {validation_error}

Return only corrected JSON matching this exact schema, with no Markdown fences:
{DECISION_JSON}

Prior response:
{raw_response}
"""
