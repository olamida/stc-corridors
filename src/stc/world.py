"""Discrete 3D grid world used by the STC simulator.

Cells are ``(x, y, z)`` integer tuples. Two agent kinds share the world:

* ``ground`` agents move on the ``z == 0`` layer (4-connected).
* ``air`` agents move in all three axes (6-connected) and may fly over
  obstacles that do not reach their altitude.

Time is discrete: one tick = one move (or one wait).
"""
from __future__ import annotations

from collections import deque
from typing import Dict, Iterable, Iterator, Set, Tuple

Cell = Tuple[int, int, int]

GROUND = "ground"
AIR = "air"

_MOVES_GROUND = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0))
_MOVES_AIR = _MOVES_GROUND + ((0, 0, 1), (0, 0, -1))


class World:
    """A bounded 3D occupancy grid with static obstacles."""

    def __init__(self, width: int, height: int, depth: int = 1,
                 blocked: Iterable[Cell] = ()) -> None:
        self.width = width
        self.height = height
        self.depth = depth
        self.blocked: Set[Cell] = set(blocked)
        self._dist_cache: Dict[Tuple[Cell, str], Dict[Cell, int]] = {}

    # -- geometry ---------------------------------------------------------
    def in_bounds(self, c: Cell) -> bool:
        x, y, z = c
        return 0 <= x < self.width and 0 <= y < self.height and 0 <= z < self.depth

    def is_free(self, c: Cell, kind: str) -> bool:
        if not self.in_bounds(c) or c in self.blocked:
            return False
        if kind == GROUND and c[2] != 0:
            return False
        return True

    def neighbors(self, c: Cell, kind: str) -> Iterator[Cell]:
        moves = _MOVES_GROUND if kind == GROUND else _MOVES_AIR
        x, y, z = c
        for dx, dy, dz in moves:
            n = (x + dx, y + dy, z + dz)
            if self.is_free(n, kind):
                yield n

    # -- shortest paths (ignoring other agents) -----------------------------
    def distance_map(self, goal: Cell, kind: str) -> Dict[Cell, int]:
        """BFS distance from every reachable cell to ``goal`` (cached).

        Used as an admissible heuristic by the space-time A* planner and to
        compute each agent's free-space shortest length (the delay baseline).
        """
        key = (goal, kind)
        cached = self._dist_cache.get(key)
        if cached is not None:
            return cached
        dist: Dict[Cell, int] = {}
        if self.is_free(goal, kind):
            dist[goal] = 0
            queue = deque([goal])
            while queue:
                cur = queue.popleft()
                for n in self.neighbors(cur, kind):
                    if n not in dist:
                        dist[n] = dist[cur] + 1
                        queue.append(n)
        self._dist_cache[key] = dist
        return dist

    def shortest_length(self, start: Cell, goal: Cell, kind: str):
        return self.distance_map(goal, kind).get(start)
