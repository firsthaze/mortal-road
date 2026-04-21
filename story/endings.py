from __future__ import annotations

ENDINGS: dict[str, dict] = {
    "ending_glory": {
        "title": "名揚天下",
        "text": (
            "你以傲人的狀態擊退了一切威脅。\n\n"
            "消息傳開，江湖人人皆知你的名號。有人稱你是俠客，有人稱你是奇人，"
            "有人稱你是仙師——說法各異，但所有人都記住了你這個名字。\n\n"
            "浮世行至此，你終於站在了最高處，俯瞰這片曾讓你步履維艱的天地。"
        ),
    },
    "ending_immortal": {
        "title": "羽化登仙",
        "text": (
            "最後那一擊，靈力突破了你從未觸碰過的境界。\n\n"
            "天地間一道白光，師傅的聲音在耳邊響起：「你回來了。」\n\n"
            "等你睜開眼，眼前已是雲海茫茫——人間的路，就在今日走完了。\n"
            "道，不在書中，不在廟裡，原來一直在這浮世行途之中。"
        ),
    },
    "ending_survivor": {
        "title": "功成身退",
        "text": (
            "你完成了這趟旅途，傷痕累累，卻始終站著。\n\n"
            "沒有鮮花，沒有掌聲，只有一個人靜靜地走在回程的路上。\n"
            "有些事，你永遠不會對外說起。\n\n"
            "而那些只有你知道的時刻，就這樣帶走了。"
        ),
    },
    "ending_sacrifice": {
        "title": "英雄犧牲",
        "text": (
            "你的力氣用盡了。\n\n"
            "膝蓋觸地的那一刻，你才發覺，這條路你已走了多遠。\n"
            "也許有人會記得，也許不會。\n\n"
            "但你清楚，自己所做的一切，從未後悔。\n"
            "眼前的光，漸漸暗了下來……"
        ),
    },
    "ending_escape": {
        "title": "浪跡天涯",
        "text": (
            "你選擇了另一條路。\n\n"
            "那些危險、那些使命，終究與你無關。天地之大，何必困於一時之局？\n"
            "你解下包袱，換個方向走去，心頭意外地輕盈。\n\n"
            "至於那些未竟之事，自有別人去完成。\n"
            "浮世之行，你走出了屬於自己的一條路。"
        ),
    },
    "ending_underdog": {
        "title": "絕地翻盤",
        "text": (
            "說實話，你自己都不敢相信。\n\n"
            "傷痕遍體，氣力將盡，就是在那種時候，你找到了最後一絲力氣。\n"
            "也許是幸運，也許是意志，反正你贏了——\n\n"
            "以一副爛牌，打出了翻天的結局。\n"
            "這浮世啊，最不缺的，就是奇蹟。"
        ),
    },
}


def determine_ending(character, history: list[str]) -> str:
    if not character.is_alive():
        return "ending_sacrifice"

    if "chose_escape" in history:
        return "ending_escape"

    hp_ratio = character.current_hp / character.stats["hp"]

    if character.char_key == "taoist" and character.stat("spirit") >= 35 and hp_ratio > 0.35:
        return "ending_immortal"

    if hp_ratio < 0.2:
        return "ending_underdog"

    if hp_ratio > 0.65:
        return "ending_glory"

    return "ending_survivor"
