from __future__ import annotations
import random
import time

from combat import Battle, BattleOutcome, build_enemy
from combat.card import build_card, ADVANCED_CARD_POOL, CLASS_EVENT_POOL
from combat.deck import Deck
from combat.enemy import BOSS_POOL
from characters.base import STAT_LABELS
from .graph import StoryGraph
from .node import StoryNode
from .endings import ENDINGS, determine_ending

W = 52


# ── 顯示工具 ──────────────────────────────────────────────────────

def _div(c: str = "─") -> None:
    print(c * W)

def _p(text: str = "") -> None:
    print(text)

def _typewrite(text: str, delay: float = 0.025) -> None:
    for ch in text:
        print(ch, end="", flush=True)
        time.sleep(delay)
    print()

def _pause(sec: float = 0.8) -> None:
    time.sleep(sec)

def _clear() -> None:
    print("\n" * 2)

def _banner(title: str) -> None:
    _clear()
    _div("═")
    _p(f"  ◆ {title}")
    _div("═")

def _wait() -> None:
    input("\n  ──（按 Enter 繼續）──\n")


# ── 條件判斷 ──────────────────────────────────────────────────────

def _check_condition(condition: dict, character) -> bool:
    if not condition:
        return True
    if "class" in condition:
        cls = condition["class"]
        if isinstance(cls, list):
            return character.char_key in cls
        return character.char_key == cls
    if "stat" in condition:
        return character.stat(condition["stat"]) >= condition.get("min", 0)
    return True


# ── 主引擎 ────────────────────────────────────────────────────────

class StoryEngine:
    def __init__(self, character, difficulty_cfg: dict, hand_size: int = 5, base_energy: int = 3) -> None:
        self.character = character
        self.difficulty_cfg = difficulty_cfg
        self.hand_size = hand_size
        self.base_energy = base_energy
        self.graph = StoryGraph()
        self.deck = Deck(character.deck_ids)
        self.history: list[str] = []
        self._battle_count = 0
        self.boss_id = random.choice(BOSS_POOL)

    def run(self) -> None:
        self._go("start")

    # ── 導航 ──────────────────────────────────────────────────────

    def _go(self, node_id: str) -> None:
        node_id = self._resolve(node_id)
        while node_id:
            node = self.graph.get(node_id)
            node_id = self._process(node)

    def _resolve(self, node_id: str) -> str:
        for act in ("act1", "act2", "act3", "act4", "act5", "act6",
                    "act7", "act8", "act9", "act10", "act11", "act12"):
            if node_id == f"__{act}__":
                chosen = self.graph.pick_act(act)
                self.history.append(f"{act}:{chosen}")
                return chosen
        if node_id == "__ending__":
            ending_id = determine_ending(self.character, self.history)
            return ending_id
        if node_id == "__sacrifice__":
            return "ending_sacrifice"
        if node_id == "__final_boss__":
            return "act12_final_boss"
        return node_id

    def _process(self, node: StoryNode) -> str | None:
        if node.history_flag:
            self.history.append(node.history_flag)

        if node.type == "story":
            return self._handle_story(node)
        if node.type == "combat":
            return self._handle_combat(node)
        if node.type == "event":
            return self._handle_event(node)
        if node.type == "ending":
            self._handle_ending(node)
            return None
        return None

    # ── 故事節點 ──────────────────────────────────────────────────

    def _handle_story(self, node: StoryNode) -> str:
        _banner(node.title)

        # 主文字（替換 {name} 為旅者姓名）
        text = node.class_text.get(self.character.char_key, node.text)
        text = text.replace("{name}", self.character.traveler_name)
        _typewrite(f"\n  {text.replace(chr(10), chr(10) + '  ')}\n")
        _pause(0.3)

        # 過濾可用選項
        available = [c for c in node.choices if _check_condition(c.condition, self.character)]

        if not available:
            _wait()
            return self._resolve(node.next) if node.next else None

        # 顯示選項
        _div()
        for i, choice in enumerate(available, 1):
            _p(f"  [{i}] {choice.text}{self._choice_hint(choice.condition)}")
        _p("  [v] 查看屬性   [d] 查看牌庫")
        _div()

        while True:
            raw = input("  選擇：").strip().lower()
            if raw == "v":
                _clear()
                _p(self.character.detail_display())
                _wait()
                _banner(node.title)
                _typewrite(f"\n  {text.replace(chr(10), chr(10) + '  ')}\n")
                _div()
                for i, choice in enumerate(available, 1):
                    _p(f"  [{i}] {choice.text}{self._choice_hint(choice.condition)}")
                _p("  [v] 查看屬性   [d] 查看牌庫")
                _div()
                continue
            if raw == "d":
                _clear()
                _div("═")
                _p(f"  ◆ 牌庫（共 {len(self.deck.all_cards)} 張）")
                _div()
                for card in self.deck.all_cards:
                    _p(f"  ・{card.name}（{card.cost}能）── {card.description}")
                _div("═")
                _wait()
                _banner(node.title)
                _typewrite(f"\n  {text.replace(chr(10), chr(10) + '  ')}\n")
                _div()
                for i, choice in enumerate(available, 1):
                    _p(f"  [{i}] {choice.text}{self._choice_hint(choice.condition)}")
                _p("  [v] 查看屬性   [d] 查看牌庫")
                _div()
                continue
            if raw.isdigit() and 1 <= int(raw) <= len(available):
                chosen = available[int(raw) - 1]
                if chosen.next == "ending_escape":
                    self.history.append("chose_escape")
                return self._resolve(chosen.next)
            _p("  請輸入有效的數字。")

    # ── 戰鬥節點 ──────────────────────────────────────────────────

    def _handle_combat(self, node: StoryNode) -> str:
        self._battle_count += 1
        combat_id = self.boss_id if node.combat_id == "__final_boss__" else node.combat_id
        enemy = build_enemy(combat_id, self.difficulty_cfg)

        battle = Battle(
            self.character, enemy,
            hand_size=self.hand_size,
            base_energy=self.base_energy,
        )
        battle.deck = self.deck  # 複用同一副牌庫（保留進階牌）

        outcome = battle.run()

        self.deck = battle.deck
        self.deck.end_turn()

        if outcome == BattleOutcome.WIN:
            return self._resolve(node.next_win or "__ending__")
        if outcome == BattleOutcome.ESCAPE:
            self.history.append("escaped_battle")
            return self._resolve(node.next_escape or "__act2__")
        # LOSE
        return "__sacrifice__"

    # ── 事件節點 ──────────────────────────────────────────────────

    def _handle_event(self, node: StoryNode) -> str:
        _banner(node.title)
        event_text = node.text.replace("{name}", self.character.traveler_name)
        _typewrite(f"\n  {event_text}\n")

        et = node.event_type

        if et == "heal":
            amt = int(self.character.stats["hp"] * node.heal_pct / 100)
            restored = self.character.heal(amt)
            _p(f"\n  恢復了 {restored} 點生命。")
            _p(f"  當前生命：{self.character.current_hp}/{self.character.stats['hp']}")
            _wait()

        elif et in ("card_reward", "card_reward_cost"):
            if et == "card_reward_cost":
                cost = int(self.character.stats["hp"] * node.cost_hp_pct / 100)
                # 直接扣血，穿透護盾與結界
                self.character.current_hp = max(0, self.character.current_hp - cost)
                _p(f"\n  你付出了 {cost} 點生命作為代價。（生命 {self.character.current_hp}/{self.character.stats['hp']}）")
                _pause(0.5)
                if not self.character.is_alive():
                    return "__sacrifice__"

            class_pool = CLASS_EVENT_POOL.get(self.character.char_key, ADVANCED_CARD_POOL)
            pool = class_pool
            sample = random.sample(pool, min(node.pick_from, len(pool)))
            cards = [build_card(cid) for cid in sample]

            _p("\n  請從以下牌中選擇一張加入牌庫：")
            _div()
            for i, card in enumerate(cards, 1):
                _p(f"  [{i}] {card.name}（{card.cost} 能）── {card.description}")
            _div()

            while True:
                raw = input("  選擇：").strip()
                if raw.isdigit() and 1 <= int(raw) <= len(cards):
                    chosen = cards[int(raw) - 1]
                    self.deck.add_card(chosen.id)
                    _p(f"\n  ✦ 【{chosen.name}】加入了你的牌庫。")
                    _pause(0.8)
                    break
                _p("  請輸入有效的數字。")

        return self._resolve(node.next or "__act7__")

    # ── 結局節點 ──────────────────────────────────────────────────

    def _handle_ending(self, node: StoryNode) -> None:
        ending = ENDINGS.get(node.id, {})
        title = ending.get("title", node.title)
        text = ending.get("text", node.text)

        _clear()
        _div("═")
        _p(f"\n  ══  {title}  ══\n")
        _div("═")
        _pause(0.5)

        for line in text.split("\n"):
            _typewrite(f"  {line}", delay=0.03)
            _pause(0.05)

        _p()
        _div()
        self._show_stats()
        _div("═")
        _wait()

    def _show_stats(self) -> None:
        c = self.character
        hp_ratio = c.current_hp / c.stats["hp"]
        hp_pct = int(hp_ratio * 100)
        _p(f"  旅者：{c.traveler_name}  【{c.name}·{c.title}】")
        _p(f"  最終生命：{c.current_hp}/{c.stats['hp']}（{hp_pct}%）")
        _p(f"  歷經戰鬥：{self._battle_count} 場")
        _p(f"  牌庫張數：{len(self.deck.all_cards)} 張")
        cards_str = "、".join(
            card.name for card in self.deck.all_cards
            if card.id not in ("strike", "dodge", "block")
        )
        if cards_str:
            _p(f"  取得進階牌：{cards_str}")

    def _choice_hint(self, cond: dict) -> str:
        if not cond:
            return ""
        if cond.get("class"):
            return f"（{self.character.name}專屬）"
        if cond.get("stat"):
            key = cond["stat"]
            req = cond["min"]
            cur = self.character.stat(key)
            label = STAT_LABELS.get(key, key)
            return f"（{label}≥{req}，你：{cur}）"
        return ""
