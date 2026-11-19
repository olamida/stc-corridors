"""Tick-based simulator for three coordination modes.

``stc``       decentralized corridor negotiation over a lossy network
``reactive``  baseline: independent shortest paths + stop-and-wait sensing
``central``   oracle: prioritized planning with global knowledge (upper bound)

All modes share one executor and one ground-truth collision checker, so the
numbers are directly comparable.
"""
from __future__ import annotations

import random
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from itertools import combinations
from typing import Dict, List, Optional, Sequence, Set, Tuple

from .agent import Agent, AgentSpec
from .planner import Constraints, Plan, plan_path
from .protocol import first_conflict
from .world import Cell, World


@dataclass
class SimConfig:
    mode: str = "stc"            # "stc" | "reactive" | "central"
    horizon: int = 12            # corridor lookahead H (ticks) broadcast each tick
    loss: float = 0.0            # independent per-link, per-tick packet loss
    comm_range: float = 1e9      # Manhattan range in cells
    latency: int = 0             # message delay in ticks
    sensing: bool = True         # adjacent-cell occupancy sensing (safety stop)
    announce_first: bool = True  # announce-then-act: broadcast a new corridor one tick before using it
    max_ticks: int = 300
    max_plan_steps: int = 200
    seed: int = 0
    record: bool = False


@dataclass
class Result:
    mode: str
    n_agents: int
    arrived: int
    success: bool
    collision_events: int
    collision_pairs: int
    makespan: Optional[int]
    mean_delay: Optional[float]
    messages_sent: int
    messages_lost: int
    replans: int
    expansions: int
    plan_failures: int
    safety_stops: int
    traj: Dict[int, List[Tuple[int, Cell]]] = field(default_factory=dict)
    windows: List[Dict[int, List[Cell]]] = field(default_factory=list)
    collision_log: List[Tuple[int, Tuple[int, int]]] = field(default_factory=list)


def _manhattan(a: Cell, b: Cell) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])


def _central_plans(world: World, agents: Sequence[Agent], cfg: SimConfig) -> None:
    cons = Constraints()
    for a in agents:                                   # priority order = id order
        plan, _ = plan_path(world, a.kind, a.start, a.goal, 0, cons,
                            max_steps=cfg.max_plan_steps)
        if plan is None:
            a.plan = Plan(0, [a.start] * (cfg.max_ticks + 2))   # never arrives
            a.plan_failures += 1
            cons.add_path(0, a.plan.cells[:2])
        else:
            a.plan = plan
            cons.add_path(0, plan.cells)


def _blocked_ahead(a: Agent, nxt: Cell, occupancy: Dict[Cell, Agent],
                   t: int, use_table: bool) -> bool:
    """Adjacent-cell occupancy sensing.

    A cell is blocked if another agent is in it now, unless (STC mode only) the
    occupant's last heard corridor says it is leaving that cell next tick.
    """
    b = occupancy.get(nxt)
    if b is None or b is a:
        return False
    if use_table:
        res = a.table.get(b.id)
        if res is not None:
            bn = res.cell_at(t + 1)
            if bn is not None and bn != nxt:
                return False
    return True


def run(world: World, specs: Sequence[AgentSpec], cfg: SimConfig) -> Result:
    rng = random.Random(cfg.seed)
    agents = [Agent(i, s, world) for i, s in enumerate(specs)]
    stats: Counter = Counter()
    collision_pairs: Set[Tuple[int, int]] = set()
    collision_log: List[Tuple[int, Tuple[int, int]]] = []
    pending: List[Tuple[int, int, object]] = []        # (deliver_t, receiver, msg)
    traj = {a.id: [(0, a.pos)] for a in agents} if cfg.record else {}
    windows: List[Dict[int, List[Cell]]] = []

    # --- initial plans -----------------------------------------------------
    if cfg.mode == "central":
        _central_plans(world, agents, cfg)
    elif cfg.mode == "reactive":
        for a in agents:
            plan, _ = plan_path(world, a.kind, a.start, a.goal, 0, None,
                                max_steps=cfg.max_plan_steps)
            a.path = list(plan.cells) if plan else [a.start]
    else:  # stc: every agent starts with a selfish plan (knows nobody yet)
        for a in agents:
            a.replan(world, 0, cfg.max_plan_steps, cfg.announce_first)

    last_tick = 0
    for t in range(cfg.max_ticks):
        active = [a for a in agents if not a.done]
        if not active:
            break
        last_tick = t

        if cfg.mode == "stc":
            # 1) broadcast corridor windows; 2) lossy delivery
            frame: Dict[int, List[Cell]] = {}
            for a in active:
                res = a.reservation(t, cfg.horizon)
                if res is None:
                    continue
                frame[a.id] = list(res.cells)
                for b in active:
                    if b is a or _manhattan(a.pos, b.pos) > cfg.comm_range:
                        continue
                    stats["sent"] += 1
                    if rng.random() < cfg.loss:
                        stats["lost"] += 1
                        continue
                    pending.append((t + cfg.latency, b.id, res))
            if cfg.record:
                windows.append(frame)
            still = []
            for deliver_t, rid, res in pending:
                if deliver_t <= t:
                    agents[rid].table.update(res)
                else:
                    still.append((deliver_t, rid, res))
            pending = still

            # 3) local reaction: yield to higher-priority corridors
            for a in active:
                a.table.forget_expired(t)
                need = (a.plan is None or a.plan.cell_at(t) != a.pos
                        or a.plan.cell_at(t + 1) is None)
                if not need:
                    for res in a.table.others():
                        if res.priority < a.id and first_conflict(a.plan, res, t) is not None:
                            need = True
                            break
                if need:
                    a.replan(world, t, cfg.max_plan_steps, cfg.announce_first)
        elif cfg.record:
            windows.append({})

        # --- execute one tick -------------------------------------------------
        occupancy = {a.pos: a for a in active}
        prev = {a.id: a.pos for a in active}
        moves: Dict[int, Cell] = {}
        for a in active:
            if cfg.mode == "reactive":
                nxt = a.path[a.path_idx + 1] if a.path_idx + 1 < len(a.path) else a.pos
            else:
                nxt = a.plan.cell_at(t + 1) if a.plan else a.pos
                if nxt is None:
                    nxt = a.pos
            if cfg.sensing and cfg.mode != "central" and nxt != a.pos:
                if _blocked_ahead(a, nxt, occupancy, t, cfg.mode == "stc"):
                    nxt = a.pos
                    stats["stops"] += 1
                    if cfg.mode == "stc":
                        a.plan = None      # plan is now time-shifted: re-plan
            moves[a.id] = nxt
        for a in active:
            if cfg.mode == "reactive" and moves[a.id] != a.pos:
                a.path_idx += 1
            a.pos = moves[a.id]

        # --- ground-truth collision check --------------------------------------
        by_cell: Dict[Cell, List[int]] = defaultdict(list)
        for a in active:
            by_cell[a.pos].append(a.id)
        for ids in by_cell.values():
            for pair in combinations(sorted(ids), 2):
                stats["collisions"] += 1
                collision_pairs.add(pair)
                collision_log.append((t + 1, pair))
        for a, b in combinations(active, 2):
            if (prev[a.id] == b.pos and prev[b.id] == a.pos
                    and prev[a.id] != prev[b.id]):
                stats["collisions"] += 1
                pair = (min(a.id, b.id), max(a.id, b.id))
                collision_pairs.add(pair)
                collision_log.append((t + 1, pair))

        for a in active:
            if cfg.record:
                traj[a.id].append((t + 1, a.pos))
            if a.pos == a.goal:
                a.done = True
                a.arrival = t + 1

    arrived = [a for a in agents if a.done]
    delays = [a.arrival - a.shortest for a in arrived if a.shortest is not None]
    all_done = len(arrived) == len(agents)
    return Result(
        mode=cfg.mode,
        n_agents=len(agents),
        arrived=len(arrived),
        success=all_done and stats["collisions"] == 0,
        collision_events=stats["collisions"],
        collision_pairs=len(collision_pairs),
        makespan=max(a.arrival for a in arrived) if all_done else None,
        mean_delay=(sum(delays) / len(delays)) if delays else None,
        messages_sent=stats["sent"],
        messages_lost=stats["lost"],
        replans=sum(a.replans for a in agents),
        expansions=sum(a.expansions for a in agents),
        plan_failures=sum(a.plan_failures for a in agents),
        safety_stops=stats["stops"],
        traj=traj,
        windows=windows,
        collision_log=collision_log,
    )
