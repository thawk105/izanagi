---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-06
wave: dev-wave-t139-alt-x-probe
seq: 2
---

## {{D:t139-alt-x-partial-recovery}}. 代替 X (4 stripe・cache line 分離・固定回数 stripe 計算) は両 workload で部分回復し、生死確認は成立した — ただし J=1 の engineering screen であり正例 artifact ではない

**決定 (1): 代替 X は成立したと記録する。** ユーザー裁定「択 (a) = O(1) stripe 計算 + cache line
padding を備えた代替 X で probe を再走する」を実行し、事前登録した受理条件
「両 workload で全標本が `mode1 < modeX < stock`」を満たした。D126 が不成立と記録した前候補の
置き換えである。一次資料 = `output/insights/2026-08-05_t139-alt-x-probe/`。

**実測 (Pegasus gen_S request `892042`、trace-disabled、t48、2 workload × 3 arm × 5 rep):**

| workload | mode1 (劣化) | modeX (代替 X) | stock | modeX/mode1 | 回復率 |
|---|---|---|---|---|---|
| W1 高競合 write | 92,425 | 185,797 | 782,534 | 2.01x | 13.5% |
| W2 中競合 mixed | 1,024,233 | 2,383,734 | 10,434,011 | 2.33x | 14.4% |

前候補は W1 で 1.36x、**W2 で 0.85x と逆転**していた。

**決定 (2): stripe 数は 4 とし、その理由を「stock との分離」に置かない。** 親 brief は
「増やすと stock へ近づきすぎる」として 2 を選んだが、定量的に支持されない — stock/mode1 は
W1 で約 8 倍・W2 で約 10 倍あり、4 stripe でも上限側の余裕は十分である。下限側は 2 stripe だと
W2 で前候補の最良値から +17% を要し、余裕が小さい。加えて**回復幅が大きいほど標準化効果が大きく、
RF 統計設計が裁定した二段階設計 (大きい効果に絞る) の本走が成立しやすい**。
この選択は前回 raw だけを入力とし、**新しい走行の結果を見る前に**確定した。

**決定 (3): stripe 関数は先頭窓・中央窓・末尾窓・長さ・storage を固定回数 load で混ぜる。**
`transaction.cc` は YCSB 専用ではないため、可変長 key で退化しない形が要る。親が実測したところ、
**末尾窓だけ、および先頭窓 + 末尾窓 + 長さのいずれも、共通 prefix と共通 suffix を持つ同一長の
key 族では 100% が 1 stripe へ退化した**。中央窓を入れて最大 bucket 占有率 27.10% に収まった。
per-byte loop は持たない (YCSB の 8 byte key では従来の byte 走査が実質 O(1) と同じ回数になり、
「O(1) 化」が測定対象上で何も変えないため)。

**決定 (4): 本 study は engineering screen であり、適格性を主張しない。** J=1・未較正・
非適格として `verdict.tsv` と事前登録の双方に明示した。適格性の権威は独立 validator だけが持ち
(D162 決定 1・3)、その validator と consumer は未実装である。**したがって非発行の理由は
「権威境界が未裁定だから」ではなく「J=1 であり validator が無いから」である。**

**決定 (5): 機序の帰属をしない。** 本 study は cache line 分離・stripe 計算の固定回数化・
stripe 数の 3 つを同時に変えた。どれが効いたかは分離していない。ablation は別の事前登録 study とする。

**決定 (6): 実装と事前登録を実走前に commit し、実走を commit へ束縛する。** job は投入時に渡した
期待 commit と job 開始時の HEAD の exact 一致を要求し、その commit の blob だけを展開する。
依存は pin の Git object から不変 snapshot を作り、書き込み用の複製と bytes 同一性を照合する。
queue 待ちの間に HEAD が進んでも、投入した identity 以外は実行されない。

**却下した案:** (a) 第 4 arm として旧候補を残す — run 数・liveness 件数・受理条件が変わり、
事前登録する問い自体が変わる。(b) 共有 policy の依存 path を書き換える — 凍結済み証拠が
その sha256 を pin しており、他タスクの証拠を壊す (D107 / D110 が既に却下した型)。
(c) 結果を見てから stripe 数や workload を変える — 事後調整であり D126 決定 (4) に反する。

**研究状態への影響:** certified 選択、材料レポート、proof chain、凍結 bytes、既存 gate は
いずれも不変である。probe は gate を新設せず受理集合を変えないため**変異 matrix は対象外**。
変わるのは、[T-139] の状態が「代替 X の設計待ち」から「**生死確認は成立、後続は RF 統計設計に
準拠した本走の設計**」へ進んだことである。
