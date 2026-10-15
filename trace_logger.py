"""JSONL tracing for a single agent run."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class TraceLogger:
    """Append structured, secret-free events to one run-specific JSONL file."""

    def __init__(self, log_dir: Path) -> None:
        log_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        self.path = log_dir / f"run-{stamp}.jsonl"

    def write(self, event: str, **data: Any) -> None:
        """Append one event; values must already exclude secrets."""
        record = {"timestamp": datetime.now(timezone.utc).isoformat(), "event": event, **data}
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
