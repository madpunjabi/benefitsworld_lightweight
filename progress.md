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

## Milestone 2 — BW-001 Day 0 (DONE)

Built:
- **Household files (`data/BW001_starter.json`)**: added D-106, a
  plausible unrelated distractor (a DMV vehicle-registration renewal
  notice) alongside the existing D-101..D-105 evidence documents — six
  documents total, no simulator metadata ever exposed.
- **Policy library** (`data/policy_library.json`, loaded by
  `scenario_loader.py` into a new `policy_items` table): 3 items covering
  exactly the Day-0 topics (responding to a verification request, using
  current/relevant evidence, reporting an employment change). Real fetches
  against the USDA SNAP pages listed in `DATA_POLICY.md` returned 403, and
  the CDSS eligibility-standards URL turned out to be a document index with
  no quotable prose (confirmed by fetching it) — so rather than risk
  misquoting real regulation, all three items are written as clearly
  synthetic county procedural guidance (`authority_level:
  benchmark_synthetic_instruction` in the DB), attributed in-universe to
  "Alameda County Human Services Agency — CalFresh Procedures Guide" with
  no real government URL attached to the synthetic text. `authority_level`
  itself is withheld from the agent-visible `/policy` schema — the literal
  string "benchmark_synthetic_instruction" would tell the benchmark agent
  it's inside a test environment, which is its own kind of leak beyond the
  explicitly-listed simulator fields.
- **`uploads` table** (canonical source of truth for document receipt):
  `POST /portal/uploads {document_id, requirement}` validates the document
  exists, records `ui_reported_success=true, actually_persisted=true` (the
  silent-failure mechanic is Milestone 4), and logs the action. Portal's
  `received_document_ids` is derived at read time from
  `uploads WHERE actually_persisted=1` — no second stored field.
- **Backend-only Day-0 predicates** (`backend/app/evaluator_day0.py`, not
  wired to any route): `current_paystub_received`,
  `termination_letter_received`, `stale_paystub_used_as_only_income_evidence`,
  `day0_income_verification_satisfied`.
- **Real UI** for `/portal` (case summary, notices derived from open
  requirements, per-requirement upload control backed by a document
  picker, received-documents list), `/files` (list + preview master-detail
  file browser), `/policy` (search + detail master-detail viewer with
  source/jurisdiction/effective-date citation). `/inbox`, `/calendar`,
  `/agent` remain Milestone-1 JSON placeholders as instructed. Styled as a
  modest government-portal look (see `frontend-agent/src/index.css`), not
  polished or futuristic.
- **Note on requirement-clearing**: uploads persist and appear as received,
  but `case.open_requirements` is *not* automatically cleared when the
  correct evidence arrives — that state transition is `EVT-income-verified`,
  explicitly Milestone 3's event-engine work per this milestone's "do not
  build dynamic events yet" instruction.

### Tests — all passing

Backend (pytest, 51 tests total, up from 31 — all 31 Milestone-1 tests
still pass unchanged): new files `test_routes_portal.py`,
`test_routes_files.py`, `test_routes_policy.py`, `test_upload_flow.py`,
`test_day0_predicates.py`; `test_scenario_loader.py` and
`test_visible_state_isolation.py` extended for the new tables/fields
(policy corpus count, no `authority_level`/`benchmark`/`distractor`
substrings anywhere in public responses, new `/portal/uploads` and
`/policy/{policy_id}` paths added to the known-path allowlist).

E2E (Playwright, 7 tests total, up from 5): new
`day0_income_golden_path.spec.ts` with two tests — the full human golden
path (portal → files → policy → two uploads → reload → both received) and
a negative test (uploading only the stale paystub does not produce the
current-paystub/termination-letter received state). Both reset the
environment via the lab API in `beforeEach` for isolation between test
runs. 7 new screenshots saved to `e2e/screenshots/` (`day0-01`..`day0-07`).

Verified: `npx tsc --noEmit` clean on frontend-agent; production bundle
re-scanned for lab/benchmark references (still clean) after the new UI
code; no new npm dependencies added (package-lock.json files unchanged);
Python dependencies remain pinned in `backend/requirements.txt`.

### Deviations from the Milestone-2 specification

- `F2.5`/`T2.4` description corrected from the original plan's draft
  ("...persists to uploads and clears the matching requirement...") to
  match what Milestone 2 actually instructed and what was built: uploads
  persist, but requirement-clearing is explicitly Milestone 3's job.
- Real web fetches to the DATA_POLICY.md-listed CDSS/USDA URLs were
  attempted before writing the policy library; USDA blocked the fetch
  (403) and CDSS returned only a document index, so all three policy items
  are `benchmark_synthetic_instruction` rather than verbatim-sourced text
  — matching the "if a synthetic benchmark instruction is needed, label it"
  fallback in `DATA_POLICY.md`.
- `authority_level` is withheld from the public `/policy` schema (not
  explicitly listed among the forbidden simulator fields in the milestone
  spec, but the same isolation principle applies: the literal string
  "benchmark_synthetic_instruction" would itself leak the fact that the
  agent is inside a benchmark).
- The portal's "upload" workflow is "select an existing household document
  and attach it to a requirement" rather than a raw file-bytes upload
  widget, since there are no real binary files in this synthetic
  environment — documents are pre-defined content records, and this is
  also how the eventual benchmark agent (browser-only, no filesystem
  access per Milestone 1's approved constraints) will need to work.
- Files UI adds a derived `type` field (uppercased filename extension) not
  present in the original Milestone-1 `DocumentOut` schema, to satisfy
  "filename / document date / type / preview" from the Milestone-2 spec.
