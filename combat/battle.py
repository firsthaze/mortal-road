from __future__ import annotations
import json
import os
import random
import time
from enum import Enum

from .card import CardEffect
from .deck import Deck
from .enemy import Enemy, EnemyAction

_config_path = os.path.join(os.path.dirname(__file__), "..", "config.json")
with open(_config_path, encoding="utf-8") as f:
    _cfg = json.load(f)


class BattleOutcome(Enum):
    WIN = "win"
    LOSE = "lose"
    ESCAPE = "escape"


# ── 顯示輔助 ──────────────────────────────────────────────────

W = 52

def _div(c: str = "─") -> None:
    print(c * W)

def _p(text: str = "") -> None:
    print(text)

def _pause(sec: float = 0.6) -> None:
    time.sleep(sec)

def _energy_bar(cur: int, max_e: int) -> str:
    return "■" * cur + "□" * (max_e - cur) + f"  ({cur}/{max_e})"

def _clear() -> None:
    print("\n" * 3)


# ── 卡牌效果應用 ───────────────────────────────────────────────

def _apply_effect_wrap(effect: CardEffect, user, target, deck: Deck) -> tuple[int, bool]:
    """回傳 (extra_energy, instant_win)"""
    # 修正方法名稱
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
            _p(f"  {m}")
    if effect.true_damage > 0:
        _, msgs = target.receive_damage(effect.true_damage, true_damage=True)
        for m in msgs:
            _p(f"  {m}")
    if effect.self_damage > 0:
        user.receive_damage(effect.self_damage, true_damage=True)
        _p(f"  自身受到 {effect.self_damage} 點反傷。")
    if effect.healing > 0:
        restored = user.heal(effect.healing)
        if restored > 0:
            _p(f"  恢復 {restored} 點生命。")
    if effect.self_block > 0:
        user.apply_status_raw("block", effect.self_block)
    if effect.self_ward > 0:
        user.apply_status_raw("ward", effect.self_ward)
    for sa in effect.target_statuses:
        target.apply_status_raw(sa.name, sa.value, sa.extra)
    for sa in effect.self_statuses:
        user.apply_status_raw(sa.name, sa.value, sa.extra)
    if effect.extra_draw > 0:
        drawn = deck.draw(effect.extra_draw)
        if drawn:
            names = "、".join(c.name for c in drawn)
            _p(f"  額外抽牌：{names}")
    return effect.extra_energy, effect.instant_win


# ── 逃跑判定 ──────────────────────────────────────────────────

def _escape_roll(character) -> bool:
    stat_val = character.stat(character.escape_stat)
    threshold = min(30 + stat_val * 0.6, 80)
    return random.random() * 100 < threshold


# ── 戰鬥畫面 ──────────────────────────────────────────────────

def _render(character, enemy: Enemy, deck: Deck, energy: int, max_energy: int) -> None:
    _clear()
    _div("═")
    # 敵人區
    intent_str = enemy._next_action.intent_str() if enemy._next_action else "？？？"
    st = enemy.status_display()
    _p(f"  【{enemy.name}】  {enemy._hp_bar()}  {st}")
    _p(f"  意圖：{intent_str}")
    _div()
    # 玩家區
    st_p = character.status_display()
    _p(f"  {character._hp_bar()}  {st_p}")
    _p(f"  【{character.name}·{character.title}】")
    _p(f"  能量：{_energy_bar(energy, max_energy)}    {deck.summary()}")
    _div()
    _p(deck.hand_display())
    _div()
    _p("  [1-5] 出牌   [e] 結束回合   [r] 逃跑")
    _div("═")


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
        _div("═")
        _p(f"  遭遇戰鬥：【{self.enemy.name}】")
        _p(f"  {self.enemy.flavor}")
        _div("═")
        _pause(1.0)

        # 第一回合先確定敵人意圖
        self.enemy.select_action(self.character)

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

        self._show_result()
        return self.outcome

    # ── 玩家回合 ──────────────────────────────────────────────

    def _player_turn(self) -> BattleOutcome | None:
        # 回合開始：tick 狀態
        msgs = self.character.tick_start_of_turn()
        for m in msgs:
            _p(f"  {m}")
        if not self.character.is_alive():
            return BattleOutcome.LOSE

        # 抽牌
        self.deck.draw(self.hand_size)
        energy = self.base_energy

        while True:
            _render(self.character, self.enemy, self.deck, energy, self.base_energy)

            # 暈眩：跳過行動
            if "stun" in self.character.statuses:
                _p("  暈眩！本回合無法行動。")
                _pause(1.2)
                break

            raw = input("  選擇：").strip().lower()

            if raw == "e":
                break

            if raw == "r":
                if _escape_roll(self.character):
                    _p("\n  成功脫身！趁亂逃離了戰鬥。")
                    _pause(1.0)
                    self.deck.end_turn()
                    return BattleOutcome.ESCAPE
                else:
                    _p("\n  逃跑失敗！敵人搶先出手！")
                    _pause(0.8)
                    self.deck.end_turn()
                    # 敵人獲得一次免費行動
                    self._execute_enemy_free_attack()
                    if not self.character.is_alive():
                        return BattleOutcome.LOSE
                    self.enemy.select_action(self.character)
                    return None

            if raw.isdigit():
                idx = int(raw) - 1
                if 0 <= idx < len(self.deck.hand):
                    card = self.deck.hand[idx]
                    if card.cost > energy:
                        _p(f"  能量不足（需要 {card.cost}，剩餘 {energy}）。")
                        _pause(0.5)
                        continue
                    self.deck.play(card)
                    energy -= card.cost
                    _p(f"\n  出牌：{card.name}")
                    effect = card.play(self.character, self.enemy)
                    for m in effect.messages:
                        _p(f"  {m}")
                    extra_e, instant_win = _apply_effect_wrap(
                        effect, self.character, self.enemy, self.deck
                    )
                    energy += extra_e
                    _pause(0.5)
                    if instant_win or not self.enemy.is_alive():
                        self.deck.end_turn()
                        return None
                else:
                    _p("  無效的選擇。")
            else:
                _p("  請輸入手牌編號、e 或 r。")

        self.deck.end_turn()
        return None

    # ── 敵人回合 ──────────────────────────────────────────────

    def _enemy_turn(self) -> BattleOutcome | None:
        msgs = self.enemy.tick_start_of_turn()
        for m in msgs:
            _p(f"  {m}")
        if not self.enemy.is_alive():
            return None

        _p(f"\n  ── 【{self.enemy.name}】的回合 ──")

        if "stun" in self.enemy.statuses:
            _p(f"  【{self.enemy.name}】暈眩，跳過行動。")
            _pause(0.8)
        else:
            action = self.enemy.execute_action()
            _p(f"  {self.enemy.name}：{action.label}！")
            _pause(0.4)

            # 恐懼狀態：敵人傷害降低 25%
            fear_mult = 0.75 if "fear" in self.enemy.statuses else 1.0
            if action.damage > 0:
                actual, msgs = self.character.receive_damage(
                    int(action.damage * fear_mult), true_damage=False
                )
                suffix = f"（受到 {actual} 點傷害）" if actual > 0 else "（閃避）"
                _p(f"  物理攻擊 {action.damage} {suffix}")
                for m in msgs:
                    _p(f"    {m}")

            if action.true_damage > 0:
                actual, msgs = self.character.receive_damage(
                    int(action.true_damage * fear_mult), true_damage=True
                )
                suffix = f"（受到 {actual} 點真實傷害）" if actual > 0 else "（結界吸收）"
                _p(f"  真實傷害 {action.true_damage} {suffix}")
                for m in msgs:
                    _p(f"    {m}")

            if action.status_name:
                self.character.apply_status_raw(
                    action.status_name, action.status_value, action.status_extra
                )
                from characters.base import _STATUS_NAMES
                label = _STATUS_NAMES.get(action.status_name, action.status_name)
                _p(f"  施加{label}效果。")

        if not self.character.is_alive():
            return BattleOutcome.LOSE

        # 敵人決定下一回合意圖
        self.enemy.select_action(self.character)
        _pause(0.8)
        return None

    def _execute_enemy_free_attack(self) -> None:
        """逃跑失敗時敵人的免費攻擊（執行當前意圖）"""
        action = self.enemy.execute_action()
        _p(f"  【{self.enemy.name}】趁機：{action.label}！")
        if action.damage > 0:
            actual, _ = self.character.receive_damage(action.damage, true_damage=False)
            _p(f"  受到 {actual} 點傷害。")
        if action.true_damage > 0:
            actual, _ = self.character.receive_damage(action.true_damage, true_damage=True)
            _p(f"  受到 {actual} 點真實傷害。")
        if action.status_name:
            self.character.apply_status_raw(
                action.status_name, action.status_value, action.status_extra
            )
        _pause(0.8)

    # ── 結果顯示 ──────────────────────────────────────────────

    def _show_result(self) -> None:
        _clear()
        _div("═")
        if self.outcome == BattleOutcome.WIN:
            _p(f"  勝利！【{self.enemy.name}】已被擊倒。")
        elif self.outcome == BattleOutcome.LOSE:
            _p("  落敗……生命耗盡，倒在了這裡。")
        elif self.outcome == BattleOutcome.ESCAPE:
            _p("  成功脫身，繼續前行。")
        _div("═")
        _pause(1.2)
