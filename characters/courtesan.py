from .base import Character


class Courtesan(Character):
    name = "花魁"
    title = "傾城一笑"
    description = (
        "名動四方，笑靨如花，卻深藏心機與算計。\n"
        "社交與魅惑是她的武器，一個眼神便能令人心神蕩漾，忘卻敵意。"
    )
    char_key = "courtesan"
    escape_stat = "social"
    base_deck_ids = [
        "strike",
        "strike",
        "charm",
        "charm",
        "alluring_gaze",
        "whispered_threat",
        "spirit_dance",
        "silk_veil",
        "social_grace",
        "enchant",
    ]
