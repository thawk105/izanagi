# [T-2849] (3) MOCC 疎通 本投入の見積り (2026-09-26 22:45 JST、job Elapse の実測単価、D2212 項 4)

## 単価 (単価実測 3 job、submit-tree 6c3913bc5、trace 保全有効、stock 1 session)

| workload | request | 判定 | tps | slot wall | job Elapse | job の固定費 (Elapse − slot) | 保全量 |
|---|---|---|---:|---:|---:|---:|---:|
| write-heavy (同時検査、D2251) | 30084 | certified・normal | 1,230,349 | 212.2 s | 244 s | 32 s | 522 MB |
| balanced (直列検査) | 30086 | certified・normal | 822,729 | 346.3 s | 380 s | 34 s | 714 MB |
| read-heavy (直列検査) | 30087 | certified・normal | 2,399,092 | 759.6 s | 792 s | 32 s | 2.4 GB |

単価実測の計 1,416 s = 0.39 node 時間。前回 wave の write-heavy 系列 (直列検査・保全なし) では候補 slot は stock slot 以下 (288〜320 s vs 332 s)。

## 案 A (推奨): 20 候補 / workload

各 workload: 5 手法 × 1 系列 (A = 6、B = 2、N_eval = 1) → 系列ごとに stock 1 + 初期点 2 + 探索 2 + endpoint 1 = 6 slot、+ block 対照 1 slot = 31 slot。候補評価 = 5 × (2 + 2) = 20。

| workload | slot | 評価 (slot × 単価) | job 固定費 (6 job) | 計 |
|---|---:|---:|---:|---:|
| write-heavy | 31 | 6,578 s | 192 s | 6,770 s (1.88 h) |
| balanced | 31 | 10,735 s | 204 s | 10,939 s (3.04 h) |
| read-heavy | 31 | 23,548 s | 192 s | 23,740 s (6.59 h) |
| 計 | 93 | | | 41,449 s (11.5 h) |

- llm 系列 3 本は提案待ちの間も node を握る: 提案 2 + critic 1 / 系列、1 機会の実測がないため 1 機会 5〜25 分と置くと +0.5〜2.5 h。
- 候補 slot が stock より短ければ下がる (−10% で約 −1.1 h)。
- **中心 約 12.5、幅 約 10〜14 node 時間。** 受入 1 回 約 0.3。壁時計は node が空けば 2〜4 時間 (18 job 同時)。
- 保全量: slot 単価 × 93 ≈ 16 + 22 + 75 ≈ 113 GB (/work の空き 81 TB)。
- LLM: 3 系列 × (提案 2 + critic 1) ≈ 9 回の役割起動 (planner・coder・critic)。週枠 429 に当たると llm 系列だけ欠測になる。

## 案 B: 40 候補 / workload (B = 6)

系列 10 slot × 5 + 1 = 51 slot / workload → 評価 68,187 s + 固定費 → 約 19 h、llm の待ち +1.5〜7 h → **約 20〜26 node 時間**。

## 案 C: write-heavy と balanced だけ (案 A の規模)

約 4.9 h + llm の待ち 0.3〜1.7 h → **約 5〜7 node 時間**。read-heavy は後日。

## 同時検査を read-heavy・balanced に広げる案 (採らない、P1)

read-heavy の 760 s のうち直列検査が大半で、同時化で約 3〜4 node 時間減りうるが、`--verify-performance-concurrent` は write-heavy 限定 (D2251) で、
広げるにはコード変更 (Codex author・変異・受入) と記憶量・静定上限の実測が要る。疎通 1 回の節約より準備費が大きいので本 wave では採らない。
