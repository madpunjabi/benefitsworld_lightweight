# Progress

## Milestone 0 — Plan only

- Revision 1: read all specs, produced `IMPLEMENTATION_PLAN.md`, then stopped
  mid-way (before `feature_list.json`/`tests.json`) on user "stop".
- Revision 2: incorporated architecture review — separate
  `frontend-agent`/`frontend-lab`, browser-only benchmark-agent access,
  harness-controlled simulated time, no server-side agent-belief model in
  V1, single source of truth for document receipt (`uploads`), expanded
  `action_log` actors, deadline-as-world-event, `X-Lab-Token` isolation.
  Produced `IMPLEMENTATION_PLAN.md`, `feature_list.json`, `tests.json`.
- Approved. Remaining ambiguities resolved by user: keep existing spec
  filenames (no rename), `RECERTIFICATION_OVERDUE` as the deadline-missed
  terminal state, lab CORS restricted to `:5174` only, benchmark-agent
  access browser-only, time harness-controlled, no agent-belief model.

## Milestone 1 — Shell + deterministic state (DONE)

Built:
- **Backend** (`backend/`): FastAPI + SQLite. `scenario_loader.py` loads
  `data/BW001_starter.json` into `world_state_meta`/`household`/`cases`/
  `documents`/`calendar_events`. `world_state.py` is the sole read/write
  layer over those tables; `visible_state.py` is the sole projector into
  agent-facing view models (explicit whitelisted dicts, further filtered by
  Pydantic `response_model`s). `reset.py` drops+recreates the schema and
  reloads the seed (deterministic — autoincrement IDs restart at 1).
  `clock.py` advances `current_sim_day` and ticks an (empty, for M1)
  `event_engine.py`. `security.py` provides the `require_lab_token`
  dependency and sanitized exception handlers (422/500/HTTPException all
  return `{"error": "..."}` with no stack trace/ORM/SQL). `cors.py`
  implements path-scoped CORS: `/lab/*` only allows Origin
  `http://localhost:5174`; every other route only allows
  `http://localhost:5173`. Interactive docs (`/docs`, `/redoc`,
  `/openapi.json`) disabled.
- **frontend-agent** (`:5173`): React + Vite + react-router. Six placeholder
  routes (`/portal /inbox /files /calendar /policy /agent`), each fetching
  its public endpoint and rendering the JSON. No import, link, or string
  reference to the lab origin, `/lab`, or any lab token anywhere in the
  package or its production bundle (verified by test).
- **frontend-lab** (`:5174`): separate React + Vite package. `LabConsole`
  shows scenario ID, current simulated day, and case status read from
  `/lab/world_state`, plus a Reset button and an advance-simulated-time
  control, both calling lab-token-gated endpoints.
- **`init.sh`**: one command starts backend (`:8000`) + frontend-agent
  (`:5173`) + frontend-lab (`:5174`), installing dependencies on first run.
- **Git**: repo was already initialized with the reviewed specs/planning
  artifacts committed (`7496803 Initial BenefitsWorld spec`, done outside
  this turn). This turn adds one commit for completed Milestone 1.

### Tests — all passing

Backend (pytest, 31 tests, `backend/tests/`):
`test_scenario_loader.py`, `test_reset_determinism.py`,
`test_clock_determinism.py`, `test_visible_state_isolation.py`,
`test_lab_token_isolation.py`, `test_lab_cors_isolation.py`,
`test_error_sanitization.py`, `test_public_routes_smoke.py`.

E2E (Playwright, 5 tests, `e2e/tests/`):
`agent_frontend_isolation.spec.ts` (scans the built production bundle for
forbidden lab references), `shell_smoke.spec.ts` (visits all six agent
routes + Lab Console, exercises reset/advance-time through the real UI,
confirms a same-origin fetch from the agent page to `/lab/world_state`
either gets blocked by the browser or receives 401, saves 9 screenshots to
`e2e/screenshots/`).

Verified from a cold start (`./init.sh` and a fresh `npx playwright test`
with no servers pre-running) as well as against already-running servers.

### Deviations from the approved plan (see also IMPLEMENTATION_PLAN.md is
### not yet updated with these — noted here for review)

- Dropped wall-clock `created_at` timestamps from `world_state_meta` and
  `action_log` (not in the M1 schema at all) to keep reset/clock
  determinism tests exact-equality comparisons simple, since this is a
  simulated environment where `current_sim_day` is the meaningful clock.
- M1's schema only includes the six tables M1 actually exercises
  (`world_state_meta`, `household`, `cases`, `documents`,
  `calendar_events`, `action_log`); `uploads`, `silent_failures`,
  `inbox_messages`, `policy_items`, `interview_slots`, `events`,
  `evaluator_checkpoints` are deferred to the milestones that use them,
  per the instruction not to build upload/event/policy/evaluator logic yet.
- Disabled FastAPI's interactive docs (`/docs`, `/redoc`, `/openapi.json`)
  as defense-in-depth against a route-table/schema fingerprinting surface
  on the backend port, and to keep the "only intended public paths exist"
  isolation test exact.
- Added two isolation tests beyond the required 8 test types:
  `test_lab_cors_isolation.py` (splits CORS behavior out from token
  behavior explicitly — preflight + response-header assertions per origin)
  and `test_public_routes_smoke.py` (200-status coverage for all six
  public endpoints).

## Milestone 2 — not started
