# 死路 Mortal Road — 遊戲規格書

> 版本：v1.0（2026-04-22）

---

## 目錄

1. [遊戲概覽](#1-遊戲概覽)
2. [角色職業](#2-角色職業)
3. [屬性系統](#3-屬性系統)
4. [卡牌系統](#4-卡牌系統)
5. [戰鬥系統](#5-戰鬥系統)
6. [狀態效果](#6-狀態效果)
7. [敵人設計](#7-敵人設計)
8. [故事結構](#8-故事結構)
9. [事件系統](#9-事件系統)
10. [結局系統](#10-結局系統)
11. [難度設定](#11-難度設定)
12. [技術架構](#12-技術架構)

---

## 1. 遊戲概覽

**死路 Mortal Road** 是一款文字冒險卡牌 RPG，玩家扮演一名在亂世中漂泊的旅者，穿越 12 個故事節點（幕），在途中遭遇各種人物與衝突。

### 核心設計原則

- **職業動機**：每個職業有自己的出發動機，而非執行上天交付的使命
- **探索感**：故事文案以「路過、偶遇」為基調，而非明顯的任務敘事
- **卡牌構築**：玩家在旅途中透過事件獲得進階牌，建構屬於自己的牌庫
- **永久死亡**：戰鬥失敗則直接進入犧牲結局，無存檔重來

### 遊玩流程

```
建立角色 → 輸入旅者名稱 → 選擇職業
    ↓
幕1（起點）→ 幕2 → ... → 幕12（終幕）
    ↓              ↑ 每幕從多個節點中隨機選一
戰鬥 / 故事選擇 / 事件
    ↓
結局（11 種）
```

---

## 2. 角色職業

### 2.1 四大職業

| 職業 | char_key | 名稱 | 頭銜 | 主攻方向 |
|------|----------|------|------|----------|
| 乞丐 | `beggar` | 破衣行者 | 塵間散人 | 高傷低防，流血戰術 |
| 花魁 | `courtesan` | 傾城一笑 | 紅塵遊俠 | 狀態控制，即決技 |
| 捕快 | `constable` | 鐵手執法 | 正道行者 | 均衡防禦，累積蓄力 |
| 道士 | `taoist` | 清風問道 | 方外散人 | 護盾結界，屬性加乘 |

### 2.2 職業基礎屬性

| 屬性 | 乞丐 | 花魁 | 捕快 | 道士 |
|------|------|------|------|------|
| HP | 80 | 70 | 100 | 85 |
| ATK | 18 | 14 | 15 | 12 |
| DEF | 5 | 6 | 10 | 8 |
| SPD | 8 | 12 | 7 | 9 |
| WIS | 3 | 6 | 4 | 10 |
| LCK | 5 | 8 | 4 | 5 |

### 2.3 職業起始牌庫

| 職業 | 起始牌組 |
|------|----------|
| 乞丐 | `strike × 3`, `dodge × 2` |
| 花魁 | `allure`, `strike × 2`, `dodge` |
| 捕快 | `arrest`, `block × 2`, `strike` |
| 道士 | `ward`, `purify`, `strike`, `dodge` |

---

## 3. 屬性系統

### 3.1 六大屬性

| 屬性 | 欄位 | 說明 |
|------|------|------|
| 生命 | `hp` | 最大生命值 |
| 攻擊 | `atk` | 物理傷害基數 |
| 防禦 | `def` | 傷害減免（護盾效率） |
| 速度 | `spd` | 決定迴避相關卡牌效果 |
| 智慧 | `wis` | 影響特殊技效率 |
| 幸運 | `lck` | 影響爆擊與觸發機率 |

### 3.2 衍生公式

```
物理傷害 = 卡牌 base_damage × (1 + ATK / 100)
護盾吸收 = 護盾值（不受 DEF 影響，DEF 影響護盾效率卡牌）
恐懼減傷 = 攻擊力 × 0.75（乘以 0.25 懲罰）
詛咒增傷 = 受到傷害 × 1.20
燃燒傷害 = 固定真實傷害（忽略護盾與結界）
```

### 3.3 屬性查看

戰鬥中按 `v` 可查看角色完整屬性面板。

---

## 4. 卡牌系統

### 4.1 CardEffect 資料結構

| 欄位 | 型別 | 說明 |
|------|------|------|
| `damage` | int | 物理傷害 |
| `true_damage` | int | 真實傷害（穿透護盾） |
| `healing` | int | 自身回血 |
| `self_block` | int | 自身護盾 |
| `self_ward` | int | 自身結界（抵擋真實傷害） |
| `extra_energy` | int | 額外能量 |
| `extra_draw` | int | 額外抽牌 |
| `target_statuses` | list[StatusApply] | 施加給敵人的狀態 |
| `self_statuses` | list[StatusApply] | 施加給自身的狀態 |
| `instant_win` | bool | 直接判定勝利 |

### 4.2 StatusApply 資料結構

| 欄位 | 型別 | 說明 |
|------|------|------|
| `name` | str | 狀態名（stun/fear/curse/burn/evade/duty_bonus） |
| `value` | int | 持續回合數（burn 為每回合傷害量） |

### 4.3 基礎牌組（所有職業可用）

| 牌 ID | 名稱 | 費用 | 效果摘要 |
|-------|------|------|----------|
| `strike` | 劈砍 | 1 | 物理傷害 × ATK |
| `dodge` | 閃身 | 1 | 自身迴避狀態 1 回合 |
| `block` | 格擋 | 1 | 護盾 + DEF × 2 |

### 4.4 職業特色起始牌

| 牌 ID | 名稱 | 費用 | 職業 | 效果摘要 |
|-------|------|------|------|----------|
| `allure` | 媚眼 | 1 | 花魁 | 施加恐懼 2 回合 |
| `arrest` | 拿下 | 2 | 捕快 | 物理傷害 + 暈眩 1 回合 |
| `ward` | 護法陣 | 2 | 道士 | 結界 + WIS × 1.5 |
| `purify` | 清心咒 | 1 | 道士 | 移除自身負面狀態，回血 |

### 4.5 進階牌池（ADVANCED_CARD_POOL）

| 牌 ID | 名稱 | 費用 | 效果摘要 |
|-------|------|------|----------|
| `heavy_blow` | 重擊 | 2 | 高物理傷害 |
| `chain_strike` | 連環劈 | 2 | 連擊 × 2 |
| `true_strike` | 穿心刺 | 2 | 真實傷害 |
| `life_drain` | 吸血 | 2 | 物理傷害 + 吸血回復 |
| `burn_palm` | 火焰掌 | 2 | 物理傷害 + 燃燒 |
| `curse_mark` | 詛咒印 | 1 | 施加詛咒 3 回合 |
| `iron_skin` | 鐵皮功 | 2 | 大量護盾 |
| `counter` | 反擊 | 1 | 護盾 + 待機反擊 |
| `meditate` | 打坐 | 0 | 抽牌 + 能量 |
| `execute` | 處決 | 3 | 高真實傷害（敵人血量低時） |

### 4.6 職業專屬事件牌池（CLASS_EVENT_POOL）

每個職業在事件中可獲得的牌不同，偏向強化各自的核心策略。

| 職業 | 偏向效果 |
|------|----------|
| 乞丐 | 高傷、連擊、吸血 |
| 花魁 | 控制、恐懼、即決 |
| 捕快 | 防禦、暈眩、蓄力 |
| 道士 | 結界、淨化、能量 |

---

## 5. 戰鬥系統

### 5.1 戰鬥參數

| 參數 | 預設值 | 說明 |
|------|--------|------|
| `hand_size` | 5 | 每回合起手張數 |
| `base_energy` | 3 | 每回合基礎能量 |

### 5.2 回合結構

```
玩家回合開始
  ├─ 重置能量（base_energy + 額外能量）
  ├─ 抽牌（hand_size 張，或剩餘牌數）
  ├─ 顯示手牌 + 敵人狀態
  ├─ 玩家輸入選擇：
  │    [1..N]  出牌
  │    [e]     結束回合
  │    [r]     逃跑
  │    [v]     查看屬性
  │    [d]     查看牌庫
  └─ 出牌執行 → 顯示效果結果

敵人回合
  ├─ 暈眩：跳過行動
  ├─ 恐懼：傷害 × 0.75
  └─ 執行敵人行動（攻擊 / 防禦 / 特技）

狀態結算
  ├─ 燃燒：造成真實傷害
  └─ 持續狀態計時器 -1
```

### 5.3 多牌連出（pending queue）

玩家一回合可出多張牌，只要能量足夠。每次出牌扣除對應費用後繼續選牌，直到主動結束或能量耗盡。

### 5.4 逃跑機制

- 按 `r` 嘗試逃跑
- 逃跑成功：記錄 `escaped_battle` 至歷史，進入逃跑後節點
- 逃跑進度影響特定結局判定

### 5.5 戰鬥結果

| 結果 | 觸發條件 | 後續 |
|------|----------|------|
| `WIN` | 敵人 HP ≤ 0 | 進入 `next_win` 節點 |
| `LOSE` | 玩家 HP ≤ 0 | 觸發 `__sacrifice__` |
| `ESCAPE` | 玩家選擇逃跑 | 進入 `next_escape` 節點 |

---

## 6. 狀態效果

| 狀態 | ID | 施加方 | 效果 | 結算時機 |
|------|-----|--------|------|----------|
| 暈眩 | `stun` | 玩家→敵 | 跳過本回合行動 | 敵人回合開始 |
| 恐懼 | `fear` | 玩家→敵 | 攻擊傷害 × 0.75 | 敵人攻擊時 |
| 詛咒 | `curse` | 玩家→敵 | 所受傷害 × 1.20 | 受傷時 |
| 燃燒 | `burn` | 玩家→敵 | 每回合 N 真實傷害 | 回合結束 |
| 迴避 | `evade` | 玩家→自 | 本回合免疫一次攻擊 | 受攻擊時 |
| 蓄力 | `duty_bonus` | 捕快卡→自 | 特定牌效果強化 | 出牌時 |
| 護盾 | `block` | 卡牌→自 | 吸收物理傷害 | 受傷時 |
| 結界 | `ward` | 卡牌→自 | 吸收真實傷害 | 受傷時 |

---

## 7. 敵人設計

### 7.1 一般敵人

| 敵人 ID | 名稱 | HP | ATK | DEF | 特性 |
|---------|------|-----|-----|-----|------|
| `bandit` | 山賊 | 60 | 12 | 3 | 基礎敵人 |
| `soldier` | 官兵 | 80 | 14 | 8 | 較高防禦 |
| `assassin` | 刺客 | 50 | 20 | 2 | 高攻低防 |
| `cultist` | 邪教徒 | 70 | 13 | 5 | 施加詛咒 |
| `wandering_master` | 行走的劍客 | 90 | 16 | 6 | 反擊技 |

### 7.2 Boss 池（BOSS_POOL）

遊戲開始時隨機選定一位 Boss，固定為最終戰對手。

| Boss ID | 名稱 | HP | ATK | DEF | 特性 |
|---------|------|-----|-----|-----|------|
| `warlord` | 亂世梟雄 | 180 | 22 | 10 | 高攻高防 |
| `shadow_lord` | 暗影主 | 150 | 25 | 6 | 施加恐懼+詛咒 |
| `iron_guard` | 鐵衛統領 | 200 | 18 | 15 | 極高防禦 |
| `corrupt_sage` | 墮落法師 | 160 | 20 | 8 | 燃燒+真傷 |

### 7.3 難度縮放

敵人屬性依難度設定乘以係數（見第 11 節）。

---

## 8. 故事結構

### 8.1 12 幕架構

| 幕 | 內容 | 節點數 |
|----|------|--------|
| act1 | 起點（市集、廟宇、荒道） | 3 |
| act2 | 第一個轉折 | 3 |
| act3 | 中途風波 | 3 |
| act4 | 廟宇或深山 | 3 |
| act5 | 情報與謎 | 3 |
| act6 | 岔路抉擇 | 3 |
| act7 | 鬼市或隱者 | 2 |
| act8 | 追捕與逃亡 | 2 |
| act9 | 血祭與背叛 | 3 |
| act10 | 倖存者與間諜 | 2 |
| act11 | 黑城深處 | 3 |
| act12 | 終幕決戰 | 3 |

### 8.2 節點類型

| 類型 | type 值 | 說明 |
|------|---------|------|
| 故事節點 | `story` | 文字敘事 + 選擇分支 |
| 戰鬥節點 | `combat` | 對戰一名敵人 |
| 事件節點 | `event` | 特殊效果（回血、獲牌） |
| 結局節點 | `ending` | 遊戲結束 |

### 8.3 StoryNode 資料結構

| 欄位 | 型別 | 說明 |
|------|------|------|
| `id` | str | 節點唯一識別碼 |
| `type` | str | 節點類型 |
| `title` | str | 標題（顯示於 banner） |
| `text` | str | 預設敘事文字 |
| `class_text` | dict | 職業專屬文字覆蓋 |
| `choices` | list | 可用選項（故事節點） |
| `next` | str | 無選項時的下一節點 |
| `next_win` | str | 戰鬥勝利後節點 |
| `next_escape` | str | 逃跑後節點 |
| `combat_id` | str | 敵人 ID |
| `event_type` | str | 事件類型 |
| `heal_pct` | int | 回血百分比 |
| `cost_hp_pct` | int | 代價 HP 百分比 |
| `pick_from` | int | 事件獲牌選擇數 |
| `history_flag` | str | 記錄至歷史的標記 |

### 8.4 Choice 資料結構

| 欄位 | 型別 | 說明 |
|------|------|------|
| `text` | str | 選項文字 |
| `next` | str | 跳轉節點 |
| `condition` | dict | 可用條件（class/stat） |

### 8.5 條件系統

```json
{ "class": "beggar" }              // 限定職業
{ "class": ["beggar", "taoist"] }  // 多職業限定
{ "stat": "wis", "min": 8 }        // 屬性門檻
```

### 8.6 特殊節點 ID

| 特殊 ID | 說明 |
|---------|------|
| `__act1__` ~ `__act12__` | 從對應幕隨機選一節點 |
| `__ending__` | 由歷史記錄決定結局 |
| `__final_boss__` | 進入最終 Boss 戰 |
| `__sacrifice__` | 死亡結局 |

---

## 9. 事件系統

### 9.1 事件類型

| event_type | 效果 | 關鍵參數 |
|------------|------|----------|
| `heal` | 回復 HP | `heal_pct`（佔最大 HP 百分比） |
| `card_reward` | 免費選牌加入牌庫 | `pick_from`（選擇數） |
| `card_reward_cost` | 付出 HP 換取選牌 | `cost_hp_pct` + `pick_from` |

### 9.2 選牌流程

1. 依職業篩選牌池（CLASS_EVENT_POOL 或 ADVANCED_CARD_POOL）
2. 從池中隨機抽取 `pick_from` 張
3. 顯示選項，玩家選一張
4. 新牌加入 `deck.all_cards`，永久保留至遊戲結束

---

## 10. 結局系統

### 10.1 結局列表

| 結局 ID | 名稱 | 觸發條件 |
|---------|------|----------|
| `ending_sacrifice` | 以身殉道 | 戰鬥失敗 |
| `ending_escape` | 全身而退 | 選擇「離開」選項 |
| `ending_warlord` | 梟雄之路 | 歷史含 `joined_warlord` |
| `ending_hermit` | 方外逍遙 | 歷史含 `found_hermit` |
| `ending_rebellion` | 振臂一呼 | 歷史含 `led_rebellion` |
| `ending_redemption` | 以德報怨 | 歷史含 `spared_enemy` |
| `ending_truth` | 真相大白 | 歷史含 `revealed_truth` |
| `ending_revenge` | 快意恩仇 | 歷史含 `took_revenge` |
| `ending_wanderer` | 天涯行者 | 歷史含 `stayed_wanderer` |
| `ending_sacrifice_hero` | 捨身取義 | 歷史含 `chose_sacrifice` |
| `ending_default` | 漂泊者 | 以上皆不符 |

### 10.2 歷史標記系統

`history` 為 `list[str]`，在旅途中逐漸累積標記：

- 從節點的 `history_flag` 欄位自動加入
- 從選項的 `chosen.next == "ending_escape"` 加入 `chose_escape`
- 從戰鬥逃跑加入 `escaped_battle`
- 幕標記格式：`act1:act1_market`

`determine_ending()` 依順序掃描 `history`，命中第一個符合條件的結局。

---

## 11. 難度設定

### 11.1 三種難度

| 難度 | 敵人 HP 係數 | 敵人 ATK 係數 | 說明 |
|------|------------|--------------|------|
| 普通 | × 1.0 | × 1.0 | 標準體驗 |
| 困難 | × 1.3 | × 1.2 | 敵人更強 |
| 地獄 | × 1.6 | × 1.5 | 極度挑戰 |

### 11.2 配置格式（config.json）

```json
{
  "difficulty": {
    "hp_mult": 1.0,
    "atk_mult": 1.0
  },
  "hand_size": 5,
  "base_energy": 3
}
```

---

## 12. 技術架構

### 12.1 目錄結構

```
mortal-road/
├── main.py                # 入口點：載入設定、選角、啟動引擎
├── config.json            # 難度與戰鬥全域設定
├── feedback.md            # 版本回饋追蹤
├── DESIGN.md              # 本文件
├── characters/
│   ├── __init__.py        # 匯出 CharacterBase 與 build_character()
│   ├── base.py            # CharacterBase：屬性、HP、傷害、狀態計算
│   ├── beggar.py          # 乞丐職業定義
│   ├── courtesan.py       # 花魁職業定義
│   ├── constable.py       # 捕快職業定義
│   └── taoist.py          # 道士職業定義
├── combat/
│   ├── __init__.py        # 匯出 Battle, BattleOutcome, build_enemy
│   ├── battle.py          # 戰鬥主迴圈、UI 顯示、效果結算
│   ├── card.py            # Card, CardEffect, build_card(), 牌池定義
│   ├── deck.py            # Deck：抽牌、出牌、回合重置、手牌顯示
│   └── enemy.py           # Enemy, build_enemy(), BOSS_POOL, 敵人行動
└── story/
    ├── __init__.py        # 匯出 StoryEngine
    ├── engine.py          # StoryEngine：導航、故事/戰鬥/事件/結局處理
    ├── graph.py           # StoryGraph：載入 nodes.json、幕節點索引
    ├── node.py            # StoryNode, Choice dataclass
    ├── endings.py         # ENDINGS 文字、determine_ending() 邏輯
    └── nodes.json         # 155 個故事節點資料（12 幕完整內容）
```

### 12.2 核心類別關係

```
main.py
  └─ StoryEngine(character, difficulty_cfg)
       ├─ StoryGraph → 讀取 nodes.json
       ├─ Deck(character.deck_ids)
       └─ Battle(character, enemy)
            ├─ Deck（共用，保留進階牌）
            └─ CardEffect（每張牌的效果計算）
```

### 12.3 資料流

```
nodes.json → StoryGraph.get(node_id) → StoryNode
StoryNode → StoryEngine._process() → 分派至對應 handler
handler → Battle / event effects / ending display
Battle → BattleOutcome → StoryEngine 決定下一節點
```

### 12.4 關鍵設計決策

| 決策 | 原因 |
|------|------|
| 牌庫跨戰鬥保留 | 進階牌構築是核心樂趣，死亡才重置 |
| Boss 遊戲開始時固定 | 避免玩家存檔重試選 Boss |
| history 線性列表 | 簡單夠用，結局判定依序掃描即可 |
| `{name}` 渲染時替換 | 資料層乾淨，展示層處理個人化 |
| pending queue 多牌 | 避免出牌後 index shift 造成的 bug |
