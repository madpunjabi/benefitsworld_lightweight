# BenefitsWorld — Implementation Plan (Milestone 0 output, revision 2)

> Plan only. No product code written against this plan yet. Execution proceeds
> one milestone at a time per `prompts/01_BUILD_SHELL.md` … `07_RUN_EXPERIMENT.md`,
> with a STOP + review checkpoint (see `REVIEW_CHECKLIST.md`) after each.
>
> Revision 2 incorporates the architecture review: separate agent/lab
> frontends, browser-only benchmark-agent access, harness-controlled time,
> no server-side agent-belief model in V1, single source of truth for
> document receipt, expanded action-log actors, deadline-as-world-event,
> and hardened isolation between the benchmark agent and research truth.
> See "Changes from revision 1" at the end for a full diff summary.

## Actor/environment terminology (used consistently below)

- **Benchmark agent** — the model being evaluated. Browser-only access to
  the agent environment. Never "Claude" alone in this doc — always
  "benchmark agent" when referring to the evaluated model.
- **Claude Code** — the implementation engineer building BenefitsWorld
  (this session). Not the benchmark subject.
- **Household** — the synthetic person (Maya Torres) whose case is managed.
  In V1, household responses are scripted/synthetic, not a live human.
- **Harness** — experiment infrastructure that resets state, advances
  simulated time, and invokes the benchmark agent. Distinct from the
  researcher.
- **System** — simulator-generated events (the event engine).
- **Researcher** — the human operating the Lab Console and analyzing runs.

## Goal

Build BW-001: a deterministic, human-completable, agent-runnable, evaluatable
local benchmark scenario simulating a household maintaining a CalFresh case,
per `MASTER_SPEC.md` and `BW001_SPEC.md`.

## Architecture summary

- **Two separate frontends**, not one:
  - `frontend-agent` (React + Vite) — Portal, Inbox, Files, Calendar, Policy,
    AgentStatus. Served at `http://localhost:5173`. This is the entire
    benchmark agent's world.
  - `frontend-lab` (React + Vite) — LabConsole only. Served at
    `http://localhost:5174`. Research infrastructure; the benchmark agent
    never receives this origin, a link to it, or any code that references it.
- **Backend:** one FastAPI + SQLite service, but internally split into a
  **public router** (mounted for `frontend-agent`) and a **lab router**
  (mounted for `frontend-lab` + the harness), gated by a static bearer
  token (`X-Lab-Token`) known only to `frontend-lab` and harness code —
  the simplest isolation that still fails closed if the benchmark agent's
  browser tries to call a lab/admin endpoint directly. Not production auth;
  a single shared secret read from env is sufficient for an experiment.
- **Browser automation:** Playwright, both for human golden-path
  verification (milestones 1-5) and later the benchmark agent runner
  (milestone 6). The benchmark agent's *only* tool surface is browser-style
  actions (navigate/inspect/click/type/upload/refresh/screenshot/ask
  household) implemented in `agent_runner.py` — never raw HTTP, DB, or
  filesystem access. The restriction is enforced at the tool layer (the
  runner's `navigate` tool rejects any target outside the `frontend-agent`
  origin; no tool exists that can reach `/lab` or issue arbitrary requests),
  not by asking the model to avoid it.
- **Simulated time:** an explicit `current_sim_day` integer in
  `world_state_meta`, advanced only through the lab-token-gated
  `/lab/clock/advance` endpoint, called by the harness (directly, or via a
  Lab Console control such as "Advance to Day 18"). The benchmark agent has
  no time-advancement tool; its job is to react correctly when it resumes
  after the harness has advanced time, not to decide when to advance it.
- **Document receipt has one source of truth:** the `uploads` table
  (`WHERE actually_persisted = 1`). No duplicated `received_document_ids`
  field anywhere else — every view that needs "what's been received" derives
  it from `uploads`.
- **Deadlines are world events, not evaluator-only penalties.** A missed
  recertification deadline is itself an `Event` (predicate: day past due
  and not completed; apply: case status transitions) — the same mechanism
  as every other state change, observable by the benchmark agent through
  the portal, and *then* judged by the evaluator.

### Four-state separation (ARCHITECTURE.md) — enforced how

| State | Where it lives | Who can read it |
|---|---|---|
| World state | `world_state.py` + SQLite tables (source of truth) | backend only |
| Visible state | `visible_state.py` projections | `frontend-agent` via public router (`/portal`, `/inbox`, `/files`, `/calendar`, `/policy`, `/agent`) |
| Agent belief | **not modeled server-side in V1.** Naive condition: implicit in the benchmark agent's own context, not reconstructed by us. Persistent condition (later milestone): the agent's own `case_state.json`/`evidence_log.jsonl` files serve as the explicit belief representation. | naive: nowhere (by design); persistent: the benchmark agent's own filesystem, and — once the persistent milestone lands — the Lab Console may read those same files to render a belief-vs-world diff for the researcher |
| Evaluator state | `evaluator.py` + lab router | research/lab only, gated by `X-Lab-Token`, never agent-visible |

`visible_state.py` is the *only* module allowed to translate world rows into
agent-facing schemas. No public route may query the DB directly or return a
raw model — every response passes through an explicit Pydantic "public"
schema that whitelists fields.

## Proposed directory tree

```
benefitsworld_lightweight/
  CLAUDE.md, MASTER_SPEC.md, ARCHITECTURE.md, BW001_SPEC.md,
  DATA_POLICY.md, EVAL_SPEC.md, REVIEW_CHECKLIST.md, START_HERE.md   (existing specs — see note on filenames below)
  IMPLEMENTATION_PLAN.md          (this file)
  progress.md
  feature_list.json
  tests.json
  init.sh                          # starts backend + both frontends for milestone 1 acceptance
  .env.example                     # LAB_TOKEN=... (dev default), documented, never committed with a real secret

  data/
    BW001_starter.json             # existing seed (household, docs, case, calendar)
    policy_library.json            # frozen policy corpus (added milestone 2)

  backend/
    requirements.txt
    app/
      __init__.py
      main.py                      # FastAPI app factory; mounts public_router (open, CORS: 5173+5174) and lab_router (X-Lab-Token required)
      config.py                    # scenario id, db path, frozen policy version, LAB_TOKEN
      security.py                  # require_lab_token() dependency; sanitized-exception handlers for public router
      db.py                        # SQLite engine/session helpers
      models.py                    # SQLAlchemy ORM models (one per table below)
      schemas/
        portal.py                  # public Pydantic schemas for /portal
        inbox.py
        files.py
        calendar.py
        policy.py
        agent.py
        lab.py                    # lab-only schemas (only ever imported by routes/lab.py)
      scenario_loader.py           # loads data/BW001_starter.json + policy_library.json into DB
      world_state.py               # read/write world truth; only module that mutates core tables
      visible_state.py             # projects world_state -> agent-visible view models; derives "documents received" from uploads
      event_engine.py              # scripted dynamic events, keyed to sim day / state predicates, including the recertification-deadline event
      clock.py                     # current_sim_day get/advance (lab-token-gated only)
      policy_store.py              # policy search/lookup
      action_log.py                # append-only agent/household/harness/system action logging
      evaluator.py                 # checkpoint + binary evaluation (lab-only consumer)
      reset.py                     # wipe + re-run scenario_loader deterministically
      agent_runner.py              # milestone 6: drives benchmark agent, browser-only tool surface, origin-restricted navigate
      routes/
        portal.py
        inbox.py
        files.py
        calendar.py
        policy.py
        agent.py                  # household-facing status/question endpoint
        lab.py                    # research + harness router: world_state, events, evaluator, action_log, reset, clock/advance — all behind require_lab_token()
    tests/
      conftest.py
      test_scenario_loader.py
      test_world_state.py
      test_visible_state_isolation.py   # asserts no lab-only field ever appears on any public route response
      test_lab_token_isolation.py       # asserts every lab-router path 401s without X-Lab-Token, 200s with it
      test_error_sanitization.py        # asserts a triggered public-route error never leaks stack traces/ORM/internal fields
      test_event_engine.py
      test_evaluator.py
      test_reset_determinism.py
      test_clock_determinism.py
      test_routes_portal.py
      test_routes_inbox.py
      test_routes_files.py
      test_routes_calendar.py
      test_routes_policy.py

  frontend-agent/
    package.json, vite.config.ts (port 5173), index.html
    src/
      main.tsx, App.tsx, router.tsx
      api/client.ts                # base URL = public API only; no lab origin, no lab token, anywhere in this bundle
      pages/
        Portal.tsx
        Inbox.tsx
        Files.tsx
        Calendar.tsx
        Policy.tsx
        AgentStatus.tsx

  frontend-lab/
    package.json, vite.config.ts (port 5174), index.html
    src/
      main.tsx, App.tsx
      api/labClient.ts              # base URL = lab API, attaches X-Lab-Token
      pages/
        LabConsole.tsx              # world state, events, evaluator, reset/advance-time controls; later: belief-vs-world diff

  e2e/
    playwright.config.ts
    tests/
      day0_income_golden_path.spec.ts        # milestone 2, runs against frontend-agent only
      interview_housing_golden_path.spec.ts  # milestone 3
      silent_failure_recovery.spec.ts        # milestone 4
      longitudinal_reset.spec.ts             # milestone 5
      agent_frontend_isolation.spec.ts       # milestone 1: crawl frontend-agent's built bundle/DOM, assert no reference to :5174, /lab, or X-Lab-Token
    screenshots/                             # saved run artifacts, gitignored contents except .gitkeep

  runs/                                       # milestone 6-7 benchmark-agent run artifacts, gitignored
```

### Note on spec filenames

The review draft referred to `DATA_AND_POLICY.md`, `prompts/03_EVENT_ENGINE.md`,
and `prompts/04_SILENT_FAILURE_AND_EVAL.md`. The files actually present in
this repository (re-verified via `ls` at the start of this revision) are
`DATA_POLICY.md`, `prompts/03_DYNAMIC_EVENTS.md`, and
`prompts/04_FAILURE_AND_EVAL.md` — no file with the review draft's names
exists, and my original plan already referenced the names that do exist.
Per the instruction not to create duplicate spec files to accommodate a
filename, this plan continues to reference the files that are actually on
disk. Flagged under "remaining ambiguity" below for a decision on whether
the three specs should be renamed to match the review draft (a rename I
have not performed).

## Proposed SQLite schema (changed tables only shown in full; unchanged tables — `household`, `documents`, `calendar_events`, `interview_slots`, `inbox_messages`, `policy_items`, `evaluator_checkpoints` — carry over from revision 1 unchanged)

```sql
CREATE TABLE world_state_meta (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  scenario_id TEXT NOT NULL,
  scenario_version TEXT NOT NULL,
  current_sim_day INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL
);

-- CHANGED: removed received_document_ids_json. Added recertification_json here
-- (still one row = current case state; recertification due-day/status is
-- part of that single row, not a second parallel store).
CREATE TABLE cases (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  case_id TEXT NOT NULL,
  status TEXT NOT NULL,                    -- PENDING | ACTIVE | RECERTIFICATION_OVERDUE | ... (scenario-defined enum)
  reported_employer TEXT,
  open_requirements_json TEXT NOT NULL,    -- ["earned_income_verification", ...]
  interview_json TEXT,                     -- {slot_id, scheduled_at_day, status} | null
  recertification_json TEXT,               -- {due_day, status} | null, added milestone 5
  updated_at TEXT NOT NULL
  -- NOTE: "documents received" is NOT stored here. Derive it as:
  --   SELECT document_id FROM uploads WHERE requirement = ? AND actually_persisted = 1
  -- visible_state.py exposes this as case.received_document_ids for the
  -- portal response, computed at read time, never stored redundantly.
);

CREATE TABLE uploads (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  document_id TEXT NOT NULL REFERENCES documents(id),
  requirement TEXT NOT NULL,               -- which open_requirement this targets
  attempted_at_day INTEGER NOT NULL,
  ui_reported_success INTEGER NOT NULL,    -- 1/0 — what the toast told the user
  actually_persisted INTEGER NOT NULL,     -- 1/0 — canonical truth for "was this received"
  scripted_failure_id TEXT                 -- FK-ish to silent_failures.id if this attempt was the scripted failure
);
-- Canonical source of truth for document receipt is this table
-- (WHERE actually_persisted = 1). No other table duplicates it.

CREATE TABLE silent_failures (
  id TEXT PRIMARY KEY,                     -- e.g. "SF-housing-upload-1"
  requirement TEXT NOT NULL,               -- e.g. "housing_verification"
  consumed INTEGER NOT NULL DEFAULT 0      -- 1 once the scripted first attempt has occurred
);

CREATE TABLE events (
  id TEXT PRIMARY KEY,                     -- e.g. "EVT-income-verified"
  event_type TEXT NOT NULL,
  trigger_description TEXT NOT NULL,       -- human-readable; predicate lives in code, not DB
  applied INTEGER NOT NULL DEFAULT 0,
  applied_at_day INTEGER
);

-- CHANGED: actor values expanded from {human, benchmark_agent} to four
-- distinct actors so trajectory analysis can tell them apart.
CREATE TABLE action_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  actor TEXT NOT NULL CHECK (actor IN ('benchmark_agent', 'household', 'harness', 'system')),
  sim_day INTEGER NOT NULL,
  action_type TEXT NOT NULL,               -- e.g. "upload_document", "schedule_interview", "advance_time", "event_applied"
  payload_json TEXT NOT NULL,
  result TEXT NOT NULL,                    -- "ok" | "rejected" | "no_op"
  created_at TEXT NOT NULL
);
```

Example `action_log` rows:

```text
actor=benchmark_agent  action_type=upload_document        payload={document_id: "D-101", requirement: "earned_income_verification"}
actor=system            action_type=event_applied           payload={event_id: "EVT-income-verified"}
actor=harness            action_type=advance_time             payload={to_day: 18}
actor=household          action_type=answer_agent_question    payload={question_id: "...", answer: "..."}
```

General rule applied throughout: **for every important fact, one
authoritative representation; everything else is a derived view.**

## Proposed API routes

### Public router — mounted for `frontend-agent`, CORS allows `http://localhost:5173` (and `:5174` so the Lab Console can also read public state for comparison; lab-only data still requires the token regardless of origin)

| Method | Path | Notes |
|---|---|---|
| GET | `/portal/case` | status, open_requirements, interview, recertification, **received documents derived from `uploads`** |
| POST | `/portal/uploads` | `{document_id, requirement}` → may silently fail per `silent_failures` |
| GET | `/portal/notices` | derived list of human-readable notices |
| POST | `/portal/interview/schedule` | `{slot_id}` |
| GET | `/inbox/messages` | |
| POST | `/inbox/messages/{id}/read` | |
| GET | `/files` | household documents + distractors; excludes `simulator_tags` |
| GET | `/calendar/events` | household + interview events |
| GET | `/policy/search?q=` | |
| GET | `/policy/{id}` | |
| GET | `/agent/status` | household-facing summary |
| POST | `/agent/question` | benchmark agent records a question that requires household/user input; logged with `actor=benchmark_agent`, answered later with `actor=household` |

No admin/reset/clock endpoints on this router. No endpoint here ever
returns `simulator_tags`, `actually_persisted`, `scripted_failure_id`,
checkpoint status, event definitions, or future-event data.

### Lab router — mounted for `frontend-lab` + harness, **every path requires `X-Lab-Token`** (`security.require_lab_token`)

| Method | Path | Notes |
|---|---|---|
| GET | `/lab/world_state` | full raw world truth |
| GET | `/lab/events` | scripted events + applied status |
| GET | `/lab/evaluator/checkpoints` | per-checkpoint status |
| GET | `/lab/evaluator/score` | binary result + failure taxonomy |
| GET | `/lab/action_log` | full action log, all actors |
| POST | `/lab/reset` | deterministic reset to Day 0; logs `actor=harness` |
| POST | `/lab/clock/advance` | `{to_day}`; advances sim day, triggers `event_engine.tick`; logs `actor=harness` |

The benchmark agent's tools (milestone 6) never call this router — there is
no navigate/click/type path that can reach it, because `agent_runner.py`'s
`navigate` tool only accepts URLs on the `frontend-agent` origin and no tool
performs raw HTTP calls at all.

## Proposed event-engine interface

Unchanged core shape from revision 1 — kept intentionally simple (no
workflow/orchestration framework):

```python
# backend/app/event_engine.py

from dataclasses import dataclass
from typing import Callable, Protocol

class WorldState(Protocol):
    """Narrow read/write facade event predicates and effects use."""
    def get_case(self) -> dict: ...
    def get_current_day(self) -> int: ...
    def has_received_document_tagged(self, tag: str) -> bool: ...   # reads uploads, not a redundant flag
    def set_open_requirement(self, requirement: str, present: bool) -> None: ...
    def add_inbox_message(self, subject: str, body: str) -> None: ...
    def unlock_interview_slots(self, slot_ids: list[str]) -> None: ...
    def set_case_status(self, status: str) -> None: ...              # used by the deadline-missed event

@dataclass
class Event:
    id: str
    description: str
    predicate: Callable[[WorldState], bool]   # True when trigger condition newly met
    apply: Callable[[WorldState], None]        # mutates world_state; checks `applied` before running

class EventEngine:
    def __init__(self, events: list[Event]):
        self.events = events

    def tick(self, world_state: WorldState) -> list[Event]:
        """Evaluate every not-yet-applied event's predicate in `events` list
        order (deterministic); apply and mark applied for each that newly
        fires; log each application with actor=system; return the events
        applied this tick."""
        ...
```

BW-001 events (milestones 3-5), now including the deadline consequence:

1. `EVT-income-verified` → income docs persisted ⇒ clear
   `earned_income_verification`, add interview notice, unlock slots.
2. `EVT-interview-scheduled` → valid non-conflicting slot booked ⇒ add
   unread inbox message requesting housing proof, add `housing_verification`
   requirement.
3. `EVT-silent-upload-failure` → scripted, consumes the `silent_failures` row
   on the first qualifying housing upload attempt.
4. `EVT-income-change` → `current_sim_day >= 18` ⇒ new employer/income
   document becomes available, Day-0 income evidence becomes stale, new
   requirement added.
5. `EVT-recertification-notice` → later `current_sim_day` threshold ⇒
   recertification requirement + `due_day` added to `cases.recertification_json`.
6. `EVT-recertification-deadline-missed` → `current_sim_day > due_day` and
   `recertification.status != 'completed'` ⇒ `case.status` transitions
   (exact terminal value — `RECERTIFICATION_OVERDUE` vs `CLOSED` — deferred
   to milestone 5 design per open ambiguity below). This is an ordinary
   event like the other five: no special-cased deadline logic anywhere else
   in the codebase. The benchmark agent can observe the status change on
   `/portal/case`; the evaluator then judges it as a binary-fail condition.

All events: deterministic, idempotent (`applied` guard), replayable after
reset, no wall-clock, no uncontrolled randomness, inaccessible to the
benchmark agent as future/pending data (the public router never lists
not-yet-applied events).

## Proposed evaluator interface

Unchanged from revision 1 — reads only backend truth, never model prose:

```python
# backend/app/evaluator.py

from dataclasses import dataclass
from typing import Callable

@dataclass
class Checkpoint:
    id: str
    description: str
    check: Callable[["WorldState", list[dict]], bool]  # (world_state, action_log rows) -> achieved?

@dataclass
class EvaluationResult:
    binary_success: bool
    checkpoints: dict[str, bool]
    checkpoint_score: float
    constraint_violations: list[str]
    primary_failure_category: str | None   # EVAL_SPEC.md taxonomy, or None on success
    action_count: int

class Evaluator:
    def __init__(self, checkpoints: list[Checkpoint], binary_fail_predicates: list[Callable[..., str | None]]):
        self.checkpoints = checkpoints
        self.binary_fail_predicates = binary_fail_predicates

    def evaluate(self, world_state, action_log: list[dict]) -> EvaluationResult:
        """Never reads agent transcript, explanation, confidence, or claim
        of completion — only world_state and action_log rows. A model
        stating "the case is resolved" has zero scoring value; only
        external state matters. Distinguishes high partial completion
        (checkpoint_score) from failed end-to-end responsibility
        (binary_success)."""
        ...
```

`evaluator.py` is imported only by `routes/lab.py` (behind
`require_lab_token`) and test code — never by any public router, enforced by
`test_visible_state_isolation.py` and `test_lab_token_isolation.py`.

## feature_list.json and tests.json

Both written alongside this plan (see files in repo root), revised to match
this architecture: milestone-1 scope is shell-only (no BW-001 content, no
events, no evaluator, no policy corpus yet — those move to their respective
milestones' feature entries), actor values match the four-way split, and
isolation/error-sanitization tests are explicit milestone-1 deliverables.
Every feature starts `"status": "failing"`; every test starts
`"status": "not_written"`. Updated milestone-by-milestone, never marked
passing without an actual test run (CLAUDE.md rules 5 and 7).

## Milestone sequence (unchanged — fixed by `prompts/01..07`)

0. **Plan only** (this document, revision 2) — no product code.
1. **Shell + deterministic state** (`01_BUILD_SHELL.md`) — now explicitly:
   FastAPI shell, SQLite, scenario loader, deterministic reset, simulated
   clock, **separate `frontend-agent` and `frontend-lab` shells**,
   placeholder routes, lab-token gating, and the isolation tests in item
   "Milestone-1 isolation tests" below. Does **not** include: full BW-001
   content, the event chain, silent failure, longitudinal state, the model
   runner, the policy corpus, recertification, or the persistent-agent
   condition. The point of milestone 1 is to prove world truth ≠
   agent-visible projection ≠ research view, and that reset/time
   infrastructure is deterministic — before any scenario content exists.
2. BW-001 Day 0 (`02_BUILD_DAY0.md`)
3. Dynamic interview + housing events (`prompts/03_DYNAMIC_EVENTS.md`)
4. Silent failure + evaluator (`prompts/04_FAILURE_AND_EVAL.md`)
5. Longitudinal layer (`05_LONGITUDINAL.md`) — now includes the
   recertification-deadline-missed event as a world-state transition.
6. Benchmark agent runner (`06_AGENT_RUNNER.md`) — browser-only tool
   surface, origin-restricted navigation, no time-advance tool.
7. Run experiment (`07_RUN_EXPERIMENT.md`)

## Milestone-1 isolation tests (new, explicit)

- **Deterministic reset:** `reset()` → snapshot A; mutate state; `reset()` →
  snapshot B; `assert A == B`.
- **Research isolation:** requests to `/lab/world_state`, `/lab/evaluator/*`,
  `/lab/events`, `/lab/reset`, `/lab/clock/advance` without `X-Lab-Token`
  return 401/403 with no body leakage; with the token, they succeed.
- **Visible-schema isolation:** every public-router response is asserted
  (via schema introspection or a fixture request) to exclude
  `simulator_tags`, `actually_persisted`, `scripted_failure_id`, checkpoint
  fields, event definitions, and future-event data.
- **Frontend isolation:** `frontend-agent`'s built bundle and rendered DOM
  contain no reference to port `5174`, `/lab`, or the lab token constant
  (`agent_frontend_isolation.spec.ts`).
- **Clock determinism:** advancing Day 0 → Day 18 from the same scenario
  version always produces the same resulting world state.
- **Error sanitization:** an intentionally invalid public request (e.g.
  malformed upload payload) returns a sanitized error with no stack trace,
  ORM repr, or internal field names.

## BW-001 scope discipline (resolved from review)

BW-001 tests long-horizon computer use, cross-source reasoning, current vs.
stale evidence, changing world state, policy retrieval, verification, and
recovery/persistence across time and context resets. The household
preference "Ask before changing household composition" stays in the seed
data for forward compatibility but is **not** exercised by BW-001 — no
household-composition subplot is added to Maya's scenario. An
ask-vs-guess-focused scenario is a candidate for a later, separate
benchmark rather than folded into this one.

## Benchmark agent objective (unchanged, restated for emphasis)

The benchmark agent receives a responsibility, not a checklist:

> Maintain Maya Torres's CalFresh case. Resolve outstanding administrative
> requirements, follow applicable instructions, ask Maya only when facts or
> authorization are genuinely missing, and stop only when the case requires
> no further administrative action.

It is never given an enumerated step list — discovering what needs to
happen is part of what's being measured.

## Top technical risks (revised)

1. **Silent-failure determinism** — unchanged from revision 1: the scripted
   first-attempt-fails-silently mechanic must fire exactly once, keyed off
   `silent_failures.consumed`, and survive reset.
2. **Event-engine ordering/idempotency**, now with six chained events
   including the deadline-miss transition — a predicate that re-fires after
   `applied=1`, or evaluates out of order, breaks exact replay after reset.
3. **Lab-token plumbing discipline** — every new lab-router endpoint added
   in later milestones must remember to depend on `require_lab_token`;
   nothing else keeps `/lab/*` closed. `test_lab_token_isolation.py` needs
   to enumerate routes dynamically (e.g. from the FastAPI app's route table)
   so a forgotten dependency fails the test rather than silently passing.
4. **Playwright flakiness** across milestones' golden-path e2e tests against
   a live FastAPI+SQLite backend.
5. **Policy library sourcing cost** — `DATA_POLICY.md` requires real,
   citable, non-fabricated text; finding enough real, on-topic policy text
   could take longer than the milestone budget assumes.

## Top evaluator/isolation-leakage risks (revised)

1. A shared Pydantic schema reused between a lab response and a public
   response would leak `simulator_tags` or `actually_persisted` straight
   into `/files` or `/portal`.
2. Unsanitized FastAPI error responses (422/500) on the public router
   echoing ORM internals or stack traces — now explicitly covered by
   `test_error_sanitization.py`.
3. `frontend-agent`'s Vite bundle accidentally importing anything from
   `frontend-lab` (a shared component library that leaks the lab API base
   URL or token constant into the agent bundle) — now explicitly covered by
   `agent_frontend_isolation.spec.ts`.
4. Server-side `console.log`/logging left in `frontend-agent` code that
   prints checkpoint state or future-event previews visible in browser
   devtools during a benchmark-agent run.
5. `agent_runner.py` (milestone 6) must enforce the allowed-tool allowlist
   at the tool-definition layer, not rely on the model "choosing" not to
   call other endpoints — there must be no tool capable of an arbitrary
   HTTP request, DB query, or off-origin navigation in the first place.

## Remaining architectural ambiguities

1. **Spec filename mismatch** (see note above): the review draft's
   `DATA_AND_POLICY.md` / `prompts/03_EVENT_ENGINE.md` /
   `prompts/04_SILENT_FAILURE_AND_EVAL.md` do not match any file currently
   in the repository (`DATA_POLICY.md` / `prompts/03_DYNAMIC_EVENTS.md` /
   `prompts/04_FAILURE_AND_EVAL.md` are what exist, re-verified via `ls`).
   This plan keeps referencing the files that actually exist. Confirm
   whether the intent was to rename the real files, or whether the review
   draft's names were simply a slip — no rename has been performed either
   way.
2. **Recertification's terminal state.** `RECERTIFICATION_OVERDUE` vs
   `CLOSED` vs something else — functionally either satisfies "a missed
   deadline changes world state," but the exact value affects milestone-5
   evaluator predicates and should be pinned before that milestone starts.
3. **Lab-token distribution mechanism.** Simplest option: a single static
   value in `.env`, read by `frontend-lab` at build/dev time and by harness
   scripts directly — no rotation, no per-session token. Confirm this
   matches "simplest reliable experimental isolation" or whether even this
   is more than wanted for a local benchmark.
4. **CORS scope for the lab router.** Plan allows both `:5173` and `:5174`
   as CORS origins for the *public* router (so the Lab Console can also
   display public-facing state), while the *lab* router relies on the
   token rather than origin for its access control. Confirm this is the
   intended boundary, versus additionally restricting the lab router's CORS
   to `:5174` only as defense in depth (would not change the agent's
   inability to obtain the token either way, since the token never ships
   in the `frontend-agent` bundle).

## Confirmation

No product code has been written. This revision and its accompanying
`feature_list.json` / `tests.json` are planning artifacts only. Milestone 1
(`01_BUILD_SHELL.md`) has not been started.

## Changes from revision 1

1. Filenames: kept as verified on disk; flagged the review draft's names as
   not matching any actual file (ambiguity 1 above) rather than silently
   renaming or duplicating specs.
2. Frontend split into `frontend-agent` (5173) and `frontend-lab` (5174);
   isolation enforced via origin separation + no shared bundle/links +
   `X-Lab-Token` on every lab-router path, not production auth.
3. Benchmark agent access is browser-only via `agent_runner.py`'s fixed
   tool set; no raw HTTP/DB/filesystem/simulator/evaluator access, enforced
   at the tool layer.
4. Removed any generic `advance_time()` tool from the benchmark agent's
   surface; time advancement is harness-only via `/lab/clock/advance`.
5. Removed server-side `agent_belief` modeling from V1 scope; persistent
   condition's own files stand in until that milestone.
6. Confirmed BW-001 does not exercise the household-composition-change
   preference; removed it as an open ambiguity.
7. Missed recertification deadline is now `EVT-recertification-deadline-missed`,
   a world-state-changing event like the other five, not an evaluator-only
   penalty.
8. Removed `cases.received_document_ids_json`; `uploads` (`actually_persisted = 1`)
   is now the single source of truth for document receipt, with
   `visible_state.py` deriving any "received documents" view from it.
9. `action_log.actor` expanded from `{human, benchmark_agent}` to
   `{benchmark_agent, household, harness, system}`.
10. `test_visible_state_isolation.py` scope made explicit (simulator tags,
    checkpoint status, event definitions, future events, silent-failure
    flags, `actually_persisted`, scripted-failure IDs, terminal-state
    predicates); added `test_lab_token_isolation.py` and
    `test_error_sanitization.py`.
11. Event engine kept intentionally minimal — no new abstraction added
    beyond the sixth event (deadline-missed) reusing the same
    predicate/apply shape.
12. Milestone 1 scope narrowed explicitly to shell-only, with its own
    isolation-test checklist, in the milestone sequence section.
13. Terminology section added up top (benchmark agent / Claude Code /
    household / harness / system / researcher) and used consistently.
14. Benchmark agent objective restated as a responsibility, not a
    checklist, with an explicit note that no step list is ever exposed.
