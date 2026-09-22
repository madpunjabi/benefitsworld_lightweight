# Milestone 6 — Benchmark agent runner

Build separate model runner. Claude Code is builder; benchmark model is a separate invocation.

Allowed benchmark tools only:
- navigate
- inspect visible page
- click
- type
- upload visible household file
- refresh
- screenshot
- ask_user
- advance simulated time when permitted

Never expose DB, evaluator, future events, simulator tags.

Save every run:
- transcript.jsonl
- tool_calls.jsonl
- screenshots/
- eval_result.json
- summary.md

Support configs: naive, persistent.

Validate first with stub/test agent. STOP after tests/commit.
