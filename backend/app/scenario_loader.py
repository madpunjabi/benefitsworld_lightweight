import json

from sqlalchemy.orm import Session

from app import config, models


def load_seed(scenario_id: str | None = None) -> dict:
    path = config.SCENARIO_SEED_PATHS[scenario_id] if scenario_id is not None else config.SCENARIO_SEED_PATH
    with open(path) as f:
        return json.load(f)


def load_policy_library() -> dict:
    with open(config.POLICY_LIBRARY_PATH) as f:
        return json.load(f)


def load_scenario(
    session: Session,
    seed: dict | None = None,
    policy_library: dict | None = None,
    scenario_id: str | None = None,
) -> None:
    """Deterministically populate a freshly-created (empty) schema from the
    scenario seed file. Caller is responsible for creating the schema first
    (see reset.reset()). Always produces identical rows/ids given the same
    seed, since it only ever runs against an empty DB.

    `scenario_id`, when given, picks which scenario's seed file to load
    (see config.SCENARIO_SEED_PATHS) and is recorded on WorldStateMeta;
    omitting it preserves the original behavior of always loading whatever
    config.SCENARIO_ID/SCENARIO_SEED_PATH resolved to at process start."""
    seed = seed if seed is not None else load_seed(scenario_id)
    policy_library = policy_library if policy_library is not None else load_policy_library()

    session.add(
        models.WorldStateMeta(
            id=1,
            scenario_id=scenario_id if scenario_id is not None else config.SCENARIO_ID,
            scenario_version=config.SCENARIO_VERSION,
            current_sim_day=0,
        )
    )

    household = seed["household"]
    session.add(
        models.Household(
            id=1,
            primary_applicant=household["primary_applicant"],
            members_json=json.dumps(household["members"]),
            preferences_json=json.dumps(household["preferences"]),
        )
    )

    case = seed["initial_case"]
    # Only scenarios that opt in (uses_recertification: true) get an
    # initial recertification record; leaving it None for everyone else
    # (BW-001 always) preserves the exact original CaseOut.recertification
    # response of `null` — see app/recertification.py for how a non-null
    # raw record then drives a computed status.
    initial_recertification = (
        {"submitted_at_day": None, "needs_update": False, "snapshot_applied_event_ids": []}
        if case.get("uses_recertification")
        else None
    )
    session.add(
        models.Case(
            id=1,
            case_id=case["case_id"],
            status=case["status"],
            reported_employer=case.get("reported_employer"),
            open_requirements_json=json.dumps(case["open_requirements"]),
            interview_json=json.dumps(case["interview"]) if case.get("interview") is not None else None,
            recertification_json=json.dumps(initial_recertification) if initial_recertification is not None else None,
        )
    )

    for doc in seed["documents"]:
        session.add(
            models.Document(
                id=doc["id"],
                filename=doc["filename"],
                doc_date=doc["date"],
                visible_text=doc["visible_text"],
                simulator_tags_json=json.dumps(doc["simulator_tags"]),
                available_from_day=doc.get("available_from_day", 0),
            )
        )

    for item in policy_library["items"]:
        session.add(
            models.PolicyItem(
                id=item["id"],
                title=item["title"],
                source=item["source"],
                source_url=item.get("source_url"),
                jurisdiction=item["jurisdiction"],
                effective_date=item.get("effective_date"),
                source_version=item.get("source_version"),
                topic=item["topic"],
                authority_level=item["authority_level"],
                text=item["text"],
            )
        )

    for slot in seed.get("interview_slots", []):
        session.add(
            models.InterviewSlot(
                id=slot["id"], day=slot["day"], start_time=slot["start_time"], end_time=slot["end_time"]
            )
        )

    for entry in seed.get("calendar_busy", []):
        session.add(
            models.CalendarEvent(
                day=entry["day"],
                start_time=entry["start"],
                end_time=entry["end"],
                label=entry["label"],
                source="household",
            )
        )

    for notice in seed.get("initial_notices", []):
        session.add(models.Notice(day=notice["day"], text=notice["text"]))

    for failure in seed.get("silent_failures", []):
        session.add(
            models.SilentFailure(
                id=failure["id"],
                document_id=failure["document_id"],
                requirement=failure["requirement"],
                consumed=0,
            )
        )

    session.commit()
