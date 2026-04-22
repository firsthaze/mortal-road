import json
import sys
import time

from characters import CHARACTER_MAP
from story import StoryEngine

with open("config.json", encoding="utf-8") as f:
    _config = json.load(f)


def typewrite(text: str, delay: float = 0.03) -> None:
    for ch in text:
        print(ch, end="", flush=True)
        time.sleep(delay)
    print()


def divider(char: str = "─", width: int = 52) -> None:
    print(char * width)


def select_character():
    divider("═")
    typewrite("  浮  世  行  ·  mortal-road", delay=0.05)
    divider("═")
    print()
    choices = list(CHARACTER_MAP.items())
    for i, (_, cls) in enumerate(choices, 1):
        char = cls()
        print(f"  [{i}] {char.name} —— {char.title}")
        print(f"      {char.description.splitlines()[0]}")
        print()
    divider()
    while True:
        raw = input("  選擇你的角色（輸入數字）：").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(choices):
            _, cls = choices[int(raw) - 1]
            char = cls()
            print()
            typewrite(f"  你選擇了【{char.name}】——{char.title}")
            typewrite(f"  {char.description.splitlines()[0]}")
            print()
            print("  " + char.status_line())
            print()
            return char
        print("  請輸入有效的數字。")


def select_difficulty() -> tuple[str, dict]:
    divider()
    print("  選擇難度：")
    levels = [("1", "簡單", "easy"), ("2", "普通", "normal"), ("3", "困難", "hard")]
    for num, label, _ in levels:
        print(f"    [{num}] {label}")
    divider()
    while True:
        raw = input("  輸入數字：").strip()
        for num, label, key in levels:
            if raw == num:
                cfg = _config["difficulty"][key]
                print(f"\n  難度設定為【{label}】\n")
                return key, cfg
        print("  請輸入有效的數字。")


def input_traveler_name(character) -> str:
    divider()
    default = character.name
    raw = input(f"  為你的旅者取個名字（留空則使用「{default}」）：").strip()
    name = raw if raw else default
    typewrite(f"\n  旅者【{name}】，浮世之行，就此開始。\n", delay=0.04)
    return name


def main() -> None:
    try:
        while True:
            character = select_character()
            _, difficulty_cfg = select_difficulty()
            traveler_name = input_traveler_name(character)
            character.traveler_name = traveler_name

            hand_size = _config["game"]["hand_size"]
            base_energy = _config["game"]["base_energy"]

            engine = StoryEngine(
                character=character,
                difficulty_cfg=difficulty_cfg,
                hand_size=hand_size,
                base_energy=base_energy,
            )
            engine.run()

            divider("═")
            again = input("  是否重新開始一局？[y/n]：").strip().lower()
            if again != "y":
                typewrite("\n  浮世匆匆，後會有期。\n", delay=0.04)
                break

    except KeyboardInterrupt:
        print("\n\n  浮世匆匆，後會有期。")
        sys.exit(0)


if __name__ == "__main__":
    main()
