# 事前登録表 (確定、段 4 裁定 2026-09-23 21:05 JST。投入後は変えない)

出所: prereg-draft.md を段 3 相談 (codex/s3-consult.md、所見 1〜9 全採用) で改めたもの。

## 共通条件

- source: CCBench pin e9e477ca + `patches/broken-silo-sort-nonswo.patch` を `patchharness.applied` (git apply、fuzz なし) で当てた木。R1〜R4 の 2 build はこの 1 つの適用文脈の中で作る。
- gate: `s5_permutation_coverage._require_condition_gate(sub, "SORT_VARIANT")` (request 値 1・既定 0) を同じ適用木で評価し、admitted であること。gate 通過は「供給経路が効く」ことの証拠であり、V07 の挙動の証拠には数えない。
- build: `s5_permutation_coverage._build_broken` と同じ cmake argv (Release・`-DENABLE_SANITIZER=OFF`・compiler 明示・`STOCK_G.cmake_defines()`・`-DCCBENCH_TRACE=1`) のうち `-DCMAKE_CXX_FLAGS=-D<macro>=1` だけを `-DCCBENCH_SORT_VARIANT=<v>` に置き換える。壊し = v=1、stock = v=0。
- build の記録 (欠ければ job 全体を「その他 (未実走)」): configure argv、`CMakeCache.txt` の `CCBENCH_SORT_VARIANT` の値、`ycsb_silo.exe` target の実コンパイル定義 (flags.make の CXX_DEFINES 行) と CXX_FLAGS 行、binary の sha256。CXX_DEFINES の `SORT_VARIANT` が v と一致しなければ走らせない。
- workload W(n): `thread_num=1`・`ycsb_tuple_num=200`・`ycsb_zipf_skew=0`・`ycsb_rratio=0`・`ycsb_rmw=true`・`ycsb_max_ope=n`・`extime=1`・`clocks_per_us=2100`。run の timeout は 120 s (s5 の `RUN_TIMEOUT_S`)。
- 実行順 R1 → R2 → R3 → R4。
- 到達の証拠: trace の C 行 `write_count` の最大値。これは**commit まで届いた取引**の write set の大きさであり、hang・中断した取引の大きさは示さない。timeout した run では「kill 前に出力された完了済み prefix の参考値」としてだけ記録し、分類に使わない。
- timeout した run は verifier にかけない (verdict 無し)。

## run と期待

| run | build | workload | 期待 (層・verdict) | 役割 |
|---|---|---|---|---|
| R1 | stock (v=0) | W(16) | rc=0、serializable・certified、巡回 0・X 0・P 0・integrity 全 0、C 行 write_count 最大 = 16 | R3 の対照 |
| R2 | stock (v=0) | W(17) | 同上、write_count 最大 = 17 | R4 の対照。W(17) が 17 要素の write set を commit まで作れることの証拠 |
| R3 | 壊し (v=1) | W(16) | rc=0、serializable・certified、P 0、write_count 最大 = 16 (libstdc++ 11 は要素数 ≤ 16 では guarded な insertion sort) | 16 要素境界の追加検証。D42・設計書の記録「16 以上で hang」と source 読みの弁別。V07 の分類の必須条件ではない |
| R4 | 壊し (v=1) | W(17) | 17 要素で `__unguarded_partition` の範囲外走査 = 未定義動作。**主予測は hang (120 s で timeout、verdict 無し)** (D42 の release / ASan の実機記録)。GCC の前進仮定で別の壊れ方もありうるので、他の観測も下で分類を固定する | **V07 の本行** |

## 分類 (上から順に最初に当たった規則を採る。観測後に規則を選ばない)

**段 A — 基盤 (job 全体):** patch 不適用・gate 不 admitted・build 失敗・build の記録欠落・CXX_DEFINES 不一致 → R1〜R4 すべて「その他 (未実走)」。基盤の失敗に限り、同じ argv で 1 回だけ再投入してよい。patch・workload・timeout・期待・分類は変えない。

**段 B — 対照 (R1・R2):**
1. rc=0・verifier の失敗でない・空履歴でない・S・巡回 0・X 0・P 0・integrity 全 0・write_count 最大 = n → 「期待どおり (対照)」
2. timeout・rc≠0・verifier の失敗・空履歴 → 「その他 (対照不成立)」
3. rc=0 で I または N → 「誤検出」
4. それ以外 (S だが write_count 最大 ≠ n・取得不能、S だが integrity 非 0 など) → 「その他 (対照不成立)」

**段 C — R3 (R1 が「期待どおり (対照)」でなければ R3 は「その他 (対照不成立)」):**
1. timeout → 「その他 (16 要素で停止 = 記録の境界どおり、source 読みの予測外)」
2. signal による終了 (rc < 0) → 「別の層で検出 (process の異常終了)」
3. rc > 0 → 「その他 (帰属不明の異常終了)」
4. rc=0 で verifier の失敗 / 解析不能 / 空履歴 → 「その他」
5. rc=0 で I または N → 「別の層で検出 (verifier)」
6. rc=0 で S かつ write_count 最大 = 16 → 「期待どおり (16 要素では S)」
7. rc=0 で S かつ write_count 最大 < 16 または取得不能 → 「その他 (条件未到達)」

**段 D — R4 (R2 が「期待どおり (対照)」でなければ R4 は「その他 (対照不成立)」):**
1. timeout → 「期待どおり (hang。verifier の判定は無く、止めたのは timeout = 盲点)」
2. signal による終了 (rc < 0) → 「別の層で検出 (process の異常終了)」
3. rc > 0 → 「その他 (帰属不明の異常終了)」
4. rc=0 で verifier の失敗 / 解析不能 / 空履歴 → 「その他」
5. rc=0 で I または N → 「別の層で検出 (verifier)」
6. rc=0 で S かつ write_count 最大 ≥ 17 → 「未発生 (17 要素の取引が commit し S = 盲点の S)」
7. rc=0 で S かつ write_count 最大 < 17 または取得不能 → 「その他 (条件未到達)」

「S」は verdict = serializable かつ certified。「I / N」は verdict = indeterminate / non-serializable。
「verifier の失敗」= 呼び出しの例外 (timeout を含む)・rc ∉ {0, 1, 3}・stdout が JSON でない・`results` が 1 件でない・rc と verdict の対応 (0 ↔ S、1 ↔ N、3 ↔ I、`orchestrator/verifier/cli.py` 冒頭) が崩れている、のいずれか。
「空履歴」= verifier の `stats.txns` = 0 (commit した取引が 0 件)。

## 計算

1 job、walltime 00:30:00。期待値は gate + 2 build + run 4 本 (うち最大 1 本が 120 s の timeout) + verifier 最大 4 本で 5〜8 分 (前回 s5 job の Elapse 134 s が基準)。上限は walltime の 0.5 node 時間で、2 node 時間を超えない。
