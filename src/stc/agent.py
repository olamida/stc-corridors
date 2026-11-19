"""A single decentralized agent: local plan, local table, local re-planning."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .planner import Plan, plan_path
from .protocol import Reservation, ReservationTable
from .world import Cell, World


@dataclass(frozen=True)
class AgentSpec:
    kind: str     # "ground" | "air"
    start: Cell
    goal: Cell


class Agent:
    def __init__(self, idx: int, spec: AgentSpec, world: World) -> None:
        self.id = idx                      # also the priority (lower = higher)
        self.kind = spec.kind
        self.pos: Cell = spec.start
        self.start = spec.start
        self.goal = spec.goal
        self.plan: Optional[Plan] = None
        self.table = ReservationTable()
        self.done = False
        self.arrival: Optional[int] = None
        # reactive-baseline state
        self.path: Optional[List[Cell]] = None
        self.path_idx = 0
        # statistics
        self.replans = 0
        self.expansions = 0
        self.plan_failures = 0
        self.shortest = world.shortest_length(spec.start, spec.goal, spec.kind)

    def reservation(self, t: int, horizon: int) -> Optional[Reservation]:
        if self.plan is None:
            return None
        cells = self.plan.window(t, horizon)
        if not cells:
            return None
        return Reservation(self.id, self.id, t, max(t, self.plan.t0), tuple(cells))

    def replan(self, world: World, t: int, max_steps: int,
               announce_first: bool = True) -> None:
        """Re-plan from the current position around the corridors heard.

        Preference order (each step is tried only if the previous one found no
        plan):
          1. avoid *all* known corridors, announce-then-act
          2. avoid all known corridors, move immediately
          3. avoid only *higher-priority* corridors (lower-priority agents are
             expected to yield to us), announce-then-act
          4. as 3, move immediately
          5. hold position this tick and retry next tick
        """
        attempts = []
        for scope in (None, self.id):
            cons = self.table.constraints(t, only_higher_than=scope)
            attempts.append((cons, announce_first))
            if announce_first:
                attempts.append((cons, False))
        plan = None
        for cons, first_wait in attempts:
            plan, exp = plan_path(world, self.kind, self.pos, self.goal, t, cons,
                                  max_steps=max_steps, first_wait=first_wait)
            self.expansions += exp
            if plan is not None:
                break
        self.replans += 1
        if plan is None:
            self.plan_failures += 1
            plan = Plan(t, [self.pos, self.pos])
        self.plan = plan
