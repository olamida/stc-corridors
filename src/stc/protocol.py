"""Corridor reservation messages, the local reservation table, conflict test.

Protocol summary (see docs/DESIGN.md):

1. Every tick, each agent broadcasts a *reservation*: its next ``H`` planned
   cells with timestamps (a short Spatio-Temporal Corridor).
2. Each agent keeps the newest reservation it has heard from every neighbour.
3. If its own plan conflicts with a reservation from a *higher-priority*
   agent, it yields: it re-plans (space-time A*) around everything it knows.
4. Nothing here needs a central server, and a lost message only delays
   conflict detection; the lookahead window gives repeated chances to hear.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .planner import Constraints, Plan
from .world import Cell


@dataclass(frozen=True)
class Reservation:
    sender: int
    priority: int            # lower value = higher priority
    t_sent: int
    t0: int                  # time of cells[0]
    cells: Tuple[Cell, ...]  # cells[k] is the position at time t0 + k

    @property
    def t_end(self) -> int:
        return self.t0 + len(self.cells) - 1

    def cell_at(self, t: int) -> Optional[Cell]:
        k = t - self.t0
        if 0 <= k < len(self.cells):
            return self.cells[k]
        return None


def first_conflict(plan: Plan, res: Reservation, t_from: int) -> Optional[int]:
    """Earliest time >= ``t_from`` at which ``plan`` and ``res`` collide.

    Detects vertex conflicts (same cell, same time) and swap conflicts
    (two agents exchanging cells between t and t+1). Returns ``None`` if
    the two corridors are compatible over their overlap.
    """
    lo = max(plan.t0, res.t0, t_from)
    hi = min(plan.end, res.t_end)
    for t in range(lo, hi + 1):
        a, b = plan.cell_at(t), res.cell_at(t)
        if a == b:
            return t
        if t < hi:
            a2, b2 = plan.cell_at(t + 1), res.cell_at(t + 1)
            if a == b2 and a2 == b:
                return t
    return None


class ReservationTable:
    """The newest reservation heard from each other agent (local knowledge)."""

    def __init__(self) -> None:
        self._by_sender: Dict[int, Reservation] = {}

    def update(self, res: Reservation) -> None:
        old = self._by_sender.get(res.sender)
        if old is None or res.t_sent >= old.t_sent:
            self._by_sender[res.sender] = res

    def get(self, sender: int) -> Optional[Reservation]:
        return self._by_sender.get(sender)

    def others(self) -> List[Reservation]:
        return list(self._by_sender.values())

    def forget_expired(self, t_now: int) -> None:
        dead = [s for s, r in self._by_sender.items() if r.t_end < t_now]
        for s in dead:
            del self._by_sender[s]

    def constraints(self, t_now: int, only_higher_than: Optional[int] = None) -> Constraints:
        """Known corridors as planning constraints.

        If ``only_higher_than`` is given, keep only reservations whose priority
        is strictly higher (numerically lower) than that value.
        """
        cons = Constraints()
        for r in self._by_sender.values():
            if only_higher_than is not None and r.priority >= only_higher_than:
                continue
            lo = max(t_now, r.t0)
            if lo > r.t_end:
                continue
            cons.add_path(lo, r.cells[lo - r.t0:])
        return cons
