"""Unit and integration tests. Run with:  pytest -q"""
import pytest

from stc import (AIR, GROUND, SCENARIOS, AgentSpec, Constraints, Plan,
                 Reservation, ReservationTable, SimConfig, World, first_conflict,
                 plan_path, run)


def empty_world(w=8, h=8, d=1):
    return World(w, h, d)


# --- planner ------------------------------------------------------------------
def test_planner_finds_shortest_path_in_empty_world():
    w = empty_world()
    plan, _ = plan_path(w, GROUND, (0, 0, 0), (5, 3, 0), 0)
    assert plan is not None
    assert len(plan.cells) - 1 == 8                    # Manhattan distance
    assert plan.cells[0] == (0, 0, 0) and plan.cells[-1] == (5, 3, 0)


def test_planner_respects_vertex_constraint_by_waiting_or_detouring():
    w = empty_world()
    cons = Constraints()
    cons.add_path(0, [(1, 0, 0), (2, 0, 0), (3, 0, 0)])   # someone sits on our lane
    plan, _ = plan_path(w, GROUND, (0, 0, 0), (4, 0, 0), 0, cons)
    assert plan is not None
    for k, c in enumerate(plan.cells):
        assert not cons.vertex_blocked(c, plan.t0 + k)


def test_planner_forbids_head_on_swap():
    w = World(3, 1, 1)                                   # 1-lane, 3 cells
    cons = Constraints()
    cons.add_path(0, [(1, 0, 0), (0, 0, 0)])             # other moves 1 -> 0
    plan, _ = plan_path(w, GROUND, (0, 0, 0), (1, 0, 0), 0, cons, max_steps=6)
    # direct 0 -> 1 at t=0 would swap with the other agent; it must not do that
    assert plan is None or plan.cell_at(1) != (1, 0, 0)


def test_first_wait_forces_announce_tick():
    w = empty_world()
    plan, _ = plan_path(w, GROUND, (0, 0, 0), (3, 0, 0), 5, first_wait=True)
    assert plan.cells[0] == plan.cells[1] == (0, 0, 0)


def test_air_agent_flies_over_buildings_ground_cannot():
    blocked = {(1, 0, z) for z in range(3)}
    w = World(3, 1, 4, blocked)
    assert plan_path(w, GROUND, (0, 0, 0), (2, 0, 0), 0)[0] is None
    air, _ = plan_path(w, AIR, (0, 0, 3), (2, 0, 0), 0)
    assert air is not None and any(c[2] == 3 for c in air.cells)


# --- protocol --------------------------------------------------------------
def test_first_conflict_detects_vertex_and_swap():
    plan = Plan(0, [(0, 0, 0), (1, 0, 0), (2, 0, 0)])
    vertex = Reservation(1, 1, 0, 0, ((5, 0, 0), (1, 0, 0), (9, 0, 0)))
    swap = Reservation(2, 2, 0, 0, ((1, 0, 0), (0, 0, 0)))
    clear = Reservation(3, 3, 0, 0, ((0, 5, 0), (1, 5, 0), (2, 5, 0)))
    assert first_conflict(plan, vertex, 0) == 1
    assert first_conflict(plan, swap, 0) == 0
    assert first_conflict(plan, clear, 0) is None


def test_table_keeps_newest_and_filters_by_priority():
    tab = ReservationTable()
    old = Reservation(7, 7, 1, 1, ((0, 0, 0), (1, 0, 0)))
    new = Reservation(7, 7, 3, 3, ((4, 0, 0), (5, 0, 0)))
    tab.update(new)
    tab.update(old)                                     # late arrival of old msg
    assert tab.get(7) is new
    assert tab.constraints(3).vertex_blocked((4, 0, 0), 3)
    assert not tab.constraints(3, only_higher_than=5).vertex_blocked((4, 0, 0), 3)


# --- end-to-end -------------------------------------------------------------
def test_head_on_pair_in_two_lane_road_is_resolved_without_collision():
    w = World(8, 2, 1)
    specs = [AgentSpec(GROUND, (0, 0, 0), (7, 0, 0)),
             AgentSpec(GROUND, (7, 0, 0), (0, 0, 0))]
    r = run(w, specs, SimConfig(mode="stc", seed=0))
    assert r.success and r.collision_events == 0


@pytest.mark.parametrize("scenario", ["crossing", "open_grid", "mixed_city"])
def test_stc_is_collision_free_without_packet_loss(scenario):
    for seed in range(5):
        w, specs = SCENARIOS[scenario](seed=seed)
        r = run(w, specs, SimConfig(mode="stc", loss=0.0, seed=seed))
        assert r.success, (scenario, seed, r.collision_events, r.arrived, r.n_agents)


def test_central_oracle_is_collision_free_everywhere():
    for name in SCENARIOS:
        for seed in range(5):
            w, specs = SCENARIOS[name](seed=seed)
            r = run(w, specs, SimConfig(mode="central", seed=seed))
            assert r.collision_events == 0, (name, seed)


def test_simulation_is_deterministic():
    w, specs = SCENARIOS["mixed_city"](seed=3)
    a = run(w, specs, SimConfig(mode="stc", loss=0.3, seed=11))
    b = run(w, specs, SimConfig(mode="stc", loss=0.3, seed=11))
    assert (a.collision_events, a.makespan, a.messages_lost, a.replans) == \
           (b.collision_events, b.makespan, b.messages_lost, b.replans)


def test_loss_actually_drops_messages():
    w, specs = SCENARIOS["open_grid"](seed=0)
    r = run(w, specs, SimConfig(mode="stc", loss=0.5, seed=0))
    assert 0.4 < r.messages_lost / r.messages_sent < 0.6
