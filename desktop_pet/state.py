from __future__ import annotations

from dataclasses import dataclass


EDGES = ("top", "right", "bottom", "left")


@dataclass
class PetState:
    edge: str = "right"
    offset: int = 0
    direction: int = 1
    mood: str = "idle"
    paused: bool = False
    dragging: bool = False
    message: str = "今天也要巡逻。"
    move_tick: int = 0

    def next_edge(self) -> str:
        index = EDGES.index(self.edge)
        return EDGES[(index + self.direction) % len(EDGES)]
