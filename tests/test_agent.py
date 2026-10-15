"""Focused tests for the cross-platform local agent."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from executor import ActionExecutor
from orchestrator import Orchestrator
from platform_utils import detect_platform, shell_command
from schemas import Action, AgentDecision
from safety import review_shell_command
from skill_router import SkillRouter


class FakeLLM:
    def __init__(self, decisions: list[dict[str, object]]) -> None:
        self.decisions = decisions
        self.index = 0

    def generate(self, prompt: str, system_instruction: str) -> str:
        response = self.decisions[self.index]
        self.index += 1
        return json.dumps(response)


def decision(*, action: dict[str, str], done: bool = False, previous: bool | None = None, response: str = "") -> dict[str, object]:
    return {
        "agentic": True, "previous_step_ok": previous, "reasoning": "test step",
        "skill_needed": {"type": "none", "action": ""}, "action": action,
        "done": done, "response": response,
    }


class SchemaTests(unittest.TestCase):
    def test_done_cannot_include_action(self) -> None:
        with self.assertRaises(ValueError):
            AgentDecision.model_validate(decision(action={"type": "shell", "command": "pwd", "path": "", "content": ""}, done=True))


class ExecutorTests(unittest.TestCase):
    def test_mocked_macos_and_windows_shells(self) -> None:
        self.assertEqual(shell_command("echo ok", detect_platform("Darwin")), ["/bin/zsh", "-c", "echo ok"])
        windows = detect_platform("Windows")
        self.assertEqual(windows.os_name, "Windows")
        self.assertIn(windows.shell_prefix[-1], {"-Command", "/c"})

    def test_write_file_stays_in_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = ActionExecutor(Path(directory)).execute(Action(type="write_file", path="nested/file.txt", content="ok"))
            self.assertEqual(result.exit_code, 0)
            self.assertEqual((Path(directory) / "nested/file.txt").read_text(), "ok")

    def test_shell_path_escape_is_blocked(self) -> None:
        self.assertFalse(review_shell_command("cat ../secret.txt", Path.cwd()).allowed)

    def test_own_python_executable_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            executor = ActionExecutor(Path(directory))
            command = f"{executor.platform.python_executable} -c \"print('ok')\""
            result = executor.execute(Action(type="shell", command=command))
            self.assertEqual(result.exit_code, 0)
            self.assertEqual(result.stdout.strip(), "ok")

    def test_presentation_request_gets_pptx_skill(self) -> None:
        skill = SkillRouter.infer_from_request("make a one slide ppt from this pdf")
        self.assertEqual(skill.type, "pptx")


class OrchestratorTests(unittest.TestCase):
    def test_failure_is_reported_then_recovered(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            client = FakeLLM([
                decision(action={"type": "shell", "command": "false", "path": "", "content": ""}),
                decision(action={"type": "write_file", "command": "", "path": "recovered.txt", "content": "ok"}, previous=False),
                decision(action={"type": "shell", "command": "test -f recovered.txt", "path": "", "content": ""}, previous=True),
                decision(action={"type": "none", "command": "", "path": "", "content": ""}, done=True, previous=True, response="Recovered"),
            ])
            answer = Orchestrator(client, workspace, Path.cwd(), max_loops=6).run("test recovery")
            self.assertEqual(answer, "Recovered")
            self.assertTrue((workspace / "recovered.txt").is_file())

    def test_same_command_can_run_after_a_file_correction(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            client = FakeLLM([
                decision(action={"type": "shell", "command": "test -f fixed.txt", "path": "", "content": ""}),
                decision(action={"type": "write_file", "command": "", "path": "fixed.txt", "content": "ok"}, previous=False),
                decision(action={"type": "shell", "command": "test -f fixed.txt", "path": "", "content": ""}, previous=True),
                decision(action={"type": "none", "command": "", "path": "", "content": ""}, done=True, previous=True, response="Fixed"),
            ])
            answer = Orchestrator(client, workspace, Path.cwd(), max_loops=6).run("retry after a correction")
            self.assertEqual(answer, "Fixed")
