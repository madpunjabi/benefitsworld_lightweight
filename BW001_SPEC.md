# BW-001 — Maintain Maya Torres's CalFresh Case

## Target difficulty
Strong final version:
- 45–90 minutes human-equivalent workload
- 80–250 meaningful agent actions
- 400–500 hard max steps
- 5 agent-visible apps
- 20–30 checkpoints
- 5–8 dynamic events
- 1+ context reset

MVP can begin smaller and grow.

## Day 0 — income verification
Portal: PENDING, income verification required, old employer still listed.

Files include:
- current paystub
- stale paystub
- termination letter
- current lease
- expired lease
- distractor

Agent should inspect policy, reconcile employer history, choose current evidence, upload it, and verify receipt.

## Interview phase
After correct income docs actually persist, interview requirement appears. One offered slot conflicts with household calendar. Agent must choose a valid slot and verify appointment.

## Housing phase
After interview scheduling, new inbox message requests housing proof. Agent must notice new information, distinguish current vs expired lease, upload current lease, and verify.

## Silent failure
First attempt at one consequential upload displays success but does not persist. Agent must re-observe state, detect failure, retry, and verify.

## Later change
Advance simulated time. New employer/income evidence appears and prior income becomes stale. Agent must update its world model and determine the needed administrative action using policy.

## Context reset
Clear benchmark conversational context. External world persists. Persistent condition retains its files. Agent must reconstruct current responsibility.

## Recertification
Later simulated time: recertification notice, deadline, newer evidence. Agent must complete and verify.

## Terminal success
- case status ACTIVE/approved as defined by scenario
- no open requirements
- interview satisfied
- recertification cleared
- required docs actually received
- no unresolved required user question
