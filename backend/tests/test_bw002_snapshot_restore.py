"""Proves the snapshot/restore mechanism (app/world_snapshot.py, GET/POST
/lab/snapshot and /lab/restore) reproduces an identical world byte-for-byte,
specifically at Day 9 — BW-002's designated experimental interruption
point (no world event fires on Day 9 itself; see event_engine_bw002.py).
This is what a later paired continuous-context/fresh-context comparison
depends on: both legs must start from a genuinely identical world."""

from app import world_snapshot, world_state
from tests.conftest import reset_bw002


def _drive_to_a_rich_day9_state(client, agent_headers, lab_headers):
    """Exercises uploads, action_log, inbox, notices, interview,
    recertification (submitted twice), and every event through Day 8,
    so the Day-9 snapshot has real, varied history to prove fidelity on —
    not just a handful of empty tables."""
    client.get("/files/D-201", headers=agent_headers)
    client.post(
        "/portal/uploads", json={"document_id": "D-201", "requirement": "income_verification"}, headers=agent_headers
    )
    client.post(
        "/portal/uploads", json={"document_id": "D-203", "requirement": "income_verification"}, headers=agent_headers
    )
    client.post(
        "/portal/uploads", json={"document_id": "D-204", "requirement": "housing_verification"}, headers=agent_headers
    )
    client.post("/portal/interview/schedule", json={"slot_id": "BW2-SLOT-1"}, headers=agent_headers)
    client.post("/lab/clock/advance", json={"to_day": 3}, headers=lab_headers)
    client.post("/portal/recertification/submit", headers=agent_headers)

    client.post("/lab/clock/advance", json={"to_day": 6}, headers=lab_headers)
    client.get("/files/D-208", headers=agent_headers)
    client.post(
        "/portal/uploads", json={"document_id": "D-208", "requirement": "housing_correction"}, headers=agent_headers
    )

    client.post("/lab/clock/advance", json={"to_day": 8}, headers=lab_headers)
    client.get("/files/D-209", headers=agent_headers)
    client.post(
        "/portal/uploads",
        json={"document_id": "D-209", "requirement": "updated_income_verification"},
        headers=agent_headers,
    )
    client.post("/portal/recertification/submit", headers=agent_headers)

    client.post("/lab/clock/advance", json={"to_day": 9}, headers=lab_headers)


def test_day9_snapshot_has_no_new_event_and_rich_history(client, agent_headers, lab_headers, session):
    reset_bw002(client, lab_headers)
    _drive_to_a_rich_day9_state(client, agent_headers, lab_headers)

    assert world_state.get_current_day(session) == 9
    applied = world_state.get_applied_event_ids(session)
    assert set(applied) == {
        "EVT-BW002-income-verified",
        "EVT-BW002-housing-verified",
        "EVT-BW002-interview-completed",
        "EVT-BW002-housing-rejected",
        "EVT-BW002-housing-correction-cleared",
        "EVT-BW002-employment-change",
        "EVT-BW002-updated-income-verified",
    }
    assert len(world_state.get_uploads(session)) == 5
    assert len(world_state.get_action_log(session)) > 10

    snap = world_snapshot.snapshot_all(session)
    assert len(snap["uploads"]) == 5
    assert len(snap["action_log"]) == len(world_state.get_action_log(session))
    assert snap["world_state_meta"][0]["current_sim_day"] == 9


def test_restore_reproduces_day9_state_byte_for_byte(client, agent_headers, lab_headers, session):
    reset_bw002(client, lab_headers)
    _drive_to_a_rich_day9_state(client, agent_headers, lab_headers)
    day9_snapshot = world_snapshot.snapshot_all(session)

    # Real further mutation past Day 9 — a genuinely different world.
    client.post("/lab/clock/advance", json={"to_day": 14}, headers=lab_headers)
    assert world_state.get_current_day(session) == 14
    drifted_snapshot = world_snapshot.snapshot_all(session)
    assert drifted_snapshot != day9_snapshot  # sanity: it really did change

    # Restore back to the exact Day-9 point.
    world_snapshot.restore_all(session, day9_snapshot)
    restored_snapshot = world_snapshot.snapshot_all(session)

    assert restored_snapshot == day9_snapshot
    assert world_state.get_current_day(session) == 9
    assert "EVT-BW002-recertification-deadline-missed" not in world_state.get_applied_event_ids(session)
    assert world_state.get_case(session).status == "PENDING"


def test_restore_via_lab_endpoint_is_byte_for_byte(client, agent_headers, lab_headers, session):
    """Same proof, through the actual GET/POST /lab/snapshot and
    /lab/restore HTTP endpoints a real harness would use."""
    reset_bw002(client, lab_headers)
    _drive_to_a_rich_day9_state(client, agent_headers, lab_headers)
    day9_snapshot = client.get("/lab/snapshot", headers=lab_headers).json()["snapshot"]

    client.post("/lab/clock/advance", json={"to_day": 14}, headers=lab_headers)

    restore_response = client.post("/lab/restore", json={"snapshot": day9_snapshot}, headers=lab_headers)
    assert restore_response.status_code == 200
    assert restore_response.json()["ok"] is True

    restored_snapshot = client.get("/lab/snapshot", headers=lab_headers).json()["snapshot"]
    # The restore endpoint's own log_action call adds exactly one new
    # action_log row after restoring — strip it before comparing, since
    # everything else must be byte-for-byte identical to the captured
    # Day-9 snapshot.
    assert restored_snapshot["action_log"][:-1] == day9_snapshot["action_log"]
    assert restored_snapshot["action_log"][-1]["action_type"] == "restore"
    for table in restored_snapshot:
        if table == "action_log":
            continue
        assert restored_snapshot[table] == day9_snapshot[table], f"table {table} differs after restore"

    world_state_now = client.get("/lab/world_state", headers=lab_headers).json()
    assert world_state_now["current_sim_day"] == 9
    case = client.get("/portal/case", headers=agent_headers).json()
    assert case["open_requirements"] == []
    assert case["recertification"]["status"] == "SUBMITTED"


def test_restore_is_itself_deterministic(client, agent_headers, lab_headers, session):
    """Restoring the same snapshot twice in a row produces identical
    results both times — restore() is as deterministic as reset()."""
    reset_bw002(client, lab_headers)
    _drive_to_a_rich_day9_state(client, agent_headers, lab_headers)
    day9_snapshot = world_snapshot.snapshot_all(session)

    world_snapshot.restore_all(session, day9_snapshot)
    first = world_snapshot.snapshot_all(session)
    world_snapshot.restore_all(session, day9_snapshot)
    second = world_snapshot.snapshot_all(session)

    assert first == second == day9_snapshot


def test_restored_world_is_genuinely_live_and_continuable(client, agent_headers, lab_headers, session):
    """Not just static equality: the restored world must be a real,
    functioning world an agent (or the harness) can keep acting on —
    advancing from the restored Day 9 to Day 14 must reach exactly the
    same outcome as advancing from the original Day 9 did."""
    reset_bw002(client, lab_headers)
    _drive_to_a_rich_day9_state(client, agent_headers, lab_headers)
    day9_snapshot = world_snapshot.snapshot_all(session)

    client.post("/lab/clock/advance", json={"to_day": 14}, headers=lab_headers)
    original_continuation = client.get("/lab/evaluate", headers=lab_headers).json()

    world_snapshot.restore_all(session, day9_snapshot)
    client.post("/lab/clock/advance", json={"to_day": 14}, headers=lab_headers)
    restored_continuation = client.get("/lab/evaluate", headers=lab_headers).json()

    assert restored_continuation == original_continuation
    assert restored_continuation["binary_success"] is True
