# s8a trigger-gating sweep 偵察レポート — workload=read-heavy trial=p3-s8a-trigger-sweep

**位置づけ:** 偵察 (preliminary、事前登録外カテゴリ)。断定 verdict なし。
**限定 (必読):** (1) 失敗条件 (c) の判定は出さない。(2) floor 0.030 は参考線 — high-abort 点 (退化点 + abort 率が基準 ident_all 比 2.0 倍超) は floor 未較正 = 判定不能 (fails-closed)。read-heavy の floor は rr95 genuine-between 未較正の残存リスクを負う (fresh 実測は 0.030 内だが下限値 — レビュー F3/STAT-2)。(3) 本 sweep は fairness 偏向 (D41 型 15) を検出しない。(4) write-heavy/read-heavy の S2 verify は rr50 固定 (off-workload 被覆)。(5) 素の sweep は適応 Backoff_ との連成地形 — gate 単独の帰属は曇る (magnitude 軸との直交性主張は adaptive-off 前提の限定付き)。(6) firewall: E 段へは軸の生死二値のみ・段 6 正式 grid へ材料流用しない。本偵察 insight を見て E 段入力を起草する記憶汚染は既知残存リスク — 偵察を見た事実を E 段 campaign provenance に情報源として記録する (D46 (a) のループ版)。(7) 本軸は 8a (post-coder) 由来 — 探索補助限定・段 6 headline 非対象 (D47 決定 5)。(8) 単一 campaign の floor 超は候補提示のみ — 生死二値の確定は cross-run 再測 (当該点 + ident_all の --remeasure) 後 (レビュー MS-2/STAT-3)。

| 点 | 分類 | median tps | CV% | abort率 | unstable | certified | 備考 |
|---|---|---:|---:|---:|---|---|---|
| g_none | degenerate | 8,348,300 | 0.14 | 15.86 |  | ✓ | high-abort/未較正: floor 判定不能 |
| g_lc | subset | 7,131,426 | 0.35 | 13.58 |  | ✓ | high-abort/未較正: floor 判定不能 |
| g_rl | subset | 3,783,945 | 0.38 | 7.80 |  | ✓ |  |
| g_lc+rl | subset | 3,707,666 | 0.36 | 7.63 |  | ✓ |  |
| g_rt | subset | 2,063,099 | 1.17 | 4.80 |  | ✓ |  |
| g_lc+rt | subset | 2,059,525 | 0.74 | 4.77 |  | ✓ |  |
| g_lc+rt+rl | subset | 1,917,500 | 1.20 | 4.56 |  | ✓ |  |
| ident_all | control-identity | 1,902,874 | 1.20 | 4.48 |  | ✓ | 基準 (恒等 gate、フラグ 1) |
| g_rt+rl | subset | 1,902,665 | 1.14 | 4.51 |  | ✓ |  |
| stock | stock | 1,892,473 | 0.75 | 4.51 |  | ✓ | stock (フラグ 0) — 骨格コスト別掲用 |

**subset 点 (stable かつ floor 較正済み, n=6 / 判定不能 1 点は除外):** max=g_rl 3,783,945 tps / min=g_rt+rl 1,902,665 tps / レンジ +98.88% (選択バイアス無補正の記述統計 — floor との断定比較は cross-run 再測点のみ)
**best vs 基準 (ident_all):** g_rl +98.85% (参考線: floor ±3.0%。未再測 = 位置関係は暫定)
**骨格常駐コスト (別掲):** ident_all vs stock = +0.55% (フラグ 1 恒等 gate の 7 store + 1 分岐が乗る側 − 素の stock。軸の固定費)
**不感縮約の backstop (実効全集合 g_lc+rt+rl vs ident_all):** +0.77% — 一次証拠は頻度実測の count=0 でありこれは低 power の backstop。floor 超の不一致を観測したら不感判定の誤りを疑い頻度実測へ差し戻す (またはノイズ再測)。floor 内でも同値の証明ではない
**退化点 (別掲、レンジ集計外):** g_none 8,348,300 tps
