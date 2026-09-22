# BenefitsWorld — Master Spec

## Thesis

The bet is not "AI can answer SNAP questions." It is:

> Frontier agents may be nearing the point where they can persistently own a public-benefits case: maintaining correct state across software, documents, policy, changing facts, failures, deadlines, and time.

## Durable user objective

> Keep this household's CalFresh case in good standing. Resolve administrative blockers, follow applicable instructions, ask the household only when facts or authorization are genuinely missing, and stop only when no further administrative action is required.

The agent receives this outcome, NOT a checklist.

## Must test
- GUI/browser navigation
- long action sequences
- cross-source reasoning
- current vs stale evidence
- multiple simultaneous requirements
- policy retrieval/application
- dynamic events
- hidden backend truth
- silent/partial failure
- verification
- proactive clarification
- persistent state
- context reset
- later recertification/deadlines

## Experimental conditions

### A. Naive
Objective + browser tools + normal context only.

### B. Persistent
Same model/task/environment plus:
- objective.md
- case_state.json
- task_queue.json
- evidence_log.jsonl
- action_log.jsonl

Loop: OBSERVE -> PLAN -> ACT -> VERIFY -> UPDATE -> DECIDE.

## Primary metric
Binary end-to-end resolution based on external world state.

## Secondary metrics
Checkpoint score, verification rate, state accuracy, human questions, constraint violations, dynamic-event capture, recovery rate, action count, cost/tokens if available.

## V1 scope
Build BW-001 only until it is deterministic, human-completable, agent-runnable, and evaluatable.
