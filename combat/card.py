from __future__ import annotations
import random
from dataclasses import dataclass, field
from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from characters.base import Character


# ── 效果資料結構 ────────────────────────────────────────────────

@dataclass
class StatusApplication:
    name: str
    value: int                          # 層數 / 回合數 / 傷害量
    extra: dict = field(default_factory=dict)


@dataclass
class CardEffect:
    damage: int = 0                     # 物理傷害
    true_damage: int = 0                # 真實傷害（無視生存減傷）
    healing: int = 0                    # 治癒使用者
    self_block: int = 0                 # 使用者獲得護盾
    self_ward: int = 0                  # 使用者獲得結界（擋真實傷害）
    self_damage: int = 0                # 使用者自身受到的真實傷害
    extra_energy: int = 0               # 本回合額外能量
    extra_draw: int = 0                 # 立即額外抽牌
    target_statuses: list[StatusApplication] = field(default_factory=list)
    self_statuses: list[StatusApplication] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)
    instant_win: bool = False           # 直接結束戰鬥（如逮捕）


# ── 卡牌基礎類別 ────────────────────────────────────────────────

class Card:
    def __init__(
        self,
        card_id: str,
        name: str,
        cost: int,
        description: str,
        effect_fn: Callable,
    ):
        self.id = card_id
        self.name = name
        self.cost = cost
        self.description = description
        self._effect_fn = effect_fn

    def play(self, user: "Character", target) -> CardEffect:
        return self._effect_fn(user, target)

    def __repr__(self) -> str:
        return f"[{self.name}·{self.cost}能]"


# ── 機率輔助 ────────────────────────────────────────────────────

def _luck_roll(luck: int) -> bool:
    return random.random() * 100 < min(25 + luck * 0.5, 80)


def _social_roll(social: int) -> bool:
    return random.random() * 100 < min(20 + social * 0.5, 75)


def _stun_roll(base_pct: float, mitigating_stat: int = 0) -> bool:
    chance = min(base_pct + mitigating_stat * 0.3, 65)
    return random.random() * 100 < chance


# ── 共用卡牌 ────────────────────────────────────────────────────

def _make_strike() -> Card:
    def effect(user, target):
        dmg = 6 + int(user.stat("strength") * 0.4)
        return CardEffect(damage=dmg, messages=[f"奮力出擊，造成 {dmg} 點傷害。"])
    return Card("strike", "出拳", 1, "造成物理傷害（武力加成）", effect)


def _make_dodge() -> Card:
    def effect(user, target):
        turns = max(1, 1 + int(user.stat("luck") / 25))
        return CardEffect(
            self_statuses=[StatusApplication("evade", turns)],
            messages=[f"身形一閃，獲得迴避狀態 {turns} 層。"],
        )
    return Card("dodge", "閃身", 1, "獲得迴避（幸運加成層數）", effect)


def _make_block() -> Card:
    def effect(user, target):
        val = 5 + int(user.stat("survival") * 0.4)
        return CardEffect(self_block=val, messages=[f"全力格擋，獲得 {val} 點護盾。"])
    return Card("block", "格擋", 1, "獲得護盾（生存加成）", effect)


# ── 乞丐專屬 ────────────────────────────────────────────────────

def _make_lucky_strike() -> Card:
    def effect(user, target):
        if _luck_roll(user.stat("luck")):
            dmg = 12 + int(user.stat("luck") * 0.5)
            return CardEffect(damage=dmg, messages=[f"老天保佑！要害一擊，造成 {dmg} 點傷害！"])
        else:
            dmg = 4 + int(user.stat("strength") * 0.2)
            return CardEffect(damage=dmg, messages=[f"出手落空，僅造成 {dmg} 點傷害。"])
    return Card("lucky_strike", "幸運一擊", 1, "幸運判定：成功造成高傷害（幸運加成），失敗造成少量傷害", effect)


def _make_survival_instinct() -> Card:
    def effect(user, target):
        blk = 6 + int(user.stat("survival") * 0.5)
        hp = 2 + int(user.stat("survival") * 0.1)
        return CardEffect(
            self_block=blk,
            healing=hp,
            messages=[f"求生本能爆發，獲得 {blk} 點護盾並恢復 {hp} 點生命。"],
        )
    return Card("survival_instinct", "求生本能", 1, "獲得護盾並小量回復（生存加成）", effect)


def _make_street_scavenge() -> Card:
    def effect(user, target):
        dmg = 4 + int(user.stat("strength") * 0.2)
        return CardEffect(
            damage=dmg,
            extra_draw=1,
            messages=[f"趁亂出手造成 {dmg} 點傷害，順手再摸一張牌。"],
        )
    return Card("street_scavenge", "街頭搜羅", 1, "造成少量傷害並立即額外抽一張牌", effect)


def _make_tough_skin() -> Card:
    def effect(user, target):
        blk = 8 + int(user.stat("survival") * 0.6)
        ward = 2 + int(user.stat("spirit") * 0.1)
        return CardEffect(
            self_block=blk,
            self_ward=ward,
            messages=[f"皮糙肉厚，獲得 {blk} 點護盾與 {ward} 點結界。"],
        )
    return Card("tough_skin", "硬皮", 1, "獲得護盾與結界（生存/靈力加成）", effect)


def _make_wild_swing() -> Card:
    def effect(user, target):
        dmg = 12 + int(user.stat("strength") * 0.6)
        fx = CardEffect(damage=dmg, messages=[f"狂暴揮擊，造成 {dmg} 點傷害！"])
        stun_chance = max(5, 30 - user.stat("luck") * 0.3)
        if random.random() * 100 < stun_chance:
            fx.self_statuses.append(StatusApplication("stun", 1))
            fx.messages.append("但出手過猛，下回合暈眩一回合！")
        return fx
    return Card("wild_swing", "狂暴揮擊", 2, "高傷害物理攻擊（武力加成），有機率自身暈眩（幸運降低機率）", effect)


def _make_desperation() -> Card:
    def effect(user, target):
        hp_ratio = user.current_hp / user.stats["hp"]
        if hp_ratio < 0.3:
            dmg = 18 + int(user.stat("strength") * 0.6)
            return CardEffect(damage=dmg, messages=[f"背水一戰！爆發全力，造成 {dmg} 點傷害！"])
        else:
            dmg = 6 + int(user.stat("strength") * 0.2)
            return CardEffect(damage=dmg, messages=[f"出手一擊，造成 {dmg} 點傷害。（HP 低於 30% 時威力大增）"])
    return Card("desperation", "背水一戰", 1, "HP 低於 30% 時造成大量傷害，否則造成普通傷害", effect)


# ── 花魁專屬 ────────────────────────────────────────────────────

def _make_charm() -> Card:
    def effect(user, target):
        if _social_roll(user.stat("social")):
            return CardEffect(
                target_statuses=[StatusApplication("stun", 1)],
                messages=["眉目含情一笑，對手愣在原地，下回合無法行動。"],
            )
        else:
            dmg = 4 + int(user.stat("social") * 0.2)
            return CardEffect(damage=dmg, messages=[f"魅惑失效，以扇柄輕擊，造成 {dmg} 點傷害。"])
    return Card("charm", "魅惑", 2, "社交判定：成功使敵人暈眩一回合，失敗造成少量傷害", effect)


def _make_alluring_gaze() -> Card:
    def effect(user, target):
        turns = max(1, 1 + int(user.stat("social") / 20))
        return CardEffect(
            target_statuses=[StatusApplication("fear", turns)],
            messages=[f"勾魂一瞥，敵人心神不寧，攻擊力降低 {turns} 回合。"],
        )
    return Card("alluring_gaze", "勾魂眼波", 1, "使敵人陷入恐懼（減傷），社交加成持續回合", effect)


def _make_whispered_threat() -> Card:
    def effect(user, target):
        dmg = 5 + int(user.stat("social") * 0.3)
        return CardEffect(
            damage=dmg,
            target_statuses=[StatusApplication("fear", 1)],
            messages=[f"耳語恐嚇，造成 {dmg} 點傷害並使敵人恐懼一回合。"],
        )
    return Card("whispered_threat", "耳語恐嚇", 1, "造成傷害並施加恐懼（社交加成）", effect)


def _make_spirit_dance() -> Card:
    def effect(user, target):
        dmg = 5 + int(user.stat("spirit") * 0.35)
        return CardEffect(true_damage=dmg, messages=[f"靈氣貫體，造成 {dmg} 點真實傷害。"])
    return Card("spirit_dance", "靈舞", 1, "造成真實傷害（靈力加成，無視減傷）", effect)


def _make_silk_veil() -> Card:
    def effect(user, target):
        blk = 3 + int(user.stat("social") * 0.25)
        return CardEffect(
            self_block=blk,
            extra_draw=1,
            messages=[f"絲絹護身，獲得 {blk} 點護盾並立即再抽一張牌。"],
        )
    return Card("silk_veil", "絲絹護體", 1, "獲得護盾並抽一張牌（社交加成）", effect)


def _make_social_grace() -> Card:
    def effect(user, target):
        hp = 4 + int(user.stat("social") * 0.25)
        return CardEffect(healing=hp, messages=[f"笑語應對，氣定神閒，恢復 {hp} 點生命。"])
    return Card("social_grace", "圓滑應對", 1, "回復生命（社交加成）", effect)


def _make_enchant() -> Card:
    def effect(user, target):
        burn_dmg = 3 + int(user.stat("spirit") * 0.2)
        turns = 2 + int(user.stat("spirit") / 20)
        return CardEffect(
            target_statuses=[StatusApplication("burn", burn_dmg, {"turns": turns})],
            messages=[f"蠱惑術發動，敵人心火燎燒，每回合受到 {burn_dmg} 點真實傷害，持續 {turns} 回合。"],
        )
    return Card("enchant", "蠱惑術", 2, "施加燃燒（每回合真實傷害，靈力加成）", effect)


# ── 捕快專屬 ────────────────────────────────────────────────────

def _make_official_decree() -> Card:
    def effect(user, target):
        if _social_roll(user.stat("social")):
            turns = 1 + int(user.stat("social") / 20)
            return CardEffect(
                target_statuses=[StatusApplication("fear", turns)],
                messages=[f"出示官牌，敵人膽寒，恐懼 {turns} 回合。"],
            )
        else:
            return CardEffect(damage=4, messages=["官牌威嚇失效，硬衝上前，造成 4 點傷害。"])
    return Card("official_decree", "官府令牌", 1, "社交判定：成功施加恐懼，失敗造成少量傷害", effect)


def _make_iron_fist() -> Card:
    def effect(user, target):
        dmg = 10 + int(user.stat("strength") * 0.5)
        fx = CardEffect(damage=dmg, messages=[f"鐵拳重擊，造成 {dmg} 點傷害！"])
        if _stun_roll(30, user.stat("social")):
            fx.target_statuses.append(StatusApplication("stun", 1))
            fx.messages.append("一拳打暈，敵人下回合無法行動。")
        return fx
    return Card("iron_fist", "鐵拳", 2, "重拳造成高傷害（武力加成），有機率暈眩敵人（社交加成機率）", effect)


def _make_arrest() -> Card:
    def effect(user, target):
        hp_ratio = target.current_hp / target.stats["hp"]
        if hp_ratio < 0.4:
            return CardEffect(instant_win=True, messages=["奉公守法！當場拿下，戰鬥結束。"])
        else:
            dmg = 8 + int(user.stat("strength") * 0.45)
            return CardEffect(damage=dmg, messages=[f"拿下不成，強行壓制，造成 {dmg} 點傷害。（敵人 HP 低於 40% 時可直接制伏）"])
    return Card("arrest", "拿下", 2, "敵人 HP < 40% 時直接制伏結束戰鬥，否則造成物理傷害", effect)


def _make_heavy_blow() -> Card:
    def effect(user, target):
        dmg = 14 + int(user.stat("strength") * 0.65)
        self_dmg = 3
        return CardEffect(
            damage=dmg,
            self_damage=self_dmg,
            messages=[f"捨命一擊，造成 {dmg} 點傷害，但自身受到 {self_dmg} 點真實傷害。"],
        )
    return Card("heavy_blow", "重擊", 2, "高傷害（武力加成），自身受到少量真實傷害", effect)


def _make_duty_bound() -> Card:
    def effect(user, target):
        blk = 6 + int(user.stat("survival") * 0.45)
        return CardEffect(
            self_block=blk,
            self_statuses=[StatusApplication("duty_bonus", 150)],
            messages=[f"職責所在，獲得 {blk} 點護盾，下一次物理攻擊傷害提升 50%。"],
        )
    return Card("duty_bound", "職責所在", 1, "獲得護盾（生存加成），下次物理攻擊 +50% 傷害", effect)


# ── 道士專屬 ────────────────────────────────────────────────────

def _make_spirit_bolt() -> Card:
    def effect(user, target):
        dmg = 8 + int(user.stat("spirit") * 0.45)
        return CardEffect(true_damage=dmg, messages=[f"靈光一閃，造成 {dmg} 點真實傷害。"])
    return Card("spirit_bolt", "靈光一擊", 1, "造成真實傷害（靈力加成）", effect)


def _make_talisman() -> Card:
    def effect(user, target):
        ward = 6 + int(user.stat("spirit") * 0.35)
        return CardEffect(self_ward=ward, messages=[f"貼上護身符，獲得 {ward} 點結界（可阻擋真實傷害）。"])
    return Card("talisman", "護身符", 1, "獲得結界（擋真實傷害，靈力加成）", effect)


def _make_curse_seal() -> Card:
    def effect(user, target):
        turns = 2 + int(user.stat("spirit") / 25)
        return CardEffect(
            target_statuses=[StatusApplication("curse", turns)],
            messages=[f"詛咒封印！敵人受到的所有傷害提升 20%，持續 {turns} 回合。"],
        )
    return Card("curse_seal", "詛咒封印", 2, "使敵人受到傷害 +20%（靈力加成持續回合）", effect)


def _make_meditate() -> Card:
    def effect(user, target):
        hp = 3 + int(user.stat("spirit") * 0.08)
        return CardEffect(
            extra_energy=1,
            healing=hp,
            messages=[f"靜坐入定，本回合獲得 1 點額外能量，並恢復 {hp} 點生命。"],
        )
    return Card("meditate", "靜坐入定", 0, "獲得 1 點額外能量並小量回復（零費，靈力加成回復）", effect)


def _make_ghost_step() -> Card:
    def effect(user, target):
        dmg = 4 + int(user.stat("luck") * 0.25)
        return CardEffect(
            true_damage=dmg,
            self_statuses=[StatusApplication("evade", 1)],
            messages=[f"鬼步穿行，造成 {dmg} 點真實傷害並獲得迴避一層。"],
        )
    return Card("ghost_step", "鬼步", 1, "造成真實傷害（幸運加成）並獲得迴避", effect)


def _make_yin_surge() -> Card:
    def effect(user, target):
        dmg = 6 + int(user.stat("spirit") * 0.45)
        burn_dmg = 2 + int(user.stat("spirit") * 0.15)
        turns = 2
        return CardEffect(
            true_damage=dmg,
            target_statuses=[StatusApplication("burn", burn_dmg, {"turns": turns})],
            messages=[
                f"陰氣爆發，造成 {dmg} 點真實傷害，",
                f"並施加燃燒（每回合 {burn_dmg} 點真實傷害，持續 {turns} 回合）。",
            ],
        )
    return Card("yin_surge", "陰氣爆發", 2, "真實傷害（靈力加成）並施加燃燒", effect)


def _make_ward() -> Card:
    def effect(user, target):
        ward = 8 + int(user.stat("spirit") * 0.5)
        return CardEffect(self_ward=ward, messages=[f"布下結界，獲得 {ward} 點結界護體。"])
    return Card("ward", "結界", 1, "獲得大量結界（靈力加成）", effect)


# ── 進階牌（事件取得）────────────────────────────────────────────

def _make_iron_will() -> Card:
    def effect(user, target):
        blk = 10 + int(user.stat("survival") * 0.7)
        fx = CardEffect(self_block=blk, messages=[f"鐵志如山，獲得 {blk} 點護盾。"])
        if "stun" in user.statuses:
            del user.statuses["stun"]
            fx.messages.append("鐵志驅散暈眩！")
        return fx
    return Card("iron_will", "鐵志", 1, "獲得大量護盾（生存加成），並清除自身暈眩", effect)


def _make_cursed_blade() -> Card:
    def effect(user, target):
        phys = 10 + int(user.stat("strength") * 0.4)
        true = 6 + int(user.stat("spirit") * 0.4)
        return CardEffect(damage=phys, true_damage=true,
                          messages=[f"邪刃齊出：{phys} 點物理傷害 ＋ {true} 點真實傷害。"])
    return Card("cursed_blade", "邪刃", 2, "同時造成物理傷害（武力）與真實傷害（靈力）", effect)


def _make_divine_luck() -> Card:
    def effect(user, target):
        if _luck_roll(user.stat("luck")):
            hp = 15 + int(user.stat("luck") * 0.3)
            return CardEffect(healing=hp, extra_draw=2,
                              messages=[f"天運降臨！恢復 {hp} 點生命並立即抽 2 張牌！"])
        return CardEffect(extra_draw=1, messages=["天運未至，但多摸了一張牌。"])
    return Card("divine_luck", "天運", 0, "零費！幸運判定：成功大量回復並抽2牌，失敗抽1牌", effect)


def _make_soul_bind() -> Card:
    def effect(user, target):
        if _social_roll(user.stat("social")):
            return CardEffect(
                target_statuses=[StatusApplication("stun", 2)],
                messages=["鎖魂術發動！敵人靈魂被縛，暈眩 2 回合！"])
        dmg = 8 + int(user.stat("social") * 0.4)
        return CardEffect(damage=dmg, messages=[f"術法失效，強行打擊，造成 {dmg} 點傷害。"])
    return Card("soul_bind", "鎖魂", 2, "社交判定：成功暈眩2回合，失敗造成傷害", effect)


def _make_spirit_burst() -> Card:
    def effect(user, target):
        dmg = 12 + int(user.stat("spirit") * 0.6)
        ward = 8 + int(user.stat("spirit") * 0.3)
        return CardEffect(true_damage=dmg, self_ward=ward,
                          messages=[f"靈氣爆發！造成 {dmg} 點真實傷害，獲得 {ward} 點結界。"])
    return Card("spirit_burst", "靈氣爆發", 2, "大量真實傷害（靈力加成）並獲得結界", effect)


def _make_phantom_blade() -> Card:
    def effect(user, target):
        dmg = 6 + int(user.stat("luck") * 0.4)
        return CardEffect(damage=dmg,
                          self_statuses=[StatusApplication("evade", 1)],
                          messages=[f"幻影刃！造成 {dmg} 點傷害，身影虛化獲得迴避一層。"])
    return Card("phantom_blade", "幻影刃", 1, "物理傷害（幸運加成）並獲得迴避", effect)


ADVANCED_CARD_POOL = [
    "iron_will", "cursed_blade", "divine_luck",
    "soul_bind", "spirit_burst", "phantom_blade",
]


# ── 牌庫 ────────────────────────────────────────────────────────

CARD_REGISTRY: dict[str, Callable[[], Card]] = {
    # 共用
    "strike":            _make_strike,
    "dodge":             _make_dodge,
    "block":             _make_block,
    # 乞丐
    "lucky_strike":      _make_lucky_strike,
    "survival_instinct": _make_survival_instinct,
    "street_scavenge":   _make_street_scavenge,
    "tough_skin":        _make_tough_skin,
    "wild_swing":        _make_wild_swing,
    "desperation":       _make_desperation,
    # 花魁
    "charm":             _make_charm,
    "alluring_gaze":     _make_alluring_gaze,
    "whispered_threat":  _make_whispered_threat,
    "spirit_dance":      _make_spirit_dance,
    "silk_veil":         _make_silk_veil,
    "social_grace":      _make_social_grace,
    "enchant":           _make_enchant,
    # 捕快
    "official_decree":   _make_official_decree,
    "iron_fist":         _make_iron_fist,
    "arrest":            _make_arrest,
    "heavy_blow":        _make_heavy_blow,
    "duty_bound":        _make_duty_bound,
    # 道士
    "spirit_bolt":       _make_spirit_bolt,
    "talisman":          _make_talisman,
    "curse_seal":        _make_curse_seal,
    "meditate":          _make_meditate,
    "ghost_step":        _make_ghost_step,
    "yin_surge":         _make_yin_surge,
    "ward":              _make_ward,
    # 進階
    "iron_will":         _make_iron_will,
    "cursed_blade":      _make_cursed_blade,
    "divine_luck":       _make_divine_luck,
    "soul_bind":         _make_soul_bind,
    "spirit_burst":      _make_spirit_burst,
    "phantom_blade":     _make_phantom_blade,
}


def build_card(card_id: str) -> Card:
    if card_id not in CARD_REGISTRY:
        raise ValueError(f"未知卡牌 ID：{card_id}")
    return CARD_REGISTRY[card_id]()
