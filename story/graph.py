from __future__ import annotations
import json
import os
import random

from .node import StoryNode, Choice

_DATA_PATH = os.path.join(os.path.dirname(__file__), "nodes.json")


class StoryGraph:
    def __init__(self) -> None:
        with open(_DATA_PATH, encoding="utf-8") as f:
            data = json.load(f)
        self.acts: dict[str, list[str]] = data["acts"]
        self.nodes: dict[str, StoryNode] = {
            nid: self._parse(nid, nd)
            for nid, nd in data["nodes"].items()
        }

    def _parse(self, nid: str, d: dict) -> StoryNode:
        choices = [
            Choice(text=c["text"], next=c.get("next", ""), condition=c.get("condition", {}))
            for c in d.get("choices", [])
        ]
        return StoryNode(
            id=nid,
            type=d.get("type", "story"),
            title=d.get("title", ""),
            text=d.get("text", ""),
            choices=choices,
            class_text=d.get("class_text", {}),
            combat_id=d.get("combat_id", ""),
            next_win=d.get("next_win", ""),
            next_escape=d.get("next_escape", ""),
            event_type=d.get("event_type", ""),
            heal_pct=d.get("heal_pct", 0),
            cost_hp_pct=d.get("cost_hp_pct", 0),
            card_pool=d.get("card_pool", []),
            pick_from=d.get("pick_from", 3),
            history_flag=d.get("history_flag", ""),
            next=d.get("next", ""),
        )

    def get(self, node_id: str) -> StoryNode:
        if node_id not in self.nodes:
            raise KeyError(f"未知節點：{node_id}")
        return self.nodes[node_id]

    def pick_act(self, act: str) -> str:
        options = self.acts.get(act, [])
        return random.choice(options) if options else ""
