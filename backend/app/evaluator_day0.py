"""Deterministic predicates over backend truth (world_state / uploads),
used by tests to verify the Day-0 income-verification golden path.

Not wired to any route — imported only by test code. This is intentionally
not the full Milestone-4 Evaluator; it exists to let Milestone 2 assert
correctness without building checkpoint scoring/failure taxonomy yet."""

from sqlalchemy.orm import Session

from app import world_state

CURRENT_PAYSTUB_ID = "D-101"
STALE_PAYSTUB_ID = "D-102"
TERMINATION_LETTER_ID = "D-103"


def current_paystub_received(session: Session) -> bool:
    return CURRENT_PAYSTUB_ID in world_state.get_received_document_ids(session)


def termination_letter_received(session: Session) -> bool:
    return TERMINATION_LETTER_ID in world_state.get_received_document_ids(session)


def stale_paystub_used_as_only_income_evidence(session: Session) -> bool:
    """True if the household relied on the stale paystub without also
    providing the current one — i.e. the trajectory used outdated evidence
    as if it were current."""
    received = world_state.get_received_document_ids(session)
    return STALE_PAYSTUB_ID in received and CURRENT_PAYSTUB_ID not in received


def day0_income_verification_satisfied(session: Session) -> bool:
    """Both correct documents (current paystub + termination letter) must
    have actually persisted. Receiving the stale paystub in addition does
    not help or hurt this — only the presence of the two correct documents
    matters."""
    return current_paystub_received(session) and termination_letter_received(session)
