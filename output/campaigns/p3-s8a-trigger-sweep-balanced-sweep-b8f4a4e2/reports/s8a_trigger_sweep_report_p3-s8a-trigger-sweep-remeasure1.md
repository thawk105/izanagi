# s8a trigger-gating sweep 偵察レポート — workload=balanced trial=p3-s8a-trigger-sweep-remeasure1

**位置づけ:** 偵察 (preliminary、事前登録外カテゴリ)。断定 verdict なし。
**限定 (必読):** (1) 失敗条件 (c) の判定は出さない。(2) floor 0.030 は参考線 — high-abort 点 (退化点 + abort 率が基準 ident_all 比 2.0 倍超) は floor 未較正 = 判定不能 (fails-closed)。read-heavy の floor は rr95 genuine-between 未較正の残存リスクを負う (fresh 実測は 0.030 内だが下限値 — レビュー F3/STAT-2)。(3) 本 sweep は fairness 偏向 (D41 型 15) を検出しない。(4) write-heavy/read-heavy の S2 verify は rr50 固定 (off-workload 被覆)。(5) 素の sweep は適応 Backoff_ との連成地形 — gate 単独の帰属は曇る (magnitude 軸との直交性主張は adaptive-off 前提の限定付き)。(6) firewall: E 段へは軸の生死二値のみ・段 6 正式 grid へ材料流用しない。本偵察 insight を見て E 段入力を起草する記憶汚染は既知残存リスク — 偵察を見た事実を E 段 campaign provenance に情報源として記録する (D46 (a) のループ版)。(7) 本軸は 8a (post-coder) 由来 — 探索補助限定・段 6 headline 非対象 (D47 決定 5)。(8) 単一 campaign の floor 超は候補提示のみ — 生死二値の確定は cross-run 再測 (当該点 + ident_all の --remeasure) 後 (レビュー MS-2/STAT-3)。

| 点 | 分類 | median tps | CV% | abort率 | unstable | certified | 備考 |
|---|---|---:|---:|---:|---|---|---|
| g_rl | subset | 1,706,192 | 0.68 | 24.69 |  | ✓ |  |
| g_lc | subset | 1,597,767 | 0.80 | 22.43 |  | ✓ |  |
| stock | stock | 904,493 | 1.60 | 20.16 |  | ✓ | stock (フラグ 0) — 骨格コスト別掲用 |
| ident_all | control-identity | 893,271 | 2.51 | 19.70 |  | ✓ | 基準 (恒等 gate、フラグ 1) |

**subset 点 (stable かつ floor 較正済み, n=2):** max=g_rl 1,706,192 tps / min=g_lc 1,597,767 tps / レンジ +6.79% (選択バイアス無補正の記述統計 — floor との断定比較は cross-run 再測点のみ)
**best vs 基準 (ident_all):** g_rl +91.00% (参考線: floor ±3.0%。未再測 = 位置関係は暫定)
**骨格常駐コスト (別掲):** ident_all vs stock = -1.24% (フラグ 1 恒等 gate の 7 store + 1 分岐が乗る側 − 素の stock。軸の固定費)
