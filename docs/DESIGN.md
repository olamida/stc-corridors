# Design notes

## Model and assumptions

| Item | Choice | Why / consequence |
|---|---|---|
| Space | integer grid `(x, y, z)` | Isolates the *coordination* problem from dynamics. |
| Time | synchronous ticks | Removes clock-sync issues; one move or wait per tick. |
| Ground agents | `z = 0`, 4-connected | Roads, no free-space driving. |
| Air agents | 6-connected, fly above buildings (z = 0..2), cruise at z = 3 | Mixed traffic interacts where drones descend to street-level pads. |
| Goal handling | agent vanishes on arrival | Avoids parking/queueing; simplifies reservation tails. |
| Priority | fixed, by agent index (drones first in `mixed_city`) | Deterministic, deadlock-prone but simple. Fairness is future work. |
| Comms | broadcast to all agents within range; independent Bernoulli loss per (sender, receiver, tick); optional latency | Worst-case-friendly toy model; burst loss is future work. |
| Sensing | an agent can tell if the cell it is about to enter is occupied *now* | Models a bumper/short-range sensor, not intent. |

## Data structures

* `Plan(t0, cells)`: `cells[k]` is the position at absolute time `t0 + k`. A *corridor* is a plan.
* `Reservation(sender, priority, t_sent, t0, cells)`: the first `H + 1` cells of the sender's plan.
* `ReservationTable`: newest reservation per neighbour (by `t_sent`). Expired entries (`t_end < now`) are dropped.
* `Constraints`: `vertex[t] -> {cells}` and `moves = {(t, from, to)}`, built from the table.

## Tick loop (STC mode)

1. **Broadcast.** Each active agent sends its reservation to every agent within range; each link independently drops the message with probability `loss`.
2. **Deliver** (immediately, or after `latency` ticks).
3. **React.** For each agent: if its plan is invalid, or overlaps (vertex or swap) with a reservation from a *higher-priority* agent, re-plan.
4. **Execute** one move. If the next cell is currently occupied (and the occupant's last heard corridor does not say it is leaving), stop and invalidate the plan.
5. **Check** collisions against ground truth, independently of any agent's beliefs.

## Re-planning policy

Tried in order until a plan is found:

1. avoid *all* known corridors, forced first wait (announce-then-act);
2. avoid all known corridors, move immediately;
3. avoid only *higher-priority* corridors (lower-priority agents are expected to yield), forced first wait;
4. as 3, move immediately;
5. hold position and retry next tick (counted as a `plan_failure`).

Steps 3-4 exist because step 1-2 can leave a high-priority agent boxed in by corridors of agents that should be yielding to it.

## Why announce-then-act

Without it, two agents that re-plan in the same tick can each choose a corridor that collides with the other's *on the very next move*, before either has heard the other's new corridor. A forced first wait makes every new corridor visible one tick before it is used. Cost: one tick of delay per re-plan. Measured benefit: see README ablation.

## Why a lookahead window helps under loss

If a conflict occurs `d` ticks in the future and the other agent broadcasts its next `H >= d` cells every tick, there are roughly `d` independent chances to hear it. With independent loss probability `p`, the probability of missing all of them is on the order of `p^d`. The simulation measures how closely real runs follow this intuition (they will not match exactly: re-plans change corridors mid-flight, and priority-yielding needs the *lower*-priority agent to hear).

## Known failure modes

* **Squeeze in a single lane:** an agent between two corridors approaching from opposite sides has no legal move. Hits the 3+3 corridor scenario.
* **Starvation:** fixed priorities.
* **Cascading re-plans:** a yielding agent's new corridor can conflict with a third agent's; resolved over later ticks, costs delay.
* **Unheard higher-priority neighbour:** the lower-priority agent keeps its corridor and only a late message or the sensing stop prevents a collision.

## Natural extensions

1. Replace grid corridors with continuous tubes tracked by MPC with control barrier functions; state the safety property in Signal Temporal Logic and verify it at runtime.
2. Acknowledged reservations (two-phase commit) as an alternative to pure broadcast; measure the bandwidth vs safety trade-off.
3. Dynamic / age-based priority and deadlock detection.
4. Bursty, range-dependent communication models.
5. Port the protocol to ROS 2 nodes and run it in Gazebo.
