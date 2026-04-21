from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Choice:
    text: str
    next: str
    condition: dict = field(default_factory=dict)


@dataclass
class StoryNode:
    id: str
    type: str                               # story | combat | event | ending
    title: str
    text: str
    choices: list[Choice] = field(default_factory=list)
    class_text: dict[str, str] = field(default_factory=dict)
    # combat
    combat_id: str = ""
    next_win: str = ""
    next_escape: str = ""
    # event
    event_type: str = ""                    # heal | card_reward | card_reward_cost
    heal_pct: int = 0
    cost_hp_pct: int = 0
    card_pool: list[str] = field(default_factory=list)
    pick_from: int = 3
    # misc
    history_flag: str = ""
    next: str = ""                          # single-exit nodes
