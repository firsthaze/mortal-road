from __future__ import annotations
import json
import os
import random
import select
import sys
import time
from enum import Enum

from .card import Card, CardEffect
from .deck import Deck
from .enemy import Enemy, EnemyAction

_config_path = os.path.join(os.path.dirname(__file__), "..", "config.json")
with open(_config_path, encoding="utf-8") as f:
    _cfg = json.load(f)


class BattleOutcome(Enum):
    WIN = "win"
    LOSE = "lose"
    ESCAPE = "escape"


# ── ANSI 顏色 ─────────────────────────────────────────────────

class _C:
    RED     = "\033[91m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    MAGENTA = "\033[95m"
    CYAN    = "\033[96m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    RESET   = "\033[0m"


# ── 顯示輔助 ──────────────────────────────────────────────────

W = 52

def _div(c: str = "─") -> None:
    print(c * W)

def _p(text: str = "") -> None:
    print(text)

def _pause(sec: float = 0.6) -> None:
    time.sleep(sec)

def _timed_pause(sec: float) -> None:
    """等待 sec 秒，或使用者按 Enter 立即跳過。"""
    print(f"  {_C.DIM}（按 Enter 立即繼續…）{_C.RESET}", end="\r", flush=True)
    try:
        rlist, _, _ = select.select([sys.stdin], [], [], sec)
        if rlist:
            sys.stdin.readline()
    except (OSError, ValueError):
        time.sleep(sec)
    print(" " * 30, end="\r", flush=True)

def _typewrite(text: str, delay: float = 0.018) -> None:
    for ch in text:
        print(ch, end="", flush=True)
        time.sleep(delay)
    print()

def _energy_bar(cur: int, max_e: int) -> str:
    return _C.YELLOW + "■" * cur + _C.DIM + "□" * (max_e - cur) + _C.RESET + f"  ({cur}/{max_e})"

def _clear() -> None:
    print("\n" * 3)


# ── 效果結果顯示 ──────────────────────────────────────────────

_STATUS_EFFECT_DESC = {
    "stun":  "暈眩，下回合無法行動",
    "fear":  "恐懼，攻擊傷害降低25%",
    "curse": "詛咒，所受傷害增加20%",
    "burn":  "燃燒，每回合受到真實傷害",
}

def _damage_result_line(target) -> str:
    name = getattr(target, "name", "目標")
    hp = target.current_hp
    max_hp = target.stats["hp"]
    shield = target.statuses.get("block", {}).get("value", 0)
    if shield > 0:
        return f"  {_C.DIM}→ {name} 生命 {hp}/{max_hp}，護盾剩餘 {shield}{_C.RESET}"
    return f"  {_C.DIM}→ {name} 生命剩餘 {hp}/{max_hp}{_C.RESET}"

def _status_applied_line(name: str, value: int) -> str:
    desc = _STATUS_EFFECT_DESC.get(name, name)
    if name == "burn":
        return f"  {_C.MAGENTA}→ 施加【{desc}】（每回合 {value} 傷）{_C.RESET}"
    return f"  {_C.MAGENTA}→ 施加【{desc}】（{value} 回合）{_C.RESET}"


# ── 卡牌效果應用 ───────────────────────────────────────────────

def _apply_effect_wrap(effect: CardEffect, user, target, deck: Deck) -> tuple[int, bool, bool]:
    """回傳 (extra_energy, instant_win, had_extra_draw)"""
    phys = effect.damage
    if phys > 0 and "duty_bonus" in user.statuses:
        mult = user.statuses["duty_bonus"]["multiplier"]
        phys = int(phys * mult)
        user.statuses["duty_bonus"]["uses"] -= 1
        if user.statuses["duty_bonus"]["uses"] <= 0:
            del user.statuses["duty_bonus"]

    if phys > 0:
        _, msgs = target.receive_damage(phys, true_damage=False)
        for m in msgs:
            _typewrite(f"  {m}")
        _typewrite(_damage_result_line(target))
    if effect.true_damage > 0:
        _, msgs = target.receive_damage(effect.true_damage, true_damage=True)
        for m in msgs:
            _typewrite(f"  {m}")
        _typewrite(_damage_result_line(target))
    if effect.self_damage > 0:
        user.receive_damage(effect.self_damage, true_damage=True)
        _typewrite(f"  自身受到 {effect.self_damage} 點反傷。")
        _typewrite(_damage_result_line(user))
    if effect.healing > 0:
        restored = user.heal(effect.healing)
        if restored > 0:
            _typewrite(f"  {_C.GREEN}恢復 {restored} 點生命。（生命 {user.current_hp}/{user.stats['hp']}）{_C.RESET}")
    if effect.self_block > 0:
        user.apply_status_raw("block", effect.self_block)
        total = user.statuses.get("block", {}).get("value", effect.self_block)
        _typewrite(f"  {_C.CYAN}護盾 {total} 點。{_C.RESET}")
    if effect.self_ward > 0:
        user.apply_status_raw("ward", effect.self_ward)
        total = user.statuses.get("ward", {}).get("value", effect.self_ward)
        _typewrite(f"  {_C.CYAN}結界 {total} 點。{_C.RESET}")
    for sa in effect.target_statuses:
        target.apply_status_raw(sa.name, sa.value, sa.extra)
        _typewrite(_status_applied_line(sa.name, sa.value))
    for sa in effect.self_statuses:
        user.apply_status_raw(sa.name, sa.value, sa.extra)
        _typewrite(_status_applied_line(sa.name, sa.value))

    had_extra_draw = effect.extra_draw > 0
    if had_extra_draw:
        drawn = deck.draw(effect.extra_draw)
        if drawn:
            names = "、".join(c.name for c in drawn)
            _typewrite(f"  {_C.CYAN}額外抽牌：{names}{_C.RESET}")
    return effect.extra_energy, effect.instant_win, had_extra_draw


# ── 逃跑判定 ──────────────────────────────────────────────────

def _escape_roll(character) -> bool:
    stat_val = character.stat(character.escape_stat)
    threshold = min(30 + stat_val * 0.6, 80)
    return random.random() * 100 < threshold


# ── 自動結束判定 ──────────────────────────────────────────────

def _no_playable_cards(hand: list[Card], energy: int) -> bool:
    """手牌中已無任何可出的牌。"""
    return all(c.cost > energy for c in hand)


# ── 戰鬥畫面 ──────────────────────────────────────────────────

def _render(character, enemy: Enemy, deck: Deck, energy: int, max_energy: int) -> None:
    _clear()
    print(_C.BOLD + "═" * W + _C.RESET)
    intent_str = enemy._next_action.intent_str() if enemy._next_action else "？？？"
    st = enemy.status_display()
    print(f"  {_C.RED}{_C.BOLD}【{enemy.name}】{_C.RESET}  {_C.YELLOW}{enemy._hp_bar()}{_C.RESET}  {st}")
    print(f"  {_C.MAGENTA}意圖：{intent_str}{_C.RESET}")
    print("─" * W)
    st_p = character.status_display()
    print(f"  {_C.CYAN}{character._hp_bar()}{_C.RESET}  {st_p}")
    print(f"  {_C.CYAN}{_C.BOLD}【{character.traveler_name}·{character.title}】{_C.RESET}")
    print(f"  能量：{_energy_bar(energy, max_energy)}    {deck.summary()}")
    print("─" * W)
    _p(deck.hand_display(character))
    print("─" * W)
    hand_max = len(deck.hand)
    _p(f"  [1-{hand_max}] 出牌   [e] 結束回合   [r] 逃跑   [s] 查看狀態")
    print(_C.BOLD + "═" * W + _C.RESET)


# ── 主戰鬥類別 ────────────────────────────────────────────────

class Battle:
    def __init__(self, character, enemy: Enemy, hand_size: int = 5, base_energy: int = 3) -> None:
        self.character = character
        self.enemy = enemy
        self.deck = Deck(character.deck_ids)
        self.hand_size = hand_size
        self.base_energy = base_energy
        self.outcome: BattleOutcome | None = None

    def run(self) -> BattleOutcome:
        _clear()
        print(_C.BOLD + "═" * W + _C.RESET)
        _typewrite(f"  遭遇戰鬥：{_C.RED}{_C.BOLD}【{self.enemy.name}】{_C.RESET}")
        _typewrite(f"  {_C.DIM}{self.enemy.flavor}{_C.RESET}")
        print(_C.BOLD + "═" * W + _C.RESET)
        _pause(1.0)

        self.enemy.select_action(self.character)
        turn_delay = _cfg["game"].get("turn_delay", 3.0)

        while self.character.is_alive() and self.enemy.is_alive():
            outcome = self._player_turn()
            if outcome:
                self.outcome = outcome
                break
            if not self.enemy.is_alive():
                self.outcome = BattleOutcome.WIN
                break
            outcome = self._enemy_turn()
            if outcome:
                self.outcome = outcome
                break
            if self.character.is_alive() and self.enemy.is_alive():
                _p(f"\n  {_C.DIM}── 回合結束，稍作停頓… ──{_C.RESET}")
                _timed_pause(turn_delay)

        self._show_result()
        return self.outcome

    # ── 玩家回合 ──────────────────────────────────────────────

    def _player_turn(self) -> BattleOutcome | None:
        msgs = self.character.tick_start_of_turn()
        for m in msgs:
            _typewrite(f"  {m}")
        if not self.character.is_alive():
            return BattleOutcome.LOSE

        self.deck.draw(self.hand_size)
        energy = self.base_energy
        pending: list[Card] = []  # 儲存卡牌物件，保留原始手牌語意

        while True:
            # 處理連打佇列（card 物件，不依賴動態 index）
            if pending:
                card = pending.pop(0)
                if card not in self.deck.hand:
                    _typewrite(f"  {_C.YELLOW}【{card.name}】已不在手中，跳過。{_C.RESET}")
                    continue
                if card.cost > energy:
                    _typewrite(f"  {_C.YELLOW}能量不足，停止連打。（{card.name} 需 {card.cost}，剩 {energy}）{_C.RESET}")
                    pending.clear()
                    continue
                self.deck.play(card)
                energy -= card.cost
                _typewrite(f"\n  {_C.CYAN}出牌：{_C.BOLD}{card.name}{_C.RESET}")
                effect = card.play(self.character, self.enemy)
                for m in effect.messages:
                    _typewrite(f"  {m}")
                extra_e, instant_win, had_draw = _apply_effect_wrap(
                    effect, self.character, self.enemy, self.deck
                )
                energy += extra_e
                _pause(0.4)
                if had_draw or "stun" in self.character.statuses or not self.enemy.is_alive():
                    if pending:
                        _typewrite(f"  {_C.YELLOW}手牌已變動，暫停連打。{_C.RESET}")
                    pending.clear()
                if instant_win or not self.enemy.is_alive():
                    self.deck.end_turn()
                    return BattleOutcome.WIN if instant_win else None
                if _no_playable_cards(self.deck.hand, energy) and not pending:
                    _typewrite(f"  {_C.DIM}（費用不足，自動結束回合）{_C.RESET}")
                    _pause(0.4)
                    break
                continue

            # 顯示畫面並等待輸入
            _render(self.character, self.enemy, self.deck, energy, self.base_energy)

            if "stun" in self.character.statuses:
                _typewrite(f"  {_C.YELLOW}暈眩！本回合無法行動。{_C.RESET}")
                _pause(1.2)
                break

            raw = input("  選擇：").strip().lower()

            if raw == "e":
                break

            if raw == "s":
                self._show_status_detail()
                continue

            if raw == "r":
                if _escape_roll(self.character):
                    _typewrite(f"\n  {_C.GREEN}成功脫身！趁亂逃離了戰鬥。{_C.RESET}")
                    _pause(1.0)
                    self.deck.end_turn()
                    return BattleOutcome.ESCAPE
                else:
                    _typewrite(f"\n  {_C.RED}逃跑失敗！敵人搶先出手！{_C.RESET}")
                    _pause(0.8)
                    self.deck.end_turn()
                    self._execute_enemy_free_attack()
                    if not self.character.is_alive():
                        return BattleOutcome.LOSE
                    self.enemy.select_action(self.character)
                    return None

            # 解析數字輸入（支援 "1" 或 "5 2 1"）
            parts = raw.split()
            indices: list[int] = []
            valid = True
            for p in parts:
                if p.isdigit() and 1 <= int(p) <= len(self.deck.hand):
                    indices.append(int(p) - 1)
                else:
                    valid = False
                    break

            if valid and indices:
                first_idx = indices[0]
                if first_idx >= len(self.deck.hand) or first_idx < 0:
                    _typewrite("  無效的選擇。")
                    continue
                card = self.deck.hand[first_idx]
                if card.cost > energy:
                    _typewrite(f"  {_C.YELLOW}能量不足（需要 {card.cost}，剩餘 {energy}）。{_C.RESET}")
                    _pause(0.5)
                    continue
                # 出第一張牌前先把後續 index 轉為卡牌物件（保留原始手牌位置語意）
                remaining_cards = [
                    self.deck.hand[i] for i in indices[1:]
                    if i < len(self.deck.hand)
                ]
                self.deck.play(card)
                energy -= card.cost
                _typewrite(f"\n  {_C.CYAN}出牌：{_C.BOLD}{card.name}{_C.RESET}")
                effect = card.play(self.character, self.enemy)
                for m in effect.messages:
                    _typewrite(f"  {m}")
                extra_e, instant_win, had_draw = _apply_effect_wrap(
                    effect, self.character, self.enemy, self.deck
                )
                energy += extra_e
                _pause(0.4)
                if had_draw or "stun" in self.character.statuses or not self.enemy.is_alive():
                    if remaining_cards:
                        _typewrite(f"  {_C.YELLOW}手牌已變動，暫停連打。{_C.RESET}")
                else:
                    pending.extend(remaining_cards)
                if instant_win or not self.enemy.is_alive():
                    self.deck.end_turn()
                    return BattleOutcome.WIN if instant_win else None
                if _no_playable_cards(self.deck.hand, energy) and not pending:
                    _typewrite(f"  {_C.DIM}（費用不足，自動結束回合）{_C.RESET}")
                    _pause(0.4)
                    break
            else:
                _typewrite("  請輸入手牌編號（1-5）、e 或 r。")

        self.deck.end_turn()
        return None

    # ── 敵人回合 ──────────────────────────────────────────────

    def _enemy_turn(self) -> BattleOutcome | None:
        msgs = self.enemy.tick_start_of_turn()
        for m in msgs:
            _typewrite(f"  {m}")
        if not self.enemy.is_alive():
            return None

        _typewrite(f"\n  {_C.RED}── 【{self.enemy.name}】的回合 ──{_C.RESET}")

        if "stun" in self.enemy.statuses:
            _typewrite(f"  {_C.YELLOW}【{self.enemy.name}】暈眩，跳過行動。{_C.RESET}")
            _pause(0.8)
        else:
            action = self.enemy.execute_action()
            _typewrite(f"  {_C.RED}{self.enemy.name}：{action.label}！{_C.RESET}")
            _pause(0.4)

            fear_mult = 0.75 if "fear" in self.enemy.statuses else 1.0
            if action.damage > 0:
                actual, msgs = self.character.receive_damage(
                    int(action.damage * fear_mult), true_damage=False
                )
                suffix = f"（受到 {_C.RED}{actual}{_C.RESET} 點傷害）" if actual > 0 else f"（{_C.GREEN}閃避{_C.RESET}）"
                _typewrite(f"  物理攻擊 {action.damage} {suffix}")
                for m in msgs:
                    _typewrite(f"    {m}")

            if action.true_damage > 0:
                actual, msgs = self.character.receive_damage(
                    int(action.true_damage * fear_mult), true_damage=True
                )
                suffix = f"（受到 {_C.RED}{actual}{_C.RESET} 點真實傷害）" if actual > 0 else f"（{_C.CYAN}結界吸收{_C.RESET}）"
                _typewrite(f"  真實傷害 {action.true_damage} {suffix}")
                for m in msgs:
                    _typewrite(f"    {m}")

            if action.self_heal > 0:
                _typewrite(f"  {_C.YELLOW}【{self.enemy.name}】回復了 {action.self_heal} 點生命！{_C.RESET}")

            if action.status_name:
                self.character.apply_status_raw(
                    action.status_name, action.status_value, action.status_extra
                )
                from characters.base import _STATUS_NAMES
                label = _STATUS_NAMES.get(action.status_name, action.status_name)
                _typewrite(f"  施加{_C.MAGENTA}{label}{_C.RESET}效果。")

        if not self.character.is_alive():
            return BattleOutcome.LOSE

        self.enemy.select_action(self.character)
        _pause(0.8)
        return None

    def _show_status_detail(self) -> None:
        _STATUS_DESC = {
            "block":      "吸收物理傷害（消耗後消失）",
            "ward":       "吸收真實傷害（消耗後消失）",
            "evade":      "迴避下一次物理攻擊（每層抵擋一次）",
            "stun":       "無法行動",
            "fear":       "攻擊傷害降低 25%",
            "curse":      "所受傷害提升 20%",
            "burn":       "每回合受到真實傷害",
            "duty_bonus": "下次物理攻擊傷害 +50%",
        }
        print(_C.BOLD + "═" * W + _C.RESET)
        _p("  ◆ 當前狀態詳情")
        _div()

        _p(f"  {_C.CYAN}【{self.character.traveler_name}】{_C.RESET}")
        if self.character.statuses:
            for k, v in self.character.statuses.items():
                desc = _STATUS_DESC.get(k, "")
                if k in ("block", "ward"):
                    _p(f"    {k}：{v['value']} 點  ── {desc}")
                elif k == "evade":
                    _p(f"    迴避：{v['stacks']} 層  ── {desc}")
                elif k == "burn":
                    _p(f"    燃燒：每回合 {v['damage']} 傷，剩 {v['turns']} 回  ── {desc}")
                elif k == "duty_bonus":
                    _p(f"    蓄力  ── {desc}")
                else:
                    _p(f"    {k}：{v['turns']} 回合  ── {desc}")
        else:
            _p("    （無狀態）")

        _div()
        _p(f"  {_C.RED}【{self.enemy.name}】{_C.RESET}")
        if self.enemy.statuses:
            for k, v in self.enemy.statuses.items():
                desc = _STATUS_DESC.get(k, "")
                if k in ("block", "ward"):
                    _p(f"    {k}：{v['value']} 點  ── {desc}")
                elif k == "evade":
                    _p(f"    迴避：{v['stacks']} 層  ── {desc}")
                elif k == "burn":
                    _p(f"    燃燒：每回合 {v['damage']} 傷，剩 {v['turns']} 回  ── {desc}")
                else:
                    _p(f"    {k}：{v['turns']} 回合  ── {desc}")
        else:
            _p("    （無狀態）")

        print(_C.BOLD + "═" * W + _C.RESET)
        input("  ──（按 Enter 返回戰鬥）──\n")

    def _execute_enemy_free_attack(self) -> None:
        action = self.enemy.execute_action()
        _typewrite(f"  {_C.RED}【{self.enemy.name}】趁機：{action.label}！{_C.RESET}")
        if action.damage > 0:
            actual, _ = self.character.receive_damage(action.damage, true_damage=False)
            _typewrite(f"  受到 {actual} 點傷害。")
        if action.true_damage > 0:
            actual, _ = self.character.receive_damage(action.true_damage, true_damage=True)
            _typewrite(f"  受到 {actual} 點真實傷害。")
        if action.status_name:
            self.character.apply_status_raw(
                action.status_name, action.status_value, action.status_extra
            )
        _pause(0.8)

    # ── 結果顯示 ──────────────────────────────────────────────

    def _show_result(self) -> None:
        _clear()
        print(_C.BOLD + "═" * W + _C.RESET)
        if self.outcome == BattleOutcome.WIN:
            _typewrite(f"  {_C.GREEN}{_C.BOLD}勝利！【{self.enemy.name}】已被擊倒。{_C.RESET}")
        elif self.outcome == BattleOutcome.LOSE:
            _typewrite(f"  {_C.RED}落敗……生命耗盡，倒在了這裡。{_C.RESET}")
        elif self.outcome == BattleOutcome.ESCAPE:
            _typewrite(f"  {_C.CYAN}成功脫身，繼續前行。{_C.RESET}")
        _p(f"  {self.character.traveler_name}  生命：{self.character.current_hp}/{self.character.stats['hp']}")
        print(_C.BOLD + "═" * W + _C.RESET)
        delay = _cfg["game"].get("battle_result_delay", 3.0)
        _timed_pause(delay)
