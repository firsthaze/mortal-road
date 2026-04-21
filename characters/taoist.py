from .base import Character


class Taoist(Character):
    name = "道士"
    title = "玄門弟子"
    description = (
        "修行玄門，通曉陰陽，以靈力溝通天地。\n"
        "真實傷害與附魔是他的所長，靈力越深，術法越不可思議。"
    )
    char_key = "taoist"
    escape_stat = "spirit"
    base_deck_ids = [
        "strike",
        "strike",
        "spirit_bolt",
        "spirit_bolt",
        "talisman",
        "curse_seal",
        "meditate",
        "ghost_step",
        "yin_surge",
        "ward",
    ]
