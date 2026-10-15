"""Bounded prompt context for iterative agent execution."""

from __future__ import annotations

from dataclasses import dataclass, field

from schemas import ExecutionResult


def truncate_output(value: str, limit: int = 4_000) -> str:
    """Keep both the start and end of a long command output."""
    if len(value) <= limit:
        return value
    half = limit // 2
    return f"{value[:half]}\n... [truncated] ...\n{value[-half:]}"


def result_summary(result: ExecutionResult) -> str:
    """Create the full-but-bounded action result supplied to the next model call."""
    return (
        f"exit_code={result.exit_code}; timed_out={result.timed_out}; blocked={result.blocked}; "
        f"duration={result.duration:.2f}s; block_reason={result.block_reason!r}\n"
        f"STDOUT:\n{truncate_output(result.stdout)}\nSTDERR:\n{truncate_output(result.stderr, 4_000)}"
    )


@dataclass
class AgentContext:
    """Keeps only the state that remains useful across loop iterations."""

    original_request: str
    completed_steps: list[str] = field(default_factory=list)
    last_result: str = ""
    token_limit: int = 24_000

    def record(self, step: str, result: ExecutionResult) -> None:
        """Store a compact completed-step line and the latest detailed result."""
        self.completed_steps.append(step)
        self.last_result = result_summary(result)
        self._compact()

    def render(self, skill_instruction: str = "") -> str:
        """Produce the dynamic portion of the model prompt."""
        steps = "\n".join(f"- {item}" for item in self.completed_steps) or "- None yet"
        return (
            f"Original user request:\n{self.original_request}\n\n"
            f"Completed steps:\n{steps}\n\n"
            f"Last action result:\n{self.last_result or 'No action has run yet.'}"
            f"{skill_instruction}\n\nDecide the next action now."
        )

    def _compact(self) -> None:
        """Collapse old history when its approximate token count grows too large."""
        while self._estimated_tokens() > self.token_limit and len(self.completed_steps) > 4:
            collapsed = self.completed_steps[:2]
            self.completed_steps[:2] = [f"Earlier completed work: {' | '.join(collapsed)}"]

    def _estimated_tokens(self) -> int:
        return (len(self.original_request) + len(self.last_result) + sum(map(len, self.completed_steps))) // 4
