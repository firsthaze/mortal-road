from __future__ import annotations
import random
from dataclasses import dataclass, field


@dataclass
class EnemyAction:
    label: str
    damage: int = 0
    true_damage: int = 0
    self_block: int = 0
    self_heal: int = 0
    status_name: str = ""
    status_value: int = 0
    status_extra: dict = field(default_factory=dict)

    def intent_str(self) -> str:
        parts = []
        if self.damage:
            parts.append(f"攻擊 {self.damage}")
        if self.true_damage:
            parts.append(f"真實傷害 {self.true_damage}")
        if self.self_block:
            parts.append(f"防禦 {self.self_block}")
        if self.self_heal:
            parts.append(f"回血 {self.self_heal}")
        if self.status_name:
            from characters.base import _STATUS_NAMES
            parts.append(f"施加{_STATUS_NAMES.get(self.status_name, self.status_name)}")
        return self.label + "（" + "，".join(parts) + "）" if parts else self.label


_STATUS_NAMES_LOCAL = {
    "stun": "暈眩", "fear": "恐懼", "curse": "詛咒",
    "block": "護盾", "ward": "結界", "evade": "迴避",
    "burn": "燃燒",
}

ENEMY_TEMPLATES: dict[str, dict] = {
    "drunk": {
        "name": "醉漢",
        "flavor": "搖搖晃晃，手握破酒壺，滿身酒氣。",
        "hp": 40, "strength": 12, "survival": 5, "spirit": 0, "social": 0,
        "ai": "simple",
    },
    "bandit": {
        "name": "山賊",
        "flavor": "橫刀立馬，凶神惡煞，攔路劫財。",
        "hp": 65, "strength": 18, "survival": 10, "spirit": 5, "social": 8,
        "ai": "normal",
    },
    "guard": {
        "name": "官兵",
        "flavor": "身著甲冑，手持長刀，奉命緝拿。",
        "hp": 85, "strength": 22, "survival": 20, "spirit": 5, "social": 15,
        "ai": "normal",
    },
    "sorcerer": {
        "name": "邪術師",
        "flavor": "面色蒼白，眼神詭異，周身縈繞著黑色靈氣。",
        "hp": 55, "strength": 8, "survival": 8, "spirit": 30, "social": 15,
        "ai": "advanced",
    },
    "wandering_master": {
        "name": "江湖散人",
        "flavor": "衣衫隨意，眼神銳利，一身功夫深藏不露。",
        "hp": 75, "strength": 25, "survival": 18, "spirit": 20, "social": 15,
        "ai": "advanced",
    },
    "cult_enforcer": {
        "name": "邪教護法",
        "flavor": "身披黑袍，手持鐵鏈，是幕後勢力派來的爪牙。",
        "hp": 80, "strength": 28, "survival": 15, "spirit": 18, "social": 10,
        "ai": "normal",
    },
    "heavenly_schemer": {
        "name": "天機老人",
        "flavor": "鶴髮童顏，眼中藏著千算萬計，微笑之間已布下天羅地網。",
        "hp": 70, "strength": 6, "survival": 12, "spirit": 35, "social": 28,
        "ai": "boss_schemer",
    },
    "phantom_assassin": {
        "name": "幽靈刺客",
        "flavor": "身形如煙，來去無蹤，刀光閃過之處只剩一道血痕。",
        "hp": 60, "strength": 30, "survival": 8, "spirit": 12, "social": 5,
        "ai": "boss_assassin",
    },
    "blood_shaman": {
        "name": "血魔祭司",
        "flavor": "以血為祭，以痛為禱，每一次呼吸都伴隨著詭異的低鳴。",
        "hp": 90, "strength": 15, "survival": 20, "spirit": 25, "social": 5,
        "ai": "boss_shaman",
    },
}


class Enemy:
    def __init__(self, template_id: str, difficulty_cfg: dict) -> None:
        tmpl = ENEMY_TEMPLATES[template_id]
        self.id = template_id
        self.name: str = tmpl["name"]
        self.flavor: str = tmpl["flavor"]
        self.ai_level: str = tmpl["ai"]

        hp_mult = difficulty_cfg.get("enemy_hp_multiplier", 1.0)
        self.stats = {
            "hp":       int(tmpl["hp"] * hp_mult),
            "strength": tmpl["strength"],
            "survival": tmpl["survival"],
            "spirit":   tmpl["spirit"],
            "social":   tmpl["social"],
        }
        self.current_hp: int = self.stats["hp"]
        self.statuses: dict[str, dict] = {}
        self._dmg_mult: float = difficulty_cfg.get("enemy_damage_multiplier", 1.0)
        self._turn_count: int = 0
        self._next_action: EnemyAction | None = None

    # ── 傷害計算 ──────────────────────────────────────────────

    def _phys(self, base: int = 8, mult: float = 0.45) -> int:
        return max(1, int((base + self.stats["strength"] * mult) * self._dmg_mult))

    def _true(self, base: int = 6, mult: float = 0.45) -> int:
        return max(1, int((base + self.stats["spirit"] * mult) * self._dmg_mult))

    def _blk(self) -> int:
        return 6 + int(self.stats["survival"] * 0.4)

    # ── AI 選擇行動 ────────────────────────────────────────────

    def select_action(self, player) -> EnemyAction:
        ai = self.ai_level
        if ai == "simple":
            action = self._ai_simple()
        elif ai == "normal":
            action = self._ai_normal()
        elif ai == "boss_schemer":
            action = self._ai_boss_schemer(player)
        elif ai == "boss_assassin":
            action = self._ai_boss_assassin(player)
        elif ai == "boss_shaman":
            action = self._ai_boss_shaman(player)
        else:
            action = self._ai_advanced(player)
        self._next_action = action
        return action

    def _ai_simple(self) -> EnemyAction:
        dmg = self._phys()
        return EnemyAction("搖晃揮拳", damage=dmg)

    def _ai_normal(self) -> EnemyAction:
        t = self._turn_count % 4
        if self.id == "bandit":
            patterns = [
                EnemyAction("刀劈", damage=self._phys()),
                EnemyAction("連環砍", damage=int(self._phys() * 0.6) * 2),
                EnemyAction("舉盾防禦", self_block=self._blk()),
                EnemyAction("恐嚇", status_name="fear", status_value=1),
            ]
        else:  # guard
            patterns = [
                EnemyAction("官刀斬擊", damage=self._phys()),
                EnemyAction("持盾格擋", self_block=self._blk()),
                EnemyAction("重力一斬", damage=int(self._phys(mult=0.8))),
                EnemyAction("官刀斬擊", damage=self._phys()),
            ]
        return patterns[t]

    def _ai_advanced(self, player) -> EnemyAction:
        hp_ratio = self.current_hp / self.stats["hp"]
        has_evade = "evade" in player.statuses
        t = self._turn_count % 4

        if hp_ratio < 0.35:
            # 低血爆發：連續詛咒+真實傷害
            if t % 2 == 0:
                return EnemyAction("業火詛咒", status_name="burn",
                                   status_value=5, status_extra={"turns": 3})
            return EnemyAction("魂魄衝擊", true_damage=self._true(mult=0.6))

        if has_evade:
            return EnemyAction("穿透術法", true_damage=self._true())

        patterns = [
            EnemyAction("靈魂衝擊", true_damage=self._true()),
            EnemyAction("詛咒封印", status_name="curse", status_value=2),
            EnemyAction("靈氣護體", self_block=self._blk()),
            EnemyAction("業火詛咒", status_name="burn",
                        status_value=4, status_extra={"turns": 2}),
        ]
        return patterns[t]

    def _ai_boss_schemer(self, player) -> EnemyAction:
        """天機老人：詛咒疊加型。奇數回合疊詛咒封印，偶數回合按詛咒層數蓄力打擊。"""
        t = self._turn_count
        hp_ratio = self.current_hp / self.stats["hp"]
        if hp_ratio < 0.4:
            # 低血：連續施壓，詛咒+真實傷害同時
            return EnemyAction("天羅地網", status_name="curse", status_value=2,
                               true_damage=self._true(base=8, mult=0.5))
        if t % 3 == 0:
            return EnemyAction("封印術", status_name="curse", status_value=2)
        if t % 3 == 1:
            curse_stacks = player.statuses.get("curse", {}).get("turns", 0)
            bonus = curse_stacks * 3
            return EnemyAction("算計一擊", true_damage=self._true() + bonus)
        return EnemyAction("靈氣護體", self_block=self._blk() + 5)

    def _ai_boss_assassin(self, player) -> EnemyAction:
        """幽靈刺客：閃避+爆發型。偶數回合積累迴避，奇數回合爆發高傷害。"""
        t = self._turn_count
        hp_ratio = self.current_hp / self.stats["hp"]
        if hp_ratio < 0.35:
            # 低血爆發：無視一切直接斬
            return EnemyAction("必殺刺·決死", damage=self._phys(base=20, mult=0.9))
        if t % 4 == 0:
            return EnemyAction("隱入虛影", self_block=8,
                               status_name="evade", status_value=2)
        if t % 4 == 1:
            return EnemyAction("幻影連斬", damage=self._phys(base=6, mult=0.5),
                               status_name="stun", status_value=1)
        if t % 4 == 2:
            return EnemyAction("穿心一刺", damage=self._phys(base=18, mult=0.8))
        return EnemyAction("殘影突刺", damage=self._phys(base=8, mult=0.4),
                           true_damage=self._true(base=4, mult=0.3))

    def _ai_boss_shaman(self, player) -> EnemyAction:
        """血魔祭司：血祭回血型。定期獻血自回，同時燃燒玩家，越傷越強。"""
        t = self._turn_count
        hp_ratio = self.current_hp / self.stats["hp"]
        if t % 5 == 0:
            heal_amt = int(self.stats["hp"] * 0.12)
            return EnemyAction("血祭儀式", self_heal=heal_amt,
                               status_name="burn", status_value=4,
                               status_extra={"turns": 2})
        if t % 5 == 1:
            return EnemyAction("腐血詛咒", status_name="curse", status_value=2,
                               true_damage=self._true(base=4, mult=0.3))
        if t % 5 == 2:
            return EnemyAction("血爪撕裂", damage=self._phys(base=10, mult=0.55))
        if t % 5 == 3:
            heal_amt = int(self.stats["hp"] * 0.08) if hp_ratio < 0.5 else 0
            return EnemyAction("噬血強化", damage=self._phys(base=8, mult=0.4),
                               self_heal=heal_amt)
        return EnemyAction("業火燎燒", status_name="burn", status_value=5,
                           status_extra={"turns": 3})

    # ── 執行行動 ──────────────────────────────────────────────

    def execute_action(self) -> EnemyAction:
        action = self._next_action or self._ai_simple()
        self._turn_count += 1
        if action.self_block:
            self.apply_status_raw("block", action.self_block)
        if action.self_heal:
            self.current_hp = min(self.stats["hp"], self.current_hp + action.self_heal)
        return action

    # ── 狀態系統（與 Character 一致） ─────────────────────────

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
        else:
            if name in self.statuses:
                self.statuses[name]["turns"] = max(self.statuses[name].get("turns", 0), value)
            else:
                self.statuses[name] = {"turns": value}

    def receive_damage(self, amount: int, true_damage: bool = False) -> tuple[int, list[str]]:
        msgs: list[str] = []
        if amount <= 0:
            return 0, msgs
        if "curse" in self.statuses:
            amount = int(amount * 1.2)
            msgs.append("詛咒加深傷害！")
        if true_damage:
            if "ward" in self.statuses:
                absorbed = min(self.statuses["ward"]["value"], amount)
                amount -= absorbed
                self.statuses["ward"]["value"] -= absorbed
                if self.statuses["ward"]["value"] <= 0:
                    del self.statuses["ward"]
        else:
            reduction = self.stats["survival"] / 100
            amount = max(1, int(amount * (1 - reduction)))
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
            msgs.append(f"【{self.name}】燃燒受到 {burn['damage']} 點傷害。")
            burn["turns"] -= 1
            if burn["turns"] <= 0:
                del self.statuses["burn"]
        for name in ("stun", "fear", "curse"):
            if name in self.statuses:
                self.statuses[name]["turns"] -= 1
                if self.statuses[name]["turns"] <= 0:
                    del self.statuses[name]
        return msgs

    def is_alive(self) -> bool:
        return self.current_hp > 0

    def status_display(self) -> str:
        if not self.statuses:
            return ""
        parts = []
        for k, v in self.statuses.items():
            label = _STATUS_NAMES_LOCAL.get(k, k)
            if k in ("block", "ward"):
                parts.append(f"[{label}:{v['value']}]")
            elif k == "evade":
                parts.append(f"[{label}:{v['stacks']}層]")
            elif k == "burn":
                parts.append(f"[{label}:{v['damage']}×{v['turns']}回]")
            else:
                parts.append(f"[{label}:{v['turns']}回]")
        return " ".join(parts)

    def _hp_bar(self, width: int = 10) -> str:
        ratio = self.current_hp / self.stats["hp"]
        filled = round(ratio * width)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}] {self.current_hp}/{self.stats['hp']}"

    def __repr__(self) -> str:
        return f"<Enemy {self.name} hp={self.current_hp}/{self.stats['hp']}>"


def build_enemy(enemy_id: str, difficulty_cfg: dict) -> "Enemy":
    if enemy_id not in ENEMY_TEMPLATES:
        raise ValueError(f"未知敵人：{enemy_id}")
    return Enemy(enemy_id, difficulty_cfg)


BOSS_POOL = ["heavenly_schemer", "phantom_assassin", "blood_shaman", "sorcerer"]
ENEMY_POOL = list(ENEMY_TEMPLATES.keys())
