from __future__ import annotations
import json
import os

_config_path = os.path.join(os.path.dirname(__file__), "..", "config.json")
with open(_config_path, encoding="utf-8") as f:
    _config = json.load(f)

STAT_LABELS = _config["stat_labels"]

_STATUS_NAMES = {
    "stun": "暈眩", "fear": "恐懼", "curse": "詛咒",
    "block": "護盾", "ward": "結界", "evade": "迴避",
    "burn": "燃燒", "duty_bonus": "蓄力",
}


class Character:
    name: str = ""
    title: str = ""
    description: str = ""
    char_key: str = ""
    base_deck_ids: list[str] = []
    escape_stat: str = "luck"

    def __init__(self) -> None:
        raw = _config["characters"][self.char_key]
        self.stats = dict(raw)
        self.current_hp = self.stats["hp"]
        self.deck_ids = list(self.base_deck_ids)
        self.statuses: dict[str, dict] = {}

    # ── 狀態系統 ──────────────────────────────────────────────

    def apply_status_raw(self, name: str, value: int, extra: dict | None = None) -> None:
        extra = extra or {}
        if name in ("block", "ward"):
            if name in self.statuses:
                self.statuses[name]["value"] += value
            else:
                self.statuses[name] = {"value": value}
        elif name == "evade":
            if "evade" in self.statuses:
                self.statuses["evade"]["stacks"] += value
            else:
                self.statuses["evade"] = {"stacks": value}
        elif name == "burn":
            if "burn" in self.statuses:
                self.statuses["burn"]["damage"] = max(self.statuses["burn"]["damage"], value)
                self.statuses["burn"]["turns"] += extra.get("turns", 2)
            else:
                self.statuses["burn"] = {"damage": value, "turns": extra.get("turns", 2)}
        elif name == "duty_bonus":
            self.statuses["duty_bonus"] = {"multiplier": value / 100.0, "uses": 1}
        else:
            if name in self.statuses:
                self.statuses[name]["turns"] = max(self.statuses[name].get("turns", 0), value)
            else:
                self.statuses[name] = {"turns": value}

    def receive_damage(self, amount: int, true_damage: bool = False) -> tuple[int, list[str]]:
        msgs: list[str] = []
        if amount <= 0:
            return 0, msgs

        # 迴避（僅物理）
        if not true_damage and "evade" in self.statuses:
            self.statuses["evade"]["stacks"] -= 1
            if self.statuses["evade"]["stacks"] <= 0:
                del self.statuses["evade"]
            return 0, ["閃避！攻擊落空。"]

        # 詛咒加深傷害
        if "curse" in self.statuses:
            amount = int(amount * 1.2)
            msgs.append("詛咒加深傷害！")

        if true_damage:
            # 結界吸收真實傷害
            if "ward" in self.statuses:
                absorbed = min(self.statuses["ward"]["value"], amount)
                amount -= absorbed
                self.statuses["ward"]["value"] -= absorbed
                if self.statuses["ward"]["value"] <= 0:
                    del self.statuses["ward"]
                if absorbed > 0:
                    msgs.append(f"結界吸收 {absorbed} 點真實傷害。")
        else:
            # 生存減傷
            reduction = self.stats["survival"] / 100
            amount = max(1, int(amount * (1 - reduction)))
            # 護盾吸收物理傷害
            if "block" in self.statuses:
                absorbed = min(self.statuses["block"]["value"], amount)
                amount -= absorbed
                self.statuses["block"]["value"] -= absorbed
                if self.statuses["block"]["value"] <= 0:
                    del self.statuses["block"]
                if absorbed > 0:
                    msgs.append(f"護盾吸收 {absorbed} 點傷害。")

        self.current_hp = max(0, self.current_hp - amount)
        return amount, msgs

    def tick_start_of_turn(self) -> list[str]:
        msgs: list[str] = []
        if "burn" in self.statuses:
            burn = self.statuses["burn"]
            self.current_hp = max(0, self.current_hp - burn["damage"])
            msgs.append(f"燃燒傷害！受到 {burn['damage']} 點真實傷害。")
            burn["turns"] -= 1
            if burn["turns"] <= 0:
                del self.statuses["burn"]
                msgs.append("燃燒效果消除。")
        for name in ("stun", "fear", "curse"):
            if name in self.statuses:
                self.statuses[name]["turns"] -= 1
                if self.statuses[name]["turns"] <= 0:
                    del self.statuses[name]
                    msgs.append(f"{_STATUS_NAMES[name]}效果消除。")
        return msgs

    def status_display(self) -> str:
        if not self.statuses:
            return ""
        parts = []
        for k, v in self.statuses.items():
            label = _STATUS_NAMES.get(k, k)
            if k in ("block", "ward"):
                parts.append(f"[{label}:{v['value']}]")
            elif k == "evade":
                parts.append(f"[{label}:{v['stacks']}層]")
            elif k == "burn":
                parts.append(f"[{label}:{v['damage']}×{v['turns']}回]")
            elif k == "duty_bonus":
                parts.append(f"[{label}]")
            else:
                parts.append(f"[{label}:{v['turns']}回]")
        return " ".join(parts)

    # ── 治療 ──────────────────────────────────────────────────

    def heal(self, amount: int) -> int:
        before = self.current_hp
        self.current_hp = min(self.stats["hp"], self.current_hp + amount)
        return self.current_hp - before

    # ── 查詢 ──────────────────────────────────────────────────

    def is_alive(self) -> bool:
        return self.current_hp > 0

    def stat(self, key: str) -> int:
        return self.stats.get(key, 0)

    # ── 顯示 ──────────────────────────────────────────────────

    def status_line(self) -> str:
        hp_bar = self._hp_bar()
        stats_str = "  ".join(
            f"{STAT_LABELS[k]}:{self.stats[k]}"
            for k in ("survival", "luck", "social", "spirit", "strength")
        )
        return f"【{self.name}·{self.title}】  {hp_bar}  {stats_str}"

    def _hp_bar(self, width: int = 10) -> str:
        ratio = self.current_hp / self.stats["hp"]
        filled = round(ratio * width)
        bar = "█" * filled + "░" * (width - filled)
        return f"生命 [{bar}] {self.current_hp}/{self.stats['hp']}"

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} hp={self.current_hp}/{self.stats['hp']}>"
