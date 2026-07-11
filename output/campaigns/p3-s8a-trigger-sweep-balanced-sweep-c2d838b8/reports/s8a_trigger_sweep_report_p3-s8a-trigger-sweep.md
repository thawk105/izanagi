# s8a trigger-gating sweep 偵察レポート — workload=balanced trial=p3-s8a-trigger-sweep

**位置づけ:** 偵察 (preliminary、事前登録外カテゴリ)。断定 verdict なし。
**限定 (必読):** (1) 失敗条件 (c) の判定は出さない。(2) floor 0.030 は参考線 — high-abort 点 (退化点 + abort 率が基準 ident_all 比 2.0 倍超) は floor 未較正 = 判定不能 (fails-closed)。read-heavy の floor は rr95 genuine-between 未較正の残存リスクを負う (fresh 実測は 0.030 内だが下限値 — レビュー F3/STAT-2)。(3) 本 sweep は fairness 偏向 (D41 型 15) を検出しない。(4) write-heavy/read-heavy の S2 verify は rr50 固定 (off-workload 被覆)。(5) 素の sweep は適応 Backoff_ との連成地形 — gate 単独の帰属は曇る (magnitude 軸との直交性主張は adaptive-off 前提の限定付き)。(6) firewall: E 段へは軸の生死二値のみ・段 6 正式 grid へ材料流用しない。本偵察 insight を見て E 段入力を起草する記憶汚染は既知残存リスク — 偵察を見た事実を E 段 campaign provenance に情報源として記録する (D46 (a) のループ版)。(7) 本軸は 8a (post-coder) 由来 — 探索補助限定・段 6 headline 非対象 (D47 決定 5)。(8) 単一 campaign の floor 超は候補提示のみ — 生死二値の確定は cross-run 再測 (当該点 + ident_all の --remeasure) 後 (レビュー MS-2/STAT-3)。

| 点 | 分類 | median tps | CV% | abort率 | unstable | certified | 備考 |
|---|---|---:|---:|---:|---|---|---|
| g_none | degenerate | 2,764,393 | 1.90 | 70.17 |  | ✓ | high-abort/未較正: floor 判定不能 |
| g_rl | subset | 1,705,451 | 0.84 | 24.83 |  | ✓ |  |
| g_lc | subset | 1,616,973 | 1.05 | 22.17 |  | ✓ |  |
| g_lc+rl | subset | 1,301,704 | 0.64 | 19.21 |  | ✓ |  |
| g_rt | subset | 961,862 | 1.96 | 18.27 |  | ✓ |  |
| g_rt+rl | subset | 947,234 | 0.79 | 19.14 |  | ✓ |  |
| g_lc+rt | subset | 930,077 | 0.87 | 18.91 |  | ✓ |  |
| ident_all | control-identity | 924,221 | 3.26 | 20.58 |  | ✓ | 基準 (恒等 gate、フラグ 1) |
| g_lc+rt+rl | subset | 908,079 | 2.04 | 19.64 |  | ✓ |  |
| stock | stock | — | — | — |  | ✗ | stock (フラグ 0) — 骨格コスト別掲用; ABORT: build-error |

**subset 点 (stable かつ floor 較正済み, n=7):** max=g_rl 1,705,451 tps / min=g_lc+rt+rl 908,079 tps / レンジ +87.81% (選択バイアス無補正の記述統計 — floor との断定比較は cross-run 再測点のみ)
**best vs 基準 (ident_all):** g_rl +84.53% (参考線: floor ±3.0%。未再測 = 位置関係は暫定)
**不感縮約の backstop (実効全集合 g_lc+rt+rl vs ident_all):** -1.75% — 一次証拠は頻度実測の count=0 でありこれは低 power の backstop。floor 超の不一致を観測したら不感判定の誤りを疑い頻度実測へ差し戻す (またはノイズ再測)。floor 内でも同値の証明ではない
**退化点 (別掲、レンジ集計外):** g_none 2,764,393 tps
