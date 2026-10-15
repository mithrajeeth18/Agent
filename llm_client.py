"""Gemini client and strict model-output validation."""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Protocol

from dotenv import load_dotenv
from pydantic import ValidationError

from prompts import repair_prompt
from schemas import AgentDecision

MODEL_NAME = "gemini-3.5-flash-lite"


class LLMError(RuntimeError):
    """Raised when Gemini cannot supply a usable decision."""


class LLMClient(Protocol):
    """Small interface that lets tests replace Gemini with a deterministic fake."""

    def generate(self, prompt: str, system_instruction: str) -> str:
        """Return raw model text for one prompt."""


def strip_markdown_fences(text: str) -> str:
    """Remove one accidental outer Markdown code fence from a model response."""
    cleaned = text.strip()
    match = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", cleaned, flags=re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else cleaned


def parse_decision(text: str) -> AgentDecision:
    """Parse and validate a JSON-only model response."""
    try:
        data = json.loads(strip_markdown_fences(text))
    except json.JSONDecodeError as error:
        raise ValueError(f"invalid JSON: {error.msg} at line {error.lineno}, column {error.colno}") from error
    try:
        return AgentDecision.model_validate(data)
    except ValidationError as error:
        raise ValueError(f"schema validation failed: {error}") from error


class GeminiClient:
    """Synchronous Gemini API adapter with bounded retries and no secret logging."""

    def __init__(self, env_file: Path | None = None, model: str = MODEL_NAME, retries: int = 3) -> None:
        load_dotenv(dotenv_path=env_file, override=False)
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise LLMError("GEMINI_API_KEY is not set; add it to .env or the environment")
        self.model = model
        self.retries = retries
        try:
            from google import genai
        except ImportError as error:
            raise LLMError("Missing dependency: install requirements.txt before running the agent") from error
        self._client = genai.Client(api_key=self.api_key)

    def generate(self, prompt: str, system_instruction: str) -> str:
        """Call Gemini and retry transient failures with exponential backoff."""
        last_error: Exception | None = None
        for attempt in range(self.retries):
            try:
                response = self._client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config={"system_instruction": system_instruction, "temperature": 0.1},
                )
                if not response.text:
                    raise LLMError("Gemini returned an empty response")
                return response.text
            except Exception as error:  # Provider exceptions vary by SDK release.
                last_error = error
                if attempt + 1 < self.retries:
                    time.sleep(2**attempt)
        raise LLMError(f"Gemini request failed after {self.retries} attempts: {last_error}")


def request_decision(client: LLMClient, prompt: str, system_instruction: str) -> tuple[AgentDecision, str]:
    """Get one decision, allowing a single repair request for malformed JSON."""
    raw = client.generate(prompt, system_instruction)
    try:
        return parse_decision(raw), raw
    except ValueError as error:
        repaired = client.generate(repair_prompt(raw, str(error)), system_instruction)
        try:
            return parse_decision(repaired), repaired
        except ValueError as repaired_error:
            raise LLMError(f"Gemini returned invalid JSON twice: {repaired_error}") from repaired_error
