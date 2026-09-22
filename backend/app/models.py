from sqlalchemy import CheckConstraint, Column, Integer, String, Text

from app.db import Base


class WorldStateMeta(Base):
    __tablename__ = "world_state_meta"

    id = Column(Integer, primary_key=True)
    scenario_id = Column(String, nullable=False)
    scenario_version = Column(String, nullable=False)
    current_sim_day = Column(Integer, nullable=False, default=0)


class Household(Base):
    __tablename__ = "household"

    id = Column(Integer, primary_key=True)
    primary_applicant = Column(String, nullable=False)
    members_json = Column(Text, nullable=False)
    preferences_json = Column(Text, nullable=False)


class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True)
    case_id = Column(String, nullable=False)
    status = Column(String, nullable=False)
    reported_employer = Column(String, nullable=True)
    open_requirements_json = Column(Text, nullable=False)
    interview_json = Column(Text, nullable=True)
    recertification_json = Column(Text, nullable=True)


class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True)
    filename = Column(String, nullable=False)
    doc_date = Column(String, nullable=False)
    visible_text = Column(Text, nullable=False)
    simulator_tags_json = Column(Text, nullable=False)
    available_from_day = Column(Integer, nullable=False, default=0)


class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    day = Column(Integer, nullable=False)
    start_time = Column(String, nullable=False)
    end_time = Column(String, nullable=False)
    label = Column(String, nullable=False)
    source = Column(String, nullable=False)


class Upload(Base):
    __tablename__ = "uploads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(String, nullable=False)
    requirement = Column(String, nullable=False)
    attempted_at_day = Column(Integer, nullable=False)
    ui_reported_success = Column(Integer, nullable=False)
    actually_persisted = Column(Integer, nullable=False)
    scripted_failure_id = Column(String, nullable=True)


class PolicyItem(Base):
    __tablename__ = "policy_items"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    source = Column(String, nullable=False)
    source_url = Column(String, nullable=True)
    jurisdiction = Column(String, nullable=False)
    # A source's own revision/version label (e.g. "12/23") is not
    # necessarily a regulatory effective date. Keep them distinct rather
    # than inferring one from the other (Milestone 2.1 correction).
    effective_date = Column(String, nullable=True)
    source_version = Column(String, nullable=True)
    topic = Column(String, nullable=False)
    authority_level = Column(String, nullable=False)
    text = Column(Text, nullable=False)


class EventRow(Base):
    """Persisted applied-state for event_engine.py events, keyed by the
    event's stable id. Definitions (predicate/apply) live in code; this
    table only records whether/when each one has fired, so applied state
    survives a process restart."""

    __tablename__ = "events"

    id = Column(String, primary_key=True)
    event_type = Column(String, nullable=False)
    trigger_description = Column(String, nullable=False)
    applied = Column(Integer, nullable=False, default=0)
    applied_at_day = Column(Integer, nullable=True)


class InterviewSlot(Base):
    __tablename__ = "interview_slots"

    id = Column(String, primary_key=True)
    day = Column(Integer, nullable=False)
    start_time = Column(String, nullable=False)
    end_time = Column(String, nullable=False)


class Notice(Base):
    __tablename__ = "notices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    day = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)


class InboxMessage(Base):
    __tablename__ = "inbox_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    day = Column(Integer, nullable=False)
    sender = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    is_read = Column(Integer, nullable=False, default=0)


class ActionLog(Base):
    __tablename__ = "action_log"
    __table_args__ = (
        CheckConstraint(
            "actor IN ('benchmark_agent', 'household', 'harness', 'system')",
            name="ck_action_log_actor",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    actor = Column(String, nullable=False)
    sim_day = Column(Integer, nullable=False)
    action_type = Column(String, nullable=False)
    payload_json = Column(Text, nullable=False)
    result = Column(String, nullable=False)
