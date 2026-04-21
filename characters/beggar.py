from .base import Character


class Beggar(Character):
    name = "乞丐"
    title = "街頭浪人"
    description = (
        "流落街頭，一無所有，卻練就了一身求生的本事。\n"
        "幸運與生存是他最可靠的夥伴，看似落魄，實則難以擊倒。"
    )
    char_key = "beggar"
    escape_stat = "luck"
    base_deck_ids = [
        "strike",
        "strike",
        "dodge",
        "dodge",
        "lucky_strike",
        "survival_instinct",
        "street_scavenge",
        "tough_skin",
        "wild_swing",
        "desperation",
    ]
