"""Interactive CLI entry point for the general-purpose local agent."""

from __future__ import annotations

import argparse
from pathlib import Path

from llm_client import GeminiClient, LLMError
from orchestrator import Orchestrator


def parse_args() -> argparse.Namespace:
    """Read command-line options for one agent request."""
    parser = argparse.ArgumentParser(description="Run the Gemini-powered local coding and document agent.")
    parser.add_argument("request", nargs="?", help="Natural-language task. Omit it to be prompted interactively.")
    parser.add_argument("--workspace", type=Path, default=None, help="Workspace directory (default: project Workspace/).")
    parser.add_argument("--max-loops", type=int, default=15, help="Maximum LLM/action iterations (default: 15).")
    return parser.parse_args()


def main() -> int:
    """Start a single visible agent run and return a shell-friendly exit status."""
    args = parse_args()
    request = args.request or input("What would you like the agent to do?\n> ").strip()
    if not request:
        print("No request provided.")
        return 2
    if args.max_loops < 1:
        print("--max-loops must be at least 1.")
        return 2
    project_root = Path(__file__).resolve().parent
    workspace = (args.workspace or project_root / "Workspace").resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    try:
        client = GeminiClient(env_file=project_root / ".env")
        runner = Orchestrator(client, workspace, project_root, max_loops=args.max_loops)
        print(f"Model: {client.model}")
        print(f"Workspace: {runner.executor.workspace}")
        final_response = runner.run(request)
    except LLMError as error:
        print(f"Agent could not start: {error}")
        return 1
    except KeyboardInterrupt:
        print("\nAgent cancelled.")
        return 130
    print(f"\n=== final_response ===\n{final_response}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
