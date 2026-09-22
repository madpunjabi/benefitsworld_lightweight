# BenefitsWorld — Start Here

Build a lightweight local benchmark, not OSWorld itself.

The benchmark tests two frontiers:
1. OSWorld-style computer use: cross-app navigation, long action sequences, hidden state, failures, verification.
2. Longitudinal agency: facts changing over simulated days/weeks, deadlines, stale information, context resets, and resumption.

## Workflow
1. Open this folder in Claude Code.
2. Ask Claude to read every spec file.
3. Paste `prompts/00_PLAN_ONLY.md`.
4. STOP after Claude's plan and bring its plan, proposed schema, and risks back to ChatGPT for review.
5. Only after review, proceed one milestone at a time.

After every milestone, bring ChatGPT:
- Claude's summary
- `git diff --stat`
- `git log --oneline -5`
- test output
- screenshots
- `progress.md`

Do not let Claude one-shot the project.
