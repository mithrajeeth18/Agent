"""The LLM → action → verification loop."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from context import AgentContext
from executor import ActionExecutor
from llm_client import LLMClient, request_decision
from prompts import system_prompt
from schemas import AgentDecision, ExecutionResult, SkillNeeded
from skill_router import SkillRouter
from trace_logger import TraceLogger


class Orchestrator:
    """Coordinate model decisions, safe local actions, and loop stop conditions."""

    def __init__(
        self, client: LLMClient, workspace: Path, project_root: Path | None = None,
        max_loops: int = 15, confirm: Callable[[str], bool] | None = None,
    ) -> None:
        self.executor = ActionExecutor(workspace)
        self.client = client
        self.max_loops = max_loops
        self.confirm = confirm or self._ask_confirmation
        root = project_root or Path(__file__).resolve().parent
        self.router = SkillRouter(root)
        self.trace = TraceLogger(root / "logs")

    def run(self, user_request: str) -> str:
        """Complete a request or return a clear, safe stop message."""
        context = AgentContext(user_request)
        active_skill = self.router.infer_from_request(user_request)
        consecutive_failures = 0
        previous_shell_command = ""
        system = system_prompt(self.executor.platform, str(self.executor.workspace))
        self._print("system_prompt", system)
        self._print("trace_file", str(self.trace.path))

        for iteration in range(1, self.max_loops + 1):
            skill_text = self.router.instruction_for(active_skill)
            prompt = context.render(skill_text)
            self._print("prompt", prompt)
            self.trace.write("prompt", iteration=iteration, summary=prompt[:2_000], skill=active_skill.model_dump())
            decision, raw_json = request_decision(self.client, prompt, system)
            self._print("raw_model_response", raw_json)
            self._print("validated_decision", decision.model_dump_json(indent=2))
            self.trace.write("decision", iteration=iteration, raw_json=raw_json, decision=decision.model_dump())
            active_skill = SkillNeeded()  # A skill is injected for one decision only.

            if decision.done:
                self.trace.write("completed", iteration=iteration, response=decision.response)
                return decision.response

            if decision.action.type == "none":
                return "The model did not provide an action or completion. Please refine the request."
            if decision.action.type == "shell":
                if decision.action.command == previous_shell_command:
                    return "Stopped because the model repeated an identical shell command without an intervening correction."
                previous_shell_command = decision.action.command
            else:
                previous_shell_command = ""

            result = self.executor.execute(decision.action, self.confirm)
            self._print("action", decision.action.model_dump_json(indent=2))
            self._print("result", result.model_dump_json(indent=2))
            self.trace.write("action", iteration=iteration, action=decision.action.model_dump())
            self.trace.write("result", iteration=iteration, result=result.model_dump())
            context.record(f"{decision.action.type}: {decision.reasoning[:240]}", result)
            active_skill = decision.skill_needed

            if self._failed(result):
                consecutive_failures += 1
                if consecutive_failures >= 3:
                    return "Stopped after three consecutive failed actions. Please provide guidance."
            else:
                consecutive_failures = 0

        return f"Stopped after reaching the configured limit of {self.max_loops} steps. Check {self.trace.path} for progress."

    @staticmethod
    def _failed(result: ExecutionResult) -> bool:
        return result.blocked or result.timed_out or result.exit_code not in (0, None)

    @staticmethod
    def _ask_confirmation(reason: str) -> bool:
        answer = input(f"Confirmation required for {reason}. Continue? [y/N]: ").strip().lower()
        return answer in {"y", "yes"}

    @staticmethod
    def _print(event: str, payload: object) -> None:
        """Print observable agent progress without ever printing API credentials."""
        print(f"\n=== {event} ===\n{payload}", flush=True)
