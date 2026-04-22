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
    "ending_demon_slayer": {
        "title": "斬邪除魔",
        "text": (
            "那卷典籍裡的字，你早就爛熟於心。\n\n"
            "此刻靈力運轉，如大河決堤，所向披靡。\n"
            "邪氣在你面前潰散，如同朝露遇日，無處遁形。\n\n"
            "師傅說：「斬邪容易，除心魔難。」\n"
            "而今日，你兩者皆辦到了。\n"
            "那本殘缺的典籍，也在你心中重新完整。"
        ),
    },
    "ending_shadow_master": {
        "title": "幕後玄機",
        "text": (
            "你從不是這場棋局的棋子——\n"
            "你才是那個在暗中布局的人。\n\n"
            "那個被商人識破的幻象，那杯套出情報的酒，\n"
            "早在第一步棋落下時，你便已算準了結局。\n\n"
            "煙花散盡，眾人還在議論那神秘的幕後推手是誰。\n"
            "你理了理衣衫，轉身融入人群，嘴角帶著一絲只有自己才懂的微笑。"
        ),
    },
    "ending_iron_badge": {
        "title": "鐵面捕快",
        "text": (
            "每一場戰鬥，你都沒有退縮。\n\n"
            "腰牌在陽光下發亮，那是你從未辜負的信仰。\n"
            "人說捕快不過是朝廷的刀，\n"
            "但你知道，這把刀守著的，是那些普通人的平靜日子。\n\n"
            "案子結了，文書押回衙門，上司點頭，同僚拱手。\n"
            "夜裡你獨坐，摸著腰牌——這一趟，值得。"
        ),
    },
    "ending_fortune_reversed": {
        "title": "命運顛覆",
        "text": (
            "乞丐？那只是你曾經蜷縮的地方，不是你的全部。\n\n"
            "你幫過那個醉漢，救過那個旅人，\n"
            "老天爺似乎也注意到了你這個不起眼的傢伙。\n\n"
            "旅途終點，口袋比出發時沉，心比出發時輕。\n"
            "那個蜷縮在牆根的自己，好像已經是很久以前的事了。\n"
            "幸運，從來不是天生的——是走出來的。"
        ),
    },
    "ending_karma_circle": {
        "title": "因果輪迴",
        "text": (
            "廟中道長說過：「因果自有輪迴。」\n\n"
            "你救了路邊的旅人，旅人的秘密牽出了幕後的線索，\n"
            "線索指引你找到了敵人，而打敗敵人的方法，\n"
            "竟藏在道長那夜輕描淡寫的一句話裡。\n\n"
            "每一步看似偶然，回頭看，卻步步相扣。\n"
            "這浮世，因緣俱足，無一多餘。"
        ),
    },
}


def determine_ending(character, history: list[str]) -> str:
    if not character.is_alive():
        return "ending_sacrifice"

    if "chose_escape" in history:
        return "ending_escape"

    hp_ratio = character.current_hp / character.stats["hp"]

    # ── 道士專屬 ──────────────────────────────────────────────
    if character.char_key == "taoist":
        if character.stat("spirit") >= 35 and hp_ratio > 0.35:
            return "ending_immortal"
        if "stole_knowledge" in history and character.stat("spirit") >= 30:
            return "ending_demon_slayer"

    # ── 花魁專屬 ──────────────────────────────────────────────
    if character.char_key == "courtesan":
        if "charmed_intel" in history and "saw_through_merchant" in history:
            return "ending_shadow_master"

    # ── 捕快專屬 ──────────────────────────────────────────────
    if character.char_key == "constable":
        fought = sum(1 for h in history if h.startswith("fought_"))
        if fought >= 3 and "escaped_battle" not in history:
            return "ending_iron_badge"

    # ── 乞丐專屬 ──────────────────────────────────────────────
    if character.char_key == "beggar":
        if "pacified_drunk" in history and "saved_traveler" in history and character.stat("luck") >= 30:
            return "ending_fortune_reversed"

    # ── 組合條件結局 ──────────────────────────────────────────
    if "met_temple_elder" in history and "saved_traveler" in history and hp_ratio > 0.5:
        return "ending_karma_circle"

    # ── 通用結局 ──────────────────────────────────────────────
    if hp_ratio < 0.2:
        return "ending_underdog"

    if hp_ratio > 0.65:
        return "ending_glory"

    return "ending_survivor"
