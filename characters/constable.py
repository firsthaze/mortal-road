from .base import Character


class Constable(Character):
    name = "捕快"
    title = "鐵面無私"
    description = (
        "奉命追緝，鐵面無私，手持官牌走遍江湖。\n"
        "武力與生存是他的根本，正面硬撼從不退縮。"
    )
    char_key = "constable"
    escape_stat = "strength"
    base_deck_ids = [
        "strike",
        "strike",
        "strike",
        "block",
        "block",
        "official_decree",
        "iron_fist",
        "arrest",
        "heavy_blow",
        "duty_bound",
    ]
