# Milestone 1 — Shell + deterministic state

Implement only:
- React/Vite shell
- FastAPI backend
- SQLite
- scenario loader
- deterministic reset
- simulated clock
- routes /portal /inbox /files /calendar /policy /agent /lab

Placeholder UI is fine. `/lab` must show current simulated day, scenario id, and backend case status.

Acceptance:
- `./init.sh` starts everything
- reset twice yields identical world state
- simulated day advances deterministically
- /lab reads backend truth
- agent-visible routes cannot access evaluator/future-event endpoints

Test with Playwright, save screenshots, update progress, commit, STOP.
