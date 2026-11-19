"""stc-corridors: decentralized Spatio-Temporal Corridor negotiation (simulation)."""
from .agent import Agent, AgentSpec
from .planner import Constraints, Plan, plan_path
from .protocol import Reservation, ReservationTable, first_conflict
from .scenarios import SCENARIOS
from .sim import Result, SimConfig, run
from .world import AIR, GROUND, World

__all__ = [
    "Agent", "AgentSpec", "Constraints", "Plan", "plan_path", "Reservation",
    "ReservationTable", "first_conflict", "SCENARIOS", "Result", "SimConfig",
    "run", "AIR", "GROUND", "World",
]
__version__ = "0.1.0"
