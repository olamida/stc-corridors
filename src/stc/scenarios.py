"""Seeded scenario generators. Every scenario returns ``(World, [AgentSpec])``.

Agent order is priority order (index 0 = highest priority).
"""
from __future__ import annotations

import random
from typing import List, Tuple

from .agent import AgentSpec
from .world import AIR, GROUND, Cell, World


def _distinct(rng: random.Random, pool: List[Cell], n: int) -> List[Cell]:
    return rng.sample(pool, n)


def crossing(n_agents: int = 8, seed: int = 0) -> Tuple[World, List[AgentSpec]]:
    """Plus-shaped intersection, two-lane roads, agents enter from the 4 arms
    and leave through a different arm (straight, left or right)."""
    size, lo, hi = 14, 6, 7           # roads occupy rows/cols 6-7
    free = set()
    for i in range(size):
        for w in (lo, hi):
            free.add((i, w, 0))
            free.add((w, i, 0))
    blocked = {(x, y, 0) for x in range(size) for y in range(size)} - free
    world = World(size, size, 1, blocked)
    rng = random.Random(seed)
    arms = {
        "W": [(0, lo, 0), (0, hi, 0), (1, lo, 0), (1, hi, 0)],
        "E": [(size - 1, lo, 0), (size - 1, hi, 0), (size - 2, lo, 0), (size - 2, hi, 0)],
        "N": [(lo, 0, 0), (hi, 0, 0), (lo, 1, 0), (hi, 1, 0)],
        "S": [(lo, size - 1, 0), (hi, size - 1, 0), (lo, size - 2, 0), (hi, size - 2, 0)],
    }
    names = list(arms)
    used_s, used_g = set(), set()
    specs: List[AgentSpec] = []
    for i in range(n_agents):
        src = names[i % 4]
        dst = rng.choice([n for n in names if n != src
                          and any(c not in used_g for c in arms[n])])
        s = rng.choice([c for c in arms[src] if c not in used_s])
        g = rng.choice([c for c in arms[dst] if c not in used_g])
        used_s.add(s)
        used_g.add(g)
        specs.append(AgentSpec(GROUND, s, g))
    return world, specs


def corridor(n_each: int = 3, seed: int = 0) -> Tuple[World, List[AgentSpec]]:
    """Single-lane corridor with two passing bays and a waiting room at each
    end. Agents travel in both directions and must negotiate who yields."""
    length, rows = 22, 7
    free = {(x, 3, 0) for x in range(length)}            # the lane
    free |= {(6, 2, 0), (14, 2, 0)}                      # passing bays
    free |= {(x, y, 0) for x in (0, 1) for y in (2, 3, 4)}
    free |= {(x, y, 0) for x in (length - 2, length - 1) for y in (2, 3, 4)}
    blocked = {(x, y, 0) for x in range(length) for y in range(rows)} - free
    world = World(length, rows, 1, blocked)
    rng = random.Random(seed)
    left = [(x, y, 0) for x in (0, 1) for y in (2, 3, 4)]
    right = [(x, y, 0) for x in (length - 2, length - 1) for y in (2, 3, 4)]
    ls, rs = rng.sample(left, n_each), rng.sample(right, n_each)
    lg = rng.sample([c for c in left if c not in ls], n_each)
    rg = rng.sample([c for c in right if c not in rs], n_each)
    specs: List[AgentSpec] = []
    for i in range(n_each):
        specs.append(AgentSpec(GROUND, ls[i], rg[i]))      # left -> right
        specs.append(AgentSpec(GROUND, rs[i], lg[i]))      # right -> left
    return world, specs


def open_grid(n_agents: int = 16, size: int = 20, density: float = 0.12,
              seed: int = 0) -> Tuple[World, List[AgentSpec]]:
    """Random obstacle field; random start/goal pairs for ground agents."""
    rng = random.Random(seed)
    for _ in range(200):
        blocked = {(x, y, 0) for x in range(size) for y in range(size)
                   if rng.random() < density}
        world = World(size, size, 1, blocked)
        cells = [(x, y, 0) for x in range(size) for y in range(size)
                 if (x, y, 0) not in blocked]
        if len(cells) < 2 * n_agents:
            continue
        starts = _distinct(rng, cells, n_agents)
        used, specs, ok = set(), [], True
        for st in starts:
            dm = None
            cand = []
            for g in cells:
                if g in used or g in starts:
                    continue
                d = world.shortest_length(st, g, GROUND)
                if d is not None and d >= size // 2:
                    cand.append(g)
            if not cand:
                ok = False
                break
            g = rng.choice(cand)
            used.add(g)
            specs.append(AgentSpec(GROUND, st, g))
        if ok:
            return world, specs
    raise RuntimeError("could not generate a connected open_grid scenario")


def mixed_city(n_ground: int = 8, n_air: int = 8, seed: int = 0,
               blocks: int = 4) -> Tuple[World, List[AgentSpec]]:
    """Street grid with 3-storey buildings. Ground vehicles drive on streets
    (z=0). Drones start at cruise altitude (z=3) and descend onto street-level
    landing pads, so they share space and time with ground traffic.
    Drones get higher priority (energy-limited); then ground vehicles."""
    pitch = 6                         # 2-wide street + 4x4 building
    size = blocks * pitch + 2
    depth = 4
    blocked = set()
    for x in range(size):
        for y in range(size):
            on_street = (x % pitch in (0, 1)) or (y % pitch in (0, 1))
            if not on_street:
                for z in range(3):                      # buildings: z=0..2
                    blocked.add((x, y, z))
    world = World(size, size, depth, blocked)
    rng = random.Random(seed)
    streets = [(x, y, 0) for x in range(size) for y in range(size)
               if (x, y, 0) not in blocked]
    sky = [(x, y, 3) for x in range(size) for y in range(size)]
    pads = _distinct(rng, streets, n_air + n_ground)
    gstarts = _distinct(rng, [c for c in streets if c not in pads], n_ground)
    astarts = _distinct(rng, sky, n_air)
    specs: List[AgentSpec] = []
    for s, g in zip(astarts, pads[:n_air]):
        specs.append(AgentSpec(AIR, s, g))
    for s, g in zip(gstarts, pads[n_air:]):
        # make sure drivers have a real trip to make
        specs.append(AgentSpec(GROUND, s, g))
    return world, specs


SCENARIOS = {
    "crossing": crossing,
    "corridor": corridor,
    "open_grid": open_grid,
    "mixed_city": mixed_city,
}
