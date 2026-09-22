from app import reset, world_state


def test_reset_is_deterministic(client, session):
    snapshot_a = world_state.snapshot(session)

    # Mutate state.
    case = world_state.get_case(session)
    case.status = "SOME_OTHER_STATUS"
    session.commit()
    assert world_state.snapshot(session) != snapshot_a

    # Reset and capture again.
    reset.reset(session)
    snapshot_b = world_state.snapshot(session)

    assert snapshot_a == snapshot_b


def test_reset_twice_in_a_row_is_stable(client, session):
    reset.reset(session)
    first = world_state.snapshot(session)
    reset.reset(session)
    second = world_state.snapshot(session)
    assert first == second
