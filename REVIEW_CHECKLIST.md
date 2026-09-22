# Review Checklist — bring this to ChatGPT after every milestone

Provide:
1. Claude's summary
2. git diff --stat
3. git log --oneline -5
4. test output
5. screenshots
6. progress.md
7. architecture decisions/questions

We will check:
- world truth separated from agent-visible state
- evaluator inaccessible to agent
- deterministic events/reset
- business logic not hidden in UI hacks
- difficulty comes from state/reasoning, not broken UX
- agent receives outcome, not checklist
- stale/current evidence requires reading contents/dates
- new events can invalidate plans
- silent failures require verification
- context reset preserves external responsibility
- binary success is external state, not prose
