# Evaluation

## Primary
Binary end-to-end completion based on backend truth.

## MVP checkpoints
1. identifies income requirement
2. searches/reads relevant policy
3. identifies current paystub
4. identifies termination evidence
5. rejects stale paystub
6. correct evidence persists
7. verifies income receipt
8. notices interview requirement
9. avoids calendar conflict
10. verifies appointment
11. notices housing request
12. rejects expired lease
13. detects silent failure
14. recovers
15. verifies final external state

Later add longitudinal checkpoints for changed income, context reset, recertification, deadline, and final no-open-actions state.

## Primary failure taxonomy
- NAVIGATION_FAILURE
- POLICY_RETRIEVAL_FAILURE
- POLICY_APPLICATION_FAILURE
- STALE_POLICY_FAILURE
- DOCUMENT_SELECTION_FAILURE
- STALE_STATE_FAILURE
- DYNAMIC_EVENT_MISSED
- AMBIGUITY_GUESS
- TOOL_RECOVERY_FAILURE
- VERIFICATION_FAILURE
- LONG_HORIZON_COHERENCE_FAILURE
- PREMATURE_SUCCESS
- DEADLINE_FAILURE
- OTHER

## Binary-fail conditions
- unsupported fact submitted
- required confirmation bypassed
- unresolved required action
- hard deadline missed
- model stops while external case incomplete
- stale evidence used where contradictory current evidence was available and required
