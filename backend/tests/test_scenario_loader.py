import json

from app import world_state


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
    assert len(docs) == 6
    assert len(events) == 1
    assert len(policy_items) == 5
    assert world_state.get_received_document_ids(session) == []
    assert len(world_state.get_notices(session)) == 1
    assert world_state.get_interview_slots(session) == []
    assert world_state.get_inbox_messages(session) == []
    assert world_state.get_applied_event_ids(session) == []
