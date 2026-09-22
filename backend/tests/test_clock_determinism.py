from app import clock, reset, world_state


def test_advance_to_day_18_is_deterministic(client, session):
    reset.reset(session)
    clock.advance_to(session, 18)
    snapshot_a = world_state.snapshot(session)

    reset.reset(session)
    clock.advance_to(session, 18)
    snapshot_b = world_state.snapshot(session)

    assert snapshot_a == snapshot_b
    assert snapshot_a["meta"]["current_sim_day"] == 18


def test_advance_rejects_moving_backwards(client, session):
    reset.reset(session)
    clock.advance_to(session, 18)
    try:
        clock.advance_to(session, 5)
        assert False, "expected ValueError"
    except ValueError:
        pass
