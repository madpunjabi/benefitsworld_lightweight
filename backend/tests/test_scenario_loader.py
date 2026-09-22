import json

from app import visible_state, world_state


def test_scenario_loader_populates_core_tables(client, session):
    meta = world_state.get_meta(session)
    household = world_state.get_household(session)
    case = world_state.get_case(session)
    docs = world_state.get_documents(session)
    events = world_state.get_calendar_events(session)
    policy_items = world_state.get_policy_items(session)

    assert meta.scenario_id == "BW-001"
    assert meta.current_sim_day == 0
    assert household.primary_applicant == "Maya Torres"
    assert case.status == "PENDING"
    assert "earned_income_verification" in json.loads(case.open_requirements_json)
    # 7 canonical documents exist (D-101..D-107), but D-107 (the Day-18
    # paystub) is not yet available_from_day-visible at Day 0.
    assert len(docs) == 7
    assert {d["id"] for d in visible_state.files_view(session)} == {
        "D-101", "D-102", "D-103", "D-104", "D-105", "D-106",
    }
    assert len(events) == 1
    assert len(policy_items) == 5
    assert world_state.get_received_document_ids(session) == []
    assert len(world_state.get_notices(session)) == 1
    assert world_state.get_interview_slots(session) == []
    assert world_state.get_inbox_messages(session) == []
    assert world_state.get_applied_event_ids(session) == []
