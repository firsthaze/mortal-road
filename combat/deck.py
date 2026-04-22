from __future__ import annotations
import random
from .card import Card, build_card


class Deck:
    """
    每回合結束時，所有牌（手牌 + 已出牌）全數回到牌庫並洗牌。
    牌庫永遠是完整的一副牌。
    """

    def __init__(self, card_ids: list[str]):
        self.all_cards: list[Card] = [build_card(cid) for cid in card_ids]
        self.draw_pile: list[Card] = []
        self.hand: list[Card] = []
        self.played: list[Card] = []
        self._shuffle_all()

    # ── 內部操作 ───────────────────────────────────────────────

    def _shuffle_all(self) -> None:
        self.draw_pile = list(self.all_cards)
        random.shuffle(self.draw_pile)
        self.hand.clear()
        self.played.clear()

    # ── 公開操作 ───────────────────────────────────────────────

    def draw(self, n: int) -> list[Card]:
        """從牌庫頂抽 n 張牌到手牌，回傳實際抽到的牌。"""
        drawn = self.draw_pile[:n]
        self.draw_pile = self.draw_pile[n:]
        self.hand.extend(drawn)
        return drawn

    def play(self, card: Card) -> None:
        """將手牌中的一張牌移到已出牌區。"""
        if card not in self.hand:
            raise ValueError(f"手牌中沒有 {card.name}。")
        self.hand.remove(card)
        self.played.append(card)

    def end_turn(self) -> None:
        """回合結束：所有牌回到牌庫，重新洗牌。"""
        self._shuffle_all()

    def add_card(self, card_id: str) -> Card:
        """透過事件新增一張進階牌到牌庫。"""
        card = build_card(card_id)
        self.all_cards.append(card)
        return card

    def remove_card(self, card_id: str) -> bool:
        """透過事件移除一張牌（優先移除非共用牌）。"""
        for i, c in enumerate(self.all_cards):
            if c.id == card_id:
                self.all_cards.pop(i)
                return True
        return False

    def all_cards_ids(self) -> list[str]:
        return [c.id for c in self.all_cards]

    def reset_to_base(self, base_deck_ids: list[str]) -> None:
        """死亡後重置為基本牌庫。"""
        self.all_cards = [build_card(cid) for cid in base_deck_ids]
        self._shuffle_all()

    # ── 顯示輔助 ──────────────────────────────────────────────

    _STATUS_TAG = {
        "stun": "暈眩", "fear": "恐懼", "curse": "詛咒",
        "burn": "燃燒", "evade": "迴避", "duty_bonus": "蓄力",
    }

    def hand_display(self, user=None) -> str:
        if not self.hand:
            return "  手牌：（空）"
        lines = ["  手牌："]
        for i, card in enumerate(self.hand, 1):
            if user is not None:
                try:
                    eff = card.preview(user)
                    tags = []
                    if eff.damage > 0:
                        tags.append(f"物傷{eff.damage}")
                    if eff.true_damage > 0:
                        tags.append(f"真傷{eff.true_damage}")
                    if eff.healing > 0:
                        tags.append(f"治癒{eff.healing}")
                    if eff.self_block > 0:
                        tags.append(f"護盾+{eff.self_block}")
                    if eff.self_ward > 0:
                        tags.append(f"結界+{eff.self_ward}")
                    if eff.extra_energy > 0:
                        tags.append(f"能量+{eff.extra_energy}")
                    if eff.extra_draw > 0:
                        tags.append(f"抽牌+{eff.extra_draw}")
                    if eff.instant_win:
                        tags.append("即決")
                    for sa in eff.target_statuses:
                        label = self._STATUS_TAG.get(sa.name, sa.name)
                        tags.append(f"敵{label}")
                    for sa in eff.self_statuses:
                        label = self._STATUS_TAG.get(sa.name, sa.name)
                        tags.append(f"自{label}")
                    dmg_str = "  ❮" + "·".join(tags) + "❯" if tags else ""
                    lines.append(f"    [{i}] {card.name}（{card.cost}能）{dmg_str}")
                except Exception:
                    lines.append(f"    [{i}] {card.name}（{card.cost}能）── {card.description}")
            else:
                lines.append(f"    [{i}] {card.name}（{card.cost}能）── {card.description}")
        return "\n".join(lines)

    def summary(self) -> str:
        return (
            f"牌庫 {len(self.draw_pile)} 張 ｜ "
            f"手牌 {len(self.hand)} 張 ｜ "
            f"已出 {len(self.played)} 張 ｜ "
            f"共 {len(self.all_cards)} 張"
        )

    def __repr__(self) -> str:
        return f"<Deck total={len(self.all_cards)} hand={len(self.hand)}>"
