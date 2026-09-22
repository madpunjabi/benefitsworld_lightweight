import json

from sqlalchemy.orm import Session

from app import config, models


def load_seed() -> dict:
    with open(config.SCENARIO_SEED_PATH) as f:
        return json.load(f)


def load_policy_library() -> dict:
    with open(config.POLICY_LIBRARY_PATH) as f:
        return json.load(f)


def load_scenario(session: Session, seed: dict | None = None, policy_library: dict | None = None) -> None:
    """Deterministically populate a freshly-created (empty) schema from the
    scenario seed file. Caller is responsible for creating the schema first
    (see reset.reset()). Always produces identical rows/ids given the same
    seed, since it only ever runs against an empty DB."""
    seed = seed if seed is not None else load_seed()
    policy_library = policy_library if policy_library is not None else load_policy_library()

    session.add(
        models.WorldStateMeta(
            id=1,
            scenario_id=config.SCENARIO_ID,
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
    session.add(
        models.Case(
            id=1,
            case_id=case["case_id"],
            status=case["status"],
            reported_employer=case.get("reported_employer"),
            open_requirements_json=json.dumps(case["open_requirements"]),
            interview_json=json.dumps(case["interview"]) if case.get("interview") is not None else None,
            recertification_json=None,
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
                available_from_day=0,
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
                effective_date=item["effective_date"],
                topic=item["topic"],
                authority_level=item["authority_level"],
                text=item["text"],
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

    session.commit()
