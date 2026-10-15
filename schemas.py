"""Validated contracts exchanged between the model and the local agent."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class SkillNeeded(BaseModel):
    """A document skill that should be included in the next model prompt."""

    type: Literal["docx", "pdf", "pptx", "xlsx", "none"] = "none"
    action: str = ""


class Action(BaseModel):
    """One action proposed by the model."""

    type: Literal["shell", "write_file", "none"] = "none"
    command: str = ""
    path: str = ""
    content: str = ""

    @model_validator(mode="after")
    def validate_action_fields(self) -> "Action":
        """Require fields that make an executable action meaningful."""
        if self.type == "shell" and not self.command.strip():
            raise ValueError("shell actions require a non-empty command")
        if self.type == "write_file" and not self.path.strip():
            raise ValueError("write_file actions require a non-empty path")
        return self


class AgentDecision(BaseModel):
    """The strict JSON decision returned by the language model."""

    agentic: bool
    previous_step_ok: bool | None
    reasoning: str
    skill_needed: SkillNeeded = Field(default_factory=SkillNeeded)
    action: Action = Field(default_factory=Action)
    done: bool
    response: str

    @model_validator(mode="after")
    def validate_completion(self) -> "AgentDecision":
        """Disallow claiming completion while asking Python to execute work."""
        if self.done and self.action.type != "none":
            raise ValueError("done decisions must not contain an executable action")
        return self


class ExecutionResult(BaseModel):
    """A serializable result from a local action."""

    exit_code: int | None
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False
    duration: float = 0.0
    blocked: bool = False
    block_reason: str = ""
