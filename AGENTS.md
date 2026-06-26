# AGENTS.md

## Project overview
This repository contains a small Python utility that queries Claude Pro usage information from Claude's API. The main entry point is [claude_usage.py](claude_usage.py).

## Working conventions
- Keep changes minimal and focused on the requested task.
- Preserve the current CLI behavior and human-readable output format unless a task explicitly requires otherwise.
- Do not commit secrets. Local configuration should stay in [.env](.env) or environment variables.
- Keep dependencies declared in [requirements.txt](requirements.txt).

## Commands
- Install dependencies: `pip install -r requirements.txt`
- Run the checker: `python claude_usage.py`
- Show raw JSON output: `python claude_usage.py --json`
- On Windows, [start.bat](start.bat) demonstrates the same workflow using environment variables.

## Configuration
- `CLAUDE_SESSION_KEY` is required.
- `CLAUDE_ORG_ID` is optional; the script provides a default value if it is not set.
- The script reads configuration from environment variables or [.env](.env).

## Notes for agents
- If a request involves changing the script, keep the existing structure and output style intact.
- If the environment is missing dependencies, install them from [requirements.txt](requirements.txt) before running the script.
- Prefer small, targeted edits over broad refactors.
