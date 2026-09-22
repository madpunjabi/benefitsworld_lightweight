# Milestone 3 — Dynamic interview + housing events

Implement deterministic event engine.

Event 1: after correct income docs actually persist -> clear income requirement, add interview notice, unlock slots.

Event 2: after valid non-conflicting interview scheduled -> add unread inbox request for current housing proof and add portal housing requirement.

Build /inbox /calendar + scheduling.

Acceptance:
- events fire once
- exact replay after reset
- conflicting slot cannot satisfy evaluator
- housing request appears only after scheduling
- human golden path works

Tests, screenshots, commit, STOP.
