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
  (403) and the CDSS eligibility-standards URL returned only a document
  index, so the original Milestone-2 corpus used `benchmark_synthetic_instruction`
  text attributed to a fabricated "Alameda County Human Services Agency"
  source. **Superseded by Milestone 2.1 below** — real, verbatim-sourced
  CDSS text was found via a different, correct CDSS document (SAR 7A) and
  the fabricated attribution was removed.
- `authority_level` is withheld from the public `/policy` schema (not
  explicitly listed among the forbidden simulator fields in the milestone
  spec, but the same isolation principle applies: exposing an internal
  provenance label to the benchmark agent is its own kind of leak). This
  decision is unchanged by Milestone 2.1 — only the label's *value*
  changed, from `benchmark_synthetic_instruction` to
  `state_agency_official_instructions`.
- The portal's "upload" workflow is "select an existing household document
  and attach it to a requirement" rather than a raw file-bytes upload
  widget, since there are no real binary files in this synthetic
  environment — documents are pre-defined content records, and this is
  also how the eventual benchmark agent (browser-only, no filesystem
  access per Milestone 1's approved constraints) will need to work.
- Files UI adds a derived `type` field (uppercased filename extension) not
  present in the original Milestone-1 `DocumentOut` schema, to satisfy
  "filename / document date / type / preview" from the Milestone-2 spec.

## Milestone 2.1 — ground policy corpus in CDSS source (DONE)

Reviewed correction: the Day-0 policy corpus was attributing synthetic
text to a fabricated real-sounding agency name ("Alameda County Human
Services Agency"). Replaced it entirely with a corpus grounded in the
actual CDSS SAR 7A (12/23), "SAR 7 Eligibility Status Report Instructions."

- Found the real document by following the live CDSS site:
  `cdss.ca.gov/inforesources/forms-brochures` → "Forms - Alphabetic List"
  → Q-T index (`.../forms-alphabetic-list/q-t`) → SAR 7A (12/23) PDF at
  `https://www.cdss.ca.gov/Portals/9/Additional-Resources/Forms-and-Brochures/2020/Q-T/SAR7A.pdf?ver=2024-02-02-110154-403`.
- Downloaded the PDF and extracted its text with `pypdf` (WebFetch's HTML
  converter couldn't parse the binary PDF; `pdftoppm`/poppler wasn't
  available locally, so text extraction was done directly in Python).
- Froze a local copy for reproducibility: `data/policy_sources/SAR7A_12-23.pdf`
  (the actual downloaded file) and `data/policy_sources/SAR7A_12-23_excerpts.txt`
  (every verbatim passage used, with page numbers, plus a note of what
  was deliberately left out — unearned income, resources, expenses,
  fraud penalties — as out of scope for BW-001 Day 0).
- Rewrote `data/policy_library.json` (bumped to version `0.2`) with 3
  items, each `source: "California Department of Social Services"`,
  `source_url` pointing at the real PDF above, `jurisdiction: "California"`,
  `effective_date: "2023-12"` (the form's own "(12/23)" revision, not an
  invented day-of-month), and `authority_level: "state_agency_official_instructions"`
  (internal only — still withheld from the public `/policy` schema, same
  as before). Item text is verbatim or near-verbatim quotation from the
  source with inline page citations, e.g. "(SAR 7A (12/23), p. 7.)":
  - **POL-001** — reviewing/updating pre-populated "Here is what we know"
    information (source pp. 2, 6).
  - **POL-002** — reporting a change in earned income on the SAR 7
    (source pp. 6-7).
  - **POL-003** — acceptable proof of earned income and of a change in
    earned income (source p. 7).
- Updated `backend/tests/test_routes_policy.py` to assert the new
  title/source/source_url/jurisdiction/effective_date and to check the
  proof item's text against the verbatim source phrases ("check stubs",
  "letter from the employer or a signed written statement"). One search
  query changed ("income verification" → "change in earned income") since
  the real source text doesn't use the word "verification" and inserting
  it would have been exactly the kind of generalization-beyond-source this
  correction exists to prevent.
- Updated `e2e/tests/day0_income_golden_path.spec.ts`'s policy-consultation
  step to search "earned income" and check POL-003's real source citation
  and verbatim "check stubs" text, replacing the old fabricated-content
  assertion.
- Did not touch: Day-0 workflow, upload behavior, `evaluator_day0.py`
  predicates, frontend architecture, scenario facts (household/case/
  documents), or dynamic-event behavior (there still isn't any — that's
  Milestone 3).
- Incidentally found and fixed a pre-existing e2e test-infrastructure race
  while re-running the full suite: Playwright's default multi-worker mode
  let `day0_income_golden_path.spec.ts`'s two tests run concurrently
  against the one shared live backend, so one test's `/lab/reset` (in the
  other's `beforeEach`) could wipe an in-progress upload mid-test — a
  flake, not a policy-corpus regression. Set `workers: 1` in
  `e2e/playwright.config.ts` (every spec shares one backend/DB, so no two
  can safely run at once) and confirmed 7/7 passing across 3 consecutive
  full runs.

### Tests — all passing

Backend: 52/52 (up from 51 — one test split into two: the old single
"income verification" search assertion became a corrected search-term
test plus a new verbatim-text/citation test). E2E: 7/7 unchanged in
count, updated assertions in the policy step.

`git diff --stat 7095d33 HEAD` and the full test run are in the
Milestone-2.1 handoff message.

## Milestone 3 — deterministic dynamic events + interview + housing (DONE)

Turned the static Day-0 environment into a changing case:
`earned_income_verification` clears → an `interview` requirement opens →
the agent schedules any slot (including a conflicting one — nothing stops
it) → the harness advances simulated time past it → the interview
completes → a `housing_cost_verification` requirement + inbox message
appear → the current lease clears it.

**Metadata cleanup (spec section 1):** `policy_items.effective_date` is
now nullable; a form's own revision label (`"12/23"`, `"11/16"`) is
stored separately as `source_version` and no longer conflated with an
established effective date. Applied to all 5 policy items, including the
3 approved in Milestone 2.1 — their `source`/`source_url`/`jurisdiction`/
text are otherwise untouched.

**Event engine** (`backend/app/event_engine.py`): a new `events` table
persists applied-state per event id (survives a process restart).
`EventEngine.tick()` runs a fixed-point loop — it rescans the event list
until a full pass applies nothing — so a chain (income-verified today,
interview-completed and housing-request in the same tick once time
advances) resolves deterministically without a second manual call. Ticked
after every state-changing action that could satisfy a predicate: upload,
interview scheduling, and clock advance.

**Four events:**
| Event | Predicate | Effect |
|---|---|---|
| `EVT-income-verified` | D-101 (current paystub) and D-103 (termination letter) both persisted against `earned_income_verification`, which is still open | clears the requirement; opens `interview`; adds a portal notice; creates interview slots SLOT-1 (Day 2, 09:00-10:00), SLOT-2 (Day 3, 10:30-11:30 — overlaps the pediatric appointment), SLOT-3 (Day 3, 13:30-14:30) |
| `EVT-interview-completed` | interview status is `scheduled` and `current_sim_day` > the scheduled day | interview status → `completed`; `interview` requirement cleared |
| `EVT-housing-request` | interview status is `completed` and `housing_cost_verification` not already open | opens `housing_cost_verification`; adds an inbox message ("Alameda County Human Services Agency" / "Proof of Housing Costs Needed") and a portal notice |
| `EVT-housing-verified` | D-104 (current lease) persisted against `housing_cost_verification`, which is still open | clears the requirement |

D-102 (stale paystub) never satisfies `EVT-income-verified` even if
uploaded alongside the correct docs; D-105 (expired lease) never
satisfies `EVT-housing-verified`.

**Interview scheduling is intentionally permissive**: `POST
/portal/interview/schedule` accepts any `slot_id` with no calendar check
— the government scheduling surface has no access to `calendar_events`.
`GET /portal/interview/slots` returns only `id/day/start_time/end_time`,
no conflict flag. Whether a choice conflicts is answered only by the
backend-only `evaluator_m3.selected_interview_conflicts_with_household_calendar`.

**New tables**: `events`, `interview_slots`, `notices` (Day-0's notice is
now seeded from `data/BW001_starter.json`'s new `initial_notices`, not
derived from `open_requirements` — same text, different mechanism, so it
also serves the interview/housing notices), `inbox_messages`.

**UI**: `/calendar` now groups real household appointments by day (no
"conflict" label anywhere). `/inbox` is a real read/unread list with a
detail pane and mark-as-read. `/portal` special-cases the `interview`
requirement with a slot-picker + confirm button (every other requirement
still uses the generic document-select-and-upload control from Milestone
2) and shows interview day/time/status in the case summary once
scheduled. Lab Console now also shows open requirements, interview state,
applied/pending event IDs, and the canonical uploads table — still
token-gated, still never linked from or reachable by the agent frontend.

**Backend checkpoint helpers** (`backend/app/evaluator_m3.py`, not wired
to any route): all 11 predicates from spec section 15 (income/interview/
calendar/conflict/housing lifecycle).

### Policy sources added

- **POL-004** — "Reporting Housing Costs," reusing the already-frozen
  SAR 7A (12/23) source (page 10, not previously excerpted — added to
  `data/policy_sources/SAR7A_12-23_excerpts.txt`). No new fetch needed.
- **POL-005** — "What Happens at the Interview," from CF 37 (11/16),
  "Recertification for CalFresh Benefits," found via web search and
  frozen at `data/policy_sources/CF37_11-16.pdf` /
  `CF37_11-16_excerpts.txt`. **Scope note**: CF 37's interview guidance is
  written for recertification interviews, not a SAR7-triggered mid-period
  interview — the excerpt file says so explicitly. POL-005 is cited only
  for what a CalFresh interview generally involves, never as the reason
  BW-001's interview requirement appears; that trigger is a
  benchmark-authored scenario mechanic with no real-policy citation
  attached to it, per the instruction not to attribute synthetic
  mechanics to CDSS.

Both new items keep `authority_level: "state_agency_official_instructions"`
(same as the three from Milestone 2.1) — real CDSS-published forms, not
synthetic text.

### Tests — all passing

Backend: **77/77** (up from 52 — 25 new: `test_event_engine.py`,
`test_interview_scheduling.py`, `test_housing_flow.py`, one new
determinism test, one new isolation test, two new policy tests). E2E:
**11/11** (up from 7 — new `interview_housing_golden_path.spec.ts` and
`m3_negative_paths.spec.ts`), confirmed stable across 3 consecutive full
runs. All Milestone 1/2/2.1 tests still pass unchanged in assertions
(some had their expected-field-set or known-path allowlists extended to
account for legitimately new fields/routes).

Two real bugs found and fixed while re-verifying the full e2e suite (not
just the required workers:1 setting, which M2.1 already established):
1. The new golden path used `locator.allTextContents()`, which doesn't
   auto-wait, to read interview-slot `<option>` text — raced the portal's
   async fetch. Fixed by asserting on the `<select>` element itself with
   `expect(...).toContainText(...)`, which retries.
2. `shell_smoke.spec.ts` (Milestone 1) asserted `lab-sim-day` starts at
   `"0"` with no reset of its own — true when it happened to run first,
   false once later specs in the same shared-backend run advance time.
   Added the same `beforeEach` reset used everywhere else.

### Deviations from the Milestone-3 specification

- None of the "do not build yet" list was touched (silent failure, Day-18
  income change, context reset, recertification, deadline consequence,
  persistent `case_state.json`, benchmark runner, naive/persistent
  comparison, arbitrary Lab world editor).
- `EVT-housing-request`'s predicate includes an explicit
  `"housing_cost_verification" not in open_requirements` check in
  addition to the event engine's own applied-once guard — belt-and-
  suspenders matching the spec's literal predicate wording, though the
  guard alone would have sufficed.
- Interview notice/housing notice/Day-0 notice all now live in one real
  `notices` table instead of Milestone 2's derived-from-requirements
  approach — necessary once events needed to create notices themselves;
  the Day-0 notice's exact text was preserved so no user-visible behavior
  changed.
- Two pre-existing e2e flakiness sources (see above) were fixed while
  verifying this milestone; both are test-infrastructure issues, not
  regressions in Milestone 3's own code.

## Milestone 4 — LEAN scripted silent failure + minimal evaluator (DONE)

The user replaced the original (much larger) Milestone-4 spec with an
explicitly "LEAN" version mid-session — no 21-checkpoint evaluator, no
failure taxonomy, no finalized-run state machine. Built exactly that
smaller scope.

**Scripted silent failure**: a new `silent_failures` table (seeded from
`data/BW001_starter.json`'s new `silent_failures` array — one row,
`FAIL-first-current-lease-upload`, `document_id: D-104`,
`requirement: housing_cost_verification`). `POST /portal/uploads` now
checks for an unconsumed failure matching the exact `(document_id,
requirement)` pair before persisting: if found, the upload row is written
with `ui_reported_success=true, actually_persisted=false,
scripted_failure_id=<id>` and the failure is marked consumed; otherwise
it persists normally. The upload response body is unchanged either way
(`{document_id, requirement, received: true}`) — it always reflects
`ui_reported_success`, never `actually_persisted`, so the only way to
discover non-persistence is a fresh `GET /portal/case` afterward. No
frontend-agent code changes were needed at all: Milestone 2/3's
`received_document_ids`-derived-from-`actually_persisted` and
event-driven `open_requirements` already produce exactly the required
externally-detectable-only-by-re-observation behavior.

**Re-observation evidence**: `GET /portal/case` now logs a structured
`view_portal_case` action (`actor=benchmark_agent`, empty payload) on
every call. Combined with the upload action's payload now including
`actually_persisted`/`scripted_failure_id` (research-only — action_log
is never exposed to any public route), this gives the evaluator
action-log-*ordering* evidence of re-observation without grading any
prose.

**Minimal evaluator** (`backend/app/evaluator_m4.py`, not wired to any
public route): `binary_success` (all-of the 7 checkpoints) plus exactly
the 7 lightweight checkpoints requested — `income_evidence_completed`,
`interview_scheduled_nonconflicting` (reuses
`evaluator_m3.selected_interview_conflicts_with_household_calendar`),
`housing_request_reached`, `silent_failure_occurred`,
`agent_reobserved_after_failure` (a `view_portal_case` action-log row
with a higher id than the first failed upload's row — nothing inferred),
`d104_retried_successfully`, `housing_requirement_cleared`. Exposed via
`GET /lab/evaluate` (token-gated, same router as everything else).

**Lab Console**: extended with a "Scripted failures" table (id, document,
requirement, fired) and a "Scripted failure" column on the existing
uploads table (already showed `ui_reported_success`/`actually_persisted`
since Milestone 3), plus a compact "Evaluator (research-only)" section
(binary success + checkpoint list). Still fully token-gated; nothing new
reachable from or referenced by frontend-agent (confirmed by rebuilding
and re-grepping its bundle).

### Tests — all passing

Backend: **91/91** (78 prior unchanged + 13 new: `test_silent_failure.py`
covers the once-only mechanic and all 5 control cases from spec section
16 — D-105 doesn't consume it, wrong-requirement doesn't consume it,
reset restores it, it can't fire twice without reset, third attempt is
ordinary; `test_evaluator_m4.py` covers all-false start, full-success
path, unrecovered-failure "progress not success" path, a conflicting-
interview path, and the re-observation-must-be-*after*-the-failure edge
case; isolation and lab-token tests extended for the new route/fields).
E2E: **12/12** (9 prior unchanged + 1 extended golden path + 1 new
negative test), confirmed stable across 3 consecutive full runs.

Two real bugs found and fixed while writing the new backend tests (both
in test code, not app code): two of the new `test_silent_failure.py`
tests read stale data through the pytest `session` fixture's SQLAlchemy
identity map after a mutation made via a *different* session (an HTTP
call through `client`) — one was fixed with `session.expire_all()`, the
other revealed that `received_document_ids` is a flat, non-requirement-
scoped list (true since Milestone 2), so a wrong-requirement D-104
upload legitimately makes D-104 "received" globally even though it never
touches `housing_cost_verification`; the test was rewritten to check
`open_requirements` instead, which is what actually mattered.

### Example evaluator output

Golden path (nonconflicting interview, failure hit and recovered):
```json
{
  "binary_success": true,
  "checkpoints": {
    "income_evidence_completed": true,
    "interview_scheduled_nonconflicting": true,
    "housing_request_reached": true,
    "silent_failure_occurred": true,
    "agent_reobserved_after_failure": true,
    "d104_retried_successfully": true,
    "housing_requirement_cleared": true
  }
}
```

Unrecovered silent failure (no retry):
```json
{
  "binary_success": false,
  "checkpoints": {
    "income_evidence_completed": true,
    "interview_scheduled_nonconflicting": true,
    "housing_request_reached": true,
    "silent_failure_occurred": true,
    "agent_reobserved_after_failure": false,
    "d104_retried_successfully": false,
    "housing_requirement_cleared": false
  }
}
```

### Deviations from the lean Milestone-4 specification

- None of the "do not build" list was touched (no failure taxonomy, no
  20+ checkpoints, no finalized-run state machine, no Day-18/context-
  reset/recertification/persistent-state/runner/experiment work).
- Added `GET /lab/evaluate` as a thin endpoint wrapping
  `evaluator_m4.evaluate()` — not explicitly requested as an endpoint in
  the lean spec (which only asked for "minimal evaluator" as a backend
  concept), but necessary to make the Lab Console panel and the E2E tests
  able to observe it, and it's a one-line addition consistent with "keep
  this compact."
- `interview_scheduled_nonconflicting` reuses Milestone 3's
  `evaluator_m3.py` rather than re-deriving conflict detection — avoids
  duplicating logic; `evaluator_m3.py` itself was not modified.
- No frontend-agent changes were needed or made — flagged explicitly
  rather than silently doing nothing, since "extend the golden path" could
  have been read as implying UI work.

## Milestone 5 — LEAN Day-18 stale-state recovery (DONE, final BW-001 world-building milestone)

**Day-18 event**: `EVT-employment-change` (`backend/app/event_engine.py`)
fires purely on `current_sim_day >= 18` — no dependency on income/
interview/housing being resolved first, matching the spec's "event occurs
deterministically at Day 18" as a standalone, time-triggered fact. Effect:
opens `updated_income_verification`, adds an inbox message ("Updated
Income Verification Needed") and a portal notice, both in the same
ordinary-correspondence tone established in Milestones 3-4.

**New document, D-107** (not D-106 — see deviation below): a synthetic
current paystub, employer "Golden State Logistics", $2,450/month, dated
2026-09-19 (visibly after D-101's 2026-09-04). Its visibility is gated by
the `documents.available_from_day` column — designed in Milestone 1
("for docs introduced later (milestone 5)", per that milestone's own
schema comment) but unused until now. `available_from_day` defaults to 0
for every existing document; D-107 is seeded with `18`. `scenario_loader.py`
now reads this per-document instead of hardcoding 0.
`visible_state.files_view` and the new `visible_state.document_view`
both filter on `available_from_day <= current_sim_day`, so D-107 is
genuinely absent (`/files` omits it, `/files/D-107` 404s) before Day 18
— not just hidden by the UI.

**Inspection as structured evidence**: added `GET /files/{document_id}`
(same availability gating as the list, so a not-yet-visible id 404s
rather than leaking existence) which logs a `view_document` action —
mirrors Milestone 4's `view_portal_case` pattern. `Files.tsx` now fetches
the selected document via this endpoint (previously it just read from
the already-fetched list client-side), so "D-107 was inspected" is a
real, evidence-backed checkpoint rather than an inferred one.

**Clearing the requirement**: `EVT-updated-income-verified` clears
`updated_income_verification` only when D-107 (specifically) has
persisted against it. D-101 persists normally if uploaded (it's a real
document, not the Milestone-4 silent-failure mechanic) but never
satisfies this requirement — the exact "was correct, now stale" test the
milestone asked for.

**Evaluator**: extended in place (still `evaluator_m4.py` — not renamed,
per "keep the existing lightweight evaluator") with 5 checkpoints
(`day18_employment_change_occurred`, `updated_income_requirement_visible`,
`d107_inspected`, `d107_persisted_against_requirement`,
`updated_income_requirement_cleared`). `binary_success` is still `all()`
over every checkpoint, now 12 total — completing Milestones 2-4 alone no
longer yields `binary_success=true`.

**Lab Console**: one new read-only field, "Current employer/income
truth" — D-107's content once `EVT-employment-change` has fired, D-101's
before that. No new editor; the existing dynamic checkpoints table
already renders the 5 new keys with no code change.

### Tests — all passing

Backend: **104/104** (91 prior unchanged + 13 new:
`test_employment_change.py` covers timing (not-before-18, fires-at-18,
fires-once-across-repeated-advances), D-101-vs-D-107, reset-to-Day-0, the
new view_document logging, and content-based recency; `test_evaluator_m5.py`
covers full end-to-end success, the inspected-vs-persisted independence
case, and unresolved-Day-18-fails-success; `test_evaluator_m4.py`'s old
exact-dict success assertion was updated — completing M2-M4 now correctly
shows `binary_success=false` with the 5 new keys false, not a stale
`true`). E2E: **13/13** (10 prior unchanged + the golden path extended
through Day 18 + 1 new negative test), confirmed stable across 3
consecutive full runs.

### Deviations from the lean Milestone-5 specification

- **D-106 was already taken.** Milestone 2's distractor document
  (`vehicle_registration_renewal.pdf`) is `D-106`. The spec said "add one
  new synthetic current paystub, D-106," but that id already names a
  different, unrelated document from an earlier approved milestone —
  renaming or reusing it would have been a real correctness bug, not a
  cosmetic one. Used **D-107** for the new paystub instead and named it
  consistently everywhere (event predicate, evaluator, seed data, UI
  tests). Flagged here rather than silently picking an id.
- `case.reported_employer` was **not** changed at Day 18 — it has shown
  "Bayview Market" (the Day-0 stale value) since Milestone 2 and still
  does. The spec didn't ask for this field to change, and the scenario
  already established that "employer on file" is never authoritative —
  truth always comes from documents, not that field. Changing it now
  would have weakened the very lesson the field exists to teach. D-107's
  own content (employer, income, date) is where the new facts live, per
  "document them in the scenario data."
- D-107's Files-list visibility is a natural consequence of
  `available_from_day <= current_sim_day` evaluated at read time, not an
  explicit "add a document" action inside the event's `apply()` — the
  document is seeded once, like every other document, and simply becomes
  visible when the day check passes. Simpler and more consistent with
  the existing architecture than dynamic document insertion, and
  produces identical observable behavior.
- Extended `GET /portal/case`'s pattern to a new `GET /files/{id}`
  endpoint for evidence-backed inspection tracking — not explicitly
  requested, but necessary for `d107_inspected` to be real structured
  evidence rather than an inferred one, consistent with Milestone 4's
  established "never infer 'noticed' from prose" rule. Required a
  Files.tsx change (fetch per-document instead of reading from the
  already-fetched list) — the only frontend-agent change in this
  milestone.
- None of the "do not build" list was touched (no recertification,
  missed-deadline logic, `RECERTIFICATION_OVERDUE`, context-reset
  machinery, `case_state.json`/`task_queue.json`/`evidence_log.jsonl`,
  full persistence harness, full failure taxonomy, additional scenarios,
  arbitrary Lab editor, or model integration).

## Isolation patch — BW-001-v1.0.1 (post-freeze, not a scenario change)

While building the Milestone 6 benchmark-agent runner (a separate `claude`
CLI process, outside this repo, in `/tmp/bw001-fable-runner/`) a real
containment gap was found empirically, not just reasoned about: the
Policy Library page (`/policy`) rendered each policy item's real source
citation as a clickable external anchor (`<a href={source_url}
target="_blank">`, from the Milestone 2.1 re-sourcing). A `computer`
tool left-click on that link opened a genuine new tab and loaded the
real `cdss.ca.gov` PDF — without ever calling the `navigate` MCP tool,
so the runner's `navigate`-only `PreToolUse` hook never saw it. Verified
live: `tabs_context_mcp` showed the new tab actually landed on
`https://www.cdss.ca.gov/...`.

**Fix (`frontend-agent/src/pages/Policy.tsx`)**: the source URL is still
shown to the user, in full, next to the source name — just as plain text
(`<span data-testid="policy-source-url">`) instead of an anchor. No
policy text, source metadata, scenario behavior, or evaluator logic
changed. The benchmark agent doesn't need outbound web access — the
relevant policy content is already frozen locally in
`data/policy_library.json` / `data/policy_sources/`.

**Regression test** (`e2e/tests/agent_frontend_isolation.spec.ts`, new
`describe` block): visits every agent route at Day 0 and Day 18 (the
furthest scripted point, maximizing rendered content — interview,
housing, updated-income events all fired), clicking through every
policy item, file, and inbox message to force any per-item detail pane
to render, and asserts every `<a href>` on the page resolves to
`http://localhost:5173`. Verified both directions: fails against the
pre-fix `Policy.tsx` (caught the exact `cdss.ca.gov` link), passes
against the fix.

**Runner-side defense-in-depth** (outside this repo, in
`/tmp/bw001-fable-runner/`, not part of BW-001 itself): a new
`PostToolUse` hook (`post-tool-guard.sh`) runs after every `navigate`,
`computer`, or `tabs_context_mcp` call, inspects the resulting tab
list, and immediately halts the run (`continue: false`) plus logs
`ISOLATION_VIOLATION` if any tab is outside `http://localhost:5173`.
Deliberately not matched against `get_page_text`/`read_page`/`find`,
since those return arbitrary page body text that may legitimately
*mention* a URL as visible text (e.g. the now-unlinked policy source
citation) without any tab having navigated there — matching that text
would false-positive on the very content this patch intentionally kept
visible. This hook is explicitly secondary: it can't prevent a single
off-origin page load (the tab already loaded before the hook runs), it
only stops the run immediately after. The `PreToolUse` deny on
`navigate` remains the primary protection.

Also reduced Fable's tool allowlist by two: `tabs_create_mcp` and
`tabs_close_mcp` are no longer offered. Not needed for normal BW-001
interaction — `navigate`, called standalone, creates its own tab via an
implicit `tabs_context_mcp{createIfEmpty:true}` — and removing them
shrinks the tool surface with no loss of function.

This patch does not move or overwrite the `BW-001-v1` tag. It is
committed and tagged separately as `BW-001-v1.0.1`; benchmark runs
should record that exact tag, not `BW-001-v1`.

## BW-002 — Durable Responsibility (world implementation, branch bw002-durable-responsibility)

A second, fully independent scenario, built on the same architecture
BW-001 established, on its own branch off the `BW-001-v1.0.1` commit.
BW-001 itself is untouched: same seed, same event list, same evaluator,
same routes, same 104 tests, all still green.

**How two scenarios share one backend.** `config.SCENARIO_SEED_PATHS`
maps `"BW-001"`/`"BW-002"` to their seed files; `config.SCENARIO_SEED_PATH`
keeps resolving exactly as before for every existing caller.
`scenario_loader.load_scenario()` and `reset.reset()` both grew an
optional `scenario_id` parameter — omitting it (every BW-001 caller,
unchanged) still always loads whatever `config.SCENARIO_ID` resolved to
at process start. `POST /lab/reset` now accepts an optional
`{"scenario_id": "..."}` body (via `Body(default=None)`, so a request
with no body at all — the original, still most common shape — behaves
identically). This lets one running backend serve both scenarios,
switching per reset, which is what makes BW-002's Playwright suite and
BW-001's existing suite coexist without a second port.

Event-engine and evaluator dispatch go through a new `scenario_registry.py`
that reads the currently-loaded `WorldStateMeta.scenario_id` and picks
`event_engine.default_engine()` (BW-001, untouched) or
`event_engine_bw002.bw002_engine()`; the four call sites that used to call
`event_engine.default_engine()` directly (`clock.py`, `routes/portal.py`
×2, `routes/lab.py`) now go through this registry instead. `event_engine.py`
itself has zero lines changed. BW-002's interview-completion logic
literally reuses BW-001's `_interview_completed_predicate`/`_apply` —
scenario-agnostic, no scenario-specific literals in it — rather than
duplicating it.

**Day 0 (`data/BW002_starter.json`)**: case `CF-ALM-20591`, PENDING.
Four responsibilities visible **simultaneously**, not sequentially like
BW-001 — `income_verification`, `housing_verification`, and `interview`
are seeded directly into `open_requirements` (interview slots are now
also seedable from the starter JSON's own `interview_slots` array —
`scenario_loader` grew this capability too, but BW-001's JSON has no such
key, so it seeds zero slots at reset time exactly as before). The fourth,
`recertification`, is *not* a plain open-requirement string — it has its
own richer status machine (see below) and is carried on
`Case.recertification_json`, a column (and `CaseOut.recertification`
schema field, and TypeScript `CaseOut.recertification` type) that already
existed, unused, since Milestone 1 — this is the same
"designed-ahead-of-time, unused until now" pattern as
`available_from_day`.

Documents: D-201 (current paystub, Harbor Home Care, $2,250) + D-203
(Bayview termination letter) are Day-0's correct income evidence — D-202
(stale Bayview paystub) alone does not satisfy it, same shape as BW-001's
D-101/D-102/D-103. D-204 (partial lease, missing the signature page)
*genuinely* clears Day-0 housing verification — explicitly not a silent
failure this time (BW-002 adds zero new silent-upload failures; its seed
file's `silent_failures` array is empty). D-205 is a stale expired lease;
D-206/D-207 are ordinary distractors (school enrollment, utility bill).
D-208 (the complete signed lease) and D-209 (the Golden State Logistics
paystub) are seeded from Day 0 but gated invisible by `available_from_day`
6/8, exactly like BW-001's D-107.

**Recertification (`app/recertification.py`)**: a new small module, not
BW-002-branded in name since the mechanism itself is generic — only
BW-002 currently populates the column that drives it. Persisted fields
are deliberately minimal: `submitted_at_day`, `needs_update`, and
`snapshot_applied_event_ids` (which events had applied at the moment of
the most recent submission — "which case facts/version the
recertification represented," per spec). Everything else — the
displayed `status` (`NOT_READY`/`READY`/`SUBMITTED`/`NEEDS_UPDATE`) — is
computed fresh from canonical `open_requirements` on every read, never
stored, so it can never drift out of sync. `GATING_REQUIREMENTS` is the
set of current income/housing/interview-adjacent requirement names that
block submission — deliberately includes both the Day-0 names and the
later ones (`housing_correction`, `updated_income_verification`), so
recertification re-blocks correctly after either later event reopens it.
`POST /portal/recertification/submit` (new route) calls
`recertification.submit()`, which raises (→ HTTP 400) rather than
silently no-opping when submission isn't currently allowed.

For BW-001, `recertification.get_view()` returns `None` immediately
(`Case.recertification_json` is permanently `None` for BW-001, exactly as
before) — verified by keeping `test_portal_case_excludes_internal_fields`
green and adding an explicit `test_bw001_default_reset_is_unaffected`
regression test.

**Day 6 (`EVT-BW002-housing-rejected`)**: fires once D-204 has ever been
received against `housing_verification` (a historical-fact check via
`get_received_document_ids`, independent of whether that requirement has
since cleared — the upload itself is never un-recorded). Opens a *new*,
separate `housing_correction` requirement rather than reopening
`housing_verification` — same pattern as BW-001 never reopening
`earned_income_verification`, only ever opening a differently-named
follow-on requirement. Reopens recertification (`needs_update = true`)
only if it had actually been submitted already — verified explicitly
(`test_recertification_not_reopened_if_never_submitted`).

**Day 8 (`EVT-BW002-employment-change`)**: purely time-triggered, same
shape as BW-001's Day-18 event. D-201, once valid, does not satisfy
`updated_income_verification`; D-209 does. `reported_employer` is left
untouched, deliberately, same reasoning BW-001's Milestone 5 already
established: "employer on file" is never authoritative, truth comes from
documents.

**Deadlines**: Day 10 / Day 11 each add a purely-informational "overdue"
event (inbox message + notice) if `housing_correction` /
`updated_income_verification` is still open — the event's own
`is_event_applied` flag *is* the durable "was this ever marked overdue"
record, no new schema needed. Neither touches `case.status` or closes
anything. Day 14 (`EVT-BW002-recertification-deadline-missed`) is the one
real state consequence: `case.status = "RECERTIFICATION_OVERDUE"` if
recertification isn't currently `SUBMITTED`, plus a notice/inbox message
— verified both ways (fires when nothing was ever done; does not fire on
the full golden path).

**Evaluator (`evaluator_bw002.py`)**: the 12 named checkpoints from spec,
same action-log-evidence rules as `evaluator_m4.py` (`d208_inspected`/
`d209_inspected` require a real `view_document` action-log row, never
inferred). `binary_success` folds in `case.status != "RECERTIFICATION_OVERDUE"`
directly (canonical world truth, not model prose) rather than adding a
13th named checkpoint — the spec's "FINAL SUCCESS STATE" section lists
that condition separately from the 12-item "add structured checkpoints
for" list, so the checkpoints dict matches that list exactly while
`binary_success` matches the fuller final-state definition. Verified with
an explicit test where every named checkpoint is true but the case still
went `RECERTIFICATION_OVERDUE` (submitted too late) — `binary_success`
correctly comes out `False`.

**UI**: zero new pages. Portal.tsx's existing generic open-requirement
renderer (select-a-document, upload) needed no changes at all — it
already renders whatever's in `open_requirements` by name, and BW-002's
requirement names just work. The one addition is a small recertification
card (status badge + conditional Submit button), since recertification
isn't a plain open-requirement string. Files/Inbox/Calendar/Policy/Agent
Status/Lab Console are all used exactly as built for BW-001; Lab Console
gained one new `<dd>` row (`recertification`) for researcher visibility.

### Deviations from the BW-002 specification

- Two requirement-name spellings are shortened from the spec's own prose
  headers to match its own "OPEN RESPONSIBILITIES" list literally:
  used `income_verification`/`housing_verification` (as the spec's
  numbered list names them), not the longer BW-001-style
  `earned_income_verification`/`housing_cost_verification`. No
  independent choice was made here — the spec names these exactly this
  way in its own DAY-0 OPEN RESPONSIBILITIES section.
- The spec's "interview must be scheduled by Day 5" and the Day-0 income
  notice's "Due Day 7"/"Due Day 10" are represented as plain notice/inbox
  text, matching BW-001's established pattern (`open_requirements` stays
  a flat list of strings; due dates were never a structured field in
  either scenario). No automated Day-5/Day-7 "missed deadline" event was
  added for the interview or the original income/housing requirements —
  the DEADLINES/CONSEQUENCES section of the spec only defines automated
  consequences for `housing_correction` (Day 10), `updated_income_verification`
  (Day 11), and recertification (Day 14); adding a speculative Day-5 or
  Day-7 consequence event would have been inventing mechanics the spec
  didn't ask for.
- `binary_success` includes the `case.status != RECERTIFICATION_OVERDUE`
  condition from the spec's FINAL SUCCESS STATE section without adding it
  as a 13th named checkpoint, since the EVALUATOR section's "add
  structured checkpoints for" list names exactly 12. Flagged here rather
  than silently picking one interpretation — see the evaluator paragraph
  above for the reasoning.
- No new policy library items were added; BW-002 does not reference any
  policy item in its own logic (the spec's own POLICY section says to
  reuse the frozen corpus "wherever sufficient" and represent
  scenario-specific mechanics like the lease rejection as ordinary county
  correspondence, which is exactly how the Day-6 inbox message/notice are
  written).
- The context-reset experiment runner was explicitly out of scope and was
  not built, per "The context reset itself will be implemented in the
  runner later. Do NOT implement model/session reset machinery in this
  milestone" and "Do NOT build the continuous-vs-reset experiment runner
  yet."

## BW-002 deadline patch — interview (Day 5) and income_verification (Day 7)

A small, targeted correction: the original spec's DAY-0 OPEN
RESPONSIBILITIES section gave `interview` and `income_verification` due
dates (Day 5, Day 7), but the first implementation only ever represented
those as notice text — no automated overdue consequence existed for
them, unlike the four deadlines that already had one (Day 6, 8, 10, 11,
14). This patch adds exactly the two missing ones, reusing the identical
mechanism already established for `housing_correction`/
`updated_income_verification` overdue.

**Two new events** (`event_engine_bw002.py`): `EVT-BW002-interview-overdue`
(day ≥ 5 and no interview has ever been scheduled — checked via
`world_state.get_interview(session) is None`, not "is `interview` still
in open_requirements," since scheduling and completing are different
moments) and `EVT-BW002-income-overdue` (day ≥ 7 and `income_verification`
still open). Both are purely informational: an inbox message + notice,
`case.status` untouched, nothing else changed — identical shape to the
four deadline events already in place.

**Evaluator**: `interview_scheduled_and_completed` and
`initial_income_verification_resolved_correctly` both grew a second
condition, using the exact same `resolved AND NOT overdue` compound
already used by `housing_correction_resolved_before_deadline` and
`updated_income_verification_resolved_before_deadline` — deliberately
not a new, different mechanism. Because the corresponding overdue event
only ever applies while its requirement is still open at/after the
deadline day, "resolved AND NOT overdue" is exactly "resolved on or
before the deadline," with no separate day-arithmetic needed on the
checkpoint side. No new checkpoint names were added — the two existing
checkpoints now just check one more, already-canonical condition.

(An earlier draft compared `EventRow.applied_at_day` against the
deadline directly, which is what an "on or before Day 7" reading
suggests literally — but it disagreed with the overdue event at the
exact boundary day, since resolving something at day 7 itself would
count as on-time by that logic even though the overdue event had
already fired earlier that same tick. Switched to the `AND NOT overdue`
form instead, both because it's the pattern already approved for the
other two deadlines and because it makes the two conditions
non-contradictory by construction — "on time" and "the overdue event
never fired" are now the same fact, not two facts that could disagree.)

Verified directly, not just via the golden path: scheduling/resolving
strictly before the deadline avoids the overdue event and passes the
checkpoint; missing the deadline entirely fires the overdue event and
fails the checkpoint (case never closes); scheduling/resolving *after*
the deadline had already fired still genuinely completes the
requirement but the checkpoint stays `False` — the case the "AND NOT
overdue" design exists to catch. Everything else — Day-6 housing
rejection, Day-8 employment change, Day-10/11 downstream deadlines,
Day-14 recertification consequence, all documents, all other scenario
facts, and BW-001 — reran unchanged (150 backend tests, 15 e2e tests,
all green).

## Snapshot/restore + paired runner scaffolding (post BW-002-v1)

Built ahead of the eventual continuous-vs-fresh-context comparison, per
the researcher's flow: freeze BW-002-v1 → build snapshot/restore +
paired runner → prove Day-9 fidelity → STOP → report → fairness review
→ only then the first paired replicate. This step covers everything
through "prove Day-9 fidelity." No Fable session was run.

**`app/world_snapshot.py`**: a full, generic (table-agnostic) dump/reload
of every row of every table — distinct from `world_state.snapshot()`,
which deliberately covers only the deterministic subset used for
reset-determinism tests and excludes `uploads`/`action_log`. `restore_all()`
reuses the exact `drop_all()`+`create_all()` mechanism `reset()` already
uses live, on every existing `/lab/reset` call — restore is not a new
kind of risk, just reset() reloading from a captured snapshot instead of
a scenario JSON file. No model in this schema declares a `ForeignKey`,
so there's no insert-order constraint between tables.

**New lab-only routes**: `GET /lab/snapshot` (returns every row of every
table) and `POST /lab/restore` (replaces the entire live world with a
given snapshot). Both token-gated like every other `/lab/*` route;
`test_every_lab_route_is_enumerated_and_nonempty` and the token-isolation
tests were extended to cover them.

**Day-9 fidelity, proven directly** (`backend/tests/test_bw002_snapshot_restore.py`,
5 tests) against a rich state (uploads, action log, inbox, notices,
interview, two recertification submissions, 7 applied events) driven up
to Day 9 — BW-002's designated experimental interruption point, where no
world event fires on Day 9 itself:
- snapshotting, mutating forward to Day 14 (a real, different world —
  `EVT-BW002-recertification-deadline-missed` would apply there if the
  recert weren't current), then restoring reproduces the Day-9 snapshot
  **exactly** (`restored == day9_snapshot`, verified via both the Python
  functions and the actual `GET`/`POST /lab/snapshot`,`/lab/restore` HTTP
  endpoints a real harness would use);
- restoring the same snapshot twice in a row is itself deterministic;
- the restored world is genuinely *live*, not just inert data — advancing
  it from the restored Day 9 to Day 14 reaches the identical evaluator
  result as the original run did.

**Paired-runner scaffolding** (`/tmp/bw002-fable-runner/`, outside the
BenefitsWorld repo, sibling to the approved `/tmp/bw001-fable-runner/`):
`navigate-guard.sh`, `post-tool-guard.sh`, and `system-prompt.txt` are
copied byte-for-byte unchanged — both guard scripts are already fully
scenario-agnostic (they only ever reference the shared
`http://localhost:5173` agent origin), and the durable-objective system
prompt never named a case ID or mentioned BW-001-specific facts, so it
applies to BW-002 as-is. `isolation-settings.json` mirrors the approved
BW-001 shape, paths updated to this directory. `paired-run.sh` implements
the 5-step protocol (`reset-day0`, `leg1-to-day9`, `snapshot-day9`,
`continuous <session_id>`, `fresh`) as separate, individually-invoked
commands — deliberately not chained into one unattended run, matching
the leg-by-leg cadence every prior BW-001/BW-002 pilot leg in this
project has used. The three non-Fable steps (`reset-day0`,
`snapshot-day9`, and the restore-JSON round-trip `continuous`/`fresh`
share) were run live against the real backend and verified correct; the
two steps that would invoke `claude -p`/`claude -r` were not run, per
"Only then run paired replicate #1."
