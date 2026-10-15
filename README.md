# Gemini Local Agent

A visible, cross-platform CLI agent for general coding and document work. Gemini 3.5 Flash-Lite proposes one strict JSON decision at a time; the program safely executes it, returns the result, and requires verification before completion.

## Current status

Implemented: Gemini client with `GEMINI_API_KEY`; Pydantic JSON validation and one repair attempt; deterministic macOS/Windows shell detection; safe subprocess execution and workspace-only file writes; confirmation/deny policies; multi-step verification loop; document-skill routing; JSONL traces; verbose terminal output; `App.py` CLI; and unit tests.

Still to verify: install dependencies, perform a live Gemini task, run the `mithrajeeth` even/odd demo, and exercise each supplied document skill against real documents.

## Project map

- `App.py` — main executable CLI; `main.py` is a compatibility wrapper.
- `orchestrator.py` — model/action/verification loop.
- `llm_client.py` — Gemini calls, retries, and strict response parsing.
- `executor.py`, `platform_utils.py`, `safety.py` — local execution policy.
- `schemas.py`, `context.py`, `skill_router.py`, `trace_logger.py`, `prompts.py` — contracts and agent state.
- `Document skills/` — supplied DOCX, PDF, PPTX, and XLSX instructions; do not modify without an explicit request.
- `tests/` — tests using a fake model and no API calls.

## Setup

Python 3.10+ is required. Keep the existing `.env` secret and untracked:

```dotenv
GEMINI_API_KEY=your_key_here
```

```bash
python3 -m pip install -r requirements.txt
```

## Run

```bash
python3 App.py "Create a Python file named mithrajeeth with an even/odd function, verify its contents, and run it."
```

Or run interactively:

```bash
python3 App.py
```

By default, every action runs inside the project’s `Workspace/` folder. File writes and command output therefore stay separate from the agent source. Shell commands use that folder as their working directory and reject obvious path escapes (`..`, `~`, and absolute paths).

To deliberately use another dedicated workspace:

```bash
python3 App.py --workspace /absolute/path/to/workspace "Your request"
```

The agent prints its system prompt, dynamic prompt, raw model response, validated decision, action, and result to the terminal. API-key values are never printed. Each run also writes `logs/run-*.jsonl`.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

Expected: eight passing tests. The recovery tests deliberately fail once, then verify the fake model corrects and retries the work.

## Handoff for future agents

Start with this README, then read `schemas.py`, `orchestrator.py`, and `safety.py`. Preserve the JSON decision contract and never expose `.env` values. The source of truth model is `gemini-3.5-flash-lite`.
