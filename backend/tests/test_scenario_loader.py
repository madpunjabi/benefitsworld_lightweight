import json

from app import world_state


def test_scenario_loader_populates_core_tables(client, session):
    meta = world_state.get_meta(session)
    household = world_state.get_household(session)
    case = world_state.get_case(session)
    docs = world_state.get_documents(session)
    events = world_state.get_calendar_events(session)

    assert meta.scenario_id == "BW-001"
    assert meta.current_sim_day == 0
    assert household.primary_applicant == "Maya Torres"
    assert case.status == "PENDING"
    assert "earned_income_verification" in json.loads(case.open_requirements_json)
    assert len(docs) == 5
    assert len(events) == 1
