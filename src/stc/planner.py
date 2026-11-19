"""Space-time A* with vertex and swap (edge) constraints.

A *plan* is a list of cells indexed by absolute time: ``cells[k]`` is where
the agent is at time ``t0 + k``. A *corridor* in this project is exactly such
a plan: a sequence of ``(x, y, z, t)`` tuples the agent intends to occupy.
"""
from __future__ import annotations

import heapq
import itertools
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Set, Tuple

from .world import Cell, World


@dataclass
class Plan:
    """A timed path. ``cells[k]`` is the position at time ``t0 + k``."""

    t0: int
    cells: List[Cell]

    @property
    def end(self) -> int:
        return self.t0 + len(self.cells) - 1

    def cell_at(self, t: int) -> Optional[Cell]:
        k = t - self.t0
        if 0 <= k < len(self.cells):
            return self.cells[k]
        return None

    def window(self, t: int, horizon: int) -> List[Cell]:
        """Cells from ``t`` to ``t + horizon`` (clipped to the plan's end)."""
        lo = max(t, self.t0) - self.t0
        hi = min(t + horizon, self.end) - self.t0
        return self.cells[lo:hi + 1]


class Constraints:
    """Other agents' known occupancy: vertex (cell, time) and moves."""

    def __init__(self) -> None:
        self.vertex: Dict[int, Set[Cell]] = defaultdict(set)
        self.moves: Set[Tuple[int, Cell, Cell]] = set()

    def add_path(self, t0: int, cells: Sequence[Cell]) -> None:
        for k, c in enumerate(cells):
            self.vertex[t0 + k].add(c)
        for k in range(len(cells) - 1):
            self.moves.add((t0 + k, cells[k], cells[k + 1]))

    def vertex_blocked(self, c: Cell, t: int) -> bool:
        s = self.vertex.get(t)
        return s is not None and c in s

    def swap_blocked(self, t: int, u: Cell, v: Cell) -> bool:
        """True if another agent moves v->u during t->t+1 (head-on swap)."""
        return (t, v, u) in self.moves


def plan_path(world: World, kind: str, start: Cell, goal: Cell, t0: int,
              constraints: Optional[Constraints] = None,
              max_steps: int = 200, max_expansions: int = 40000,
              first_wait: bool = False) -> Tuple[Optional[Plan], int]:
    """Cooperative space-time A*.

    Returns ``(plan, expansions)``; ``plan`` is ``None`` if no collision-free
    plan was found within ``max_steps`` / ``max_expansions``. Waiting in place
    is a legal action, which is what lets low-priority agents *yield*.

    ``first_wait=True`` forces the first action to be a wait. The corridor is
    then broadcast one tick *before* the agent first moves along it
    ("announce-then-act"), so neighbours can object in time.
    """
    h = world.distance_map(goal, kind)
    if start not in h:
        return None, 0
    cons = constraints if constraints is not None else Constraints()

    tie = itertools.count()
    heap = [(h[start], 0, next(tie), start, t0)]
    parent: Dict[Tuple[Cell, int], Optional[Tuple[Cell, int]]] = {(start, t0): None}
    expansions = 0

    while heap:
        _, _, _, cell, t = heapq.heappop(heap)
        expansions += 1
        if cell == goal:
            path: List[Cell] = []
            node: Optional[Tuple[Cell, int]] = (cell, t)
            while node is not None:
                path.append(node[0])
                node = parent[node]
            path.reverse()
            return Plan(t0, path), expansions
        if expansions > max_expansions:
            break
        g = t - t0
        if g >= max_steps:
            continue
        nt = t + 1
        options = (cell,) if (first_wait and g == 0) else itertools.chain(
            (cell,), world.neighbors(cell, kind))
        for nxt in options:
            if nxt not in h:
                continue
            key = (nxt, nt)
            if key in parent:
                continue
            if cons.vertex_blocked(nxt, nt):
                continue
            if nxt != cell and cons.swap_blocked(t, cell, nxt):
                continue
            parent[key] = (cell, t)
            heapq.heappush(heap, (g + 1 + h[nxt], -(g + 1), next(tie), nxt, nt))
    return None, expansions
