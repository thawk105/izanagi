# [T-2865] 段 4 裁定 (親) — plan v2 と変異の事前登録

入力: brief.md、codex/s3-consult-A.md (adopt_with_conditions)、codex/s3-consult-B.md (adopt_with_conditions)。裁定 inbox 再走査 (新着なし)、local main 620a6bb13 (不動)。

## 1. 所見の裁定

| 所見 | 判定 | 採否 | 成果物影響 (1 行) |
|---|---|---|---|
| A1 fixed10 の実効 define を検査し不一致なら停止 | real (patch 無しで -DCCBENCH_BACKOFF_FIXED は無言で無視されうる。model.py:84 の写像と patch:19 の配線を確認) | 採用 | 放置時、fixed10 の値が適応 stock の値にすり替わり全 IR 点の分母が変わる |
| A2 / B1 参照 3 本のどれかが不適格なら「最良参照比」は null | real | 採用 | 放置時、欠けた参照を除いた最大で比が過大になり超過点数が増える |
| A3 比較集計で fixed10 の genome・非空の前後 source evidence・実効 define を照合 | real | 採用 (段階 D aggregate の照合の写しに fixed10 を足すだけ) | 放置時、別 genome の行が最良参照として数えられる |
| A4 / B2 再測 1 点の射程 | real | 再測を実装しない (下記 P3) で解消 | — |
| A5 出力 path を比較専用に | real (運用) | 採用。比較集計は投影を書かない。path は親が `.../silo_function_policy_recon/compare/` に固定。コードの path gate は足さない (仮想リスク) | 放置時、projection.json が上書きされ後段入力が変わる |
| B3 巡回順の効能を狭く記す | real | 採用 (insight の文言) | — |
| B4 見積り下限の訂正 | real | 採用 (下記 P4) | — |
| B5 完了文を射程に合わせる | real | 採用 | — |
| B「削れるもの」: 新 subcommand でなく既存 aggregate の拡張 | 一部 refuted | 別 subcommand `compare-aggregate` とする (既存 aggregate は段階 D の 8 job 形と投影書き込みに固定され、拡張すると段階 D の記録の再計算経路を変える)。ただし照合 helper は共有してよい | — |

## 2. plan v2

- **P1 (確定):** IR 点 x (job j) について、x・同 job の abort0・stock・B0-L-W0・fixed10 のすべてが適格 (`_eligible`) で、x が high-abort でない (abort 率 ≤ 同 job abort0 の 2 倍) ときだけ `best_ref_ratio = median(x) / max(median(stock), median(B0-L-W0), median(fixed10))` を出す。どれか欠ければ null (false・負けに数えない)。参照ごとの比 `ratio_vs[ref]` も、その参照と x が適格なら別掲する。`exceeds = best_ref_ratio > 1.03` は探索的な目印 (未較正の暫定床・16 点からの最大選択は未補正) として記す。集計の要約 = 適格点数・null 件数 (理由別)・超過点数・最大の best_ref_ratio。
- **P2 (確定):** job j の実行順 = 基本列 [IR(小さい ID), IR(bit 反転), abort0, stock, B0-L-W0, fixed10] を j 位置だけ左へ巡回。結果の `case_order` に残し、集計で予定順と照合する。効能は「参照の位置を job 間で分散する」だけと記す (候補ごとの位置交絡は残る)。
- **P3 (確定): 再測は実装しない。** 裁定 D2235 項 7 は「小比較を 1 回」。初走の超過は探索的観測として報告し、再測するかは段階 E の判断と併せてユーザーへ返す。
- **P4 (確定、投入前にユーザー確認):** 1 job (6 方策) ≈ 650〜830 秒 × 8 = 1.44〜1.84 node 時間。検査: 焦点走 ≈ 0.07 (段階 D 4 回 253 秒)、変異 ≈ 0.3 (段階 D は 18 変異で 2,029 秒 = 待ち行列込みの上限値。本 wave 9 変異)、受入 ≈ 0.25 (2026-09-22 の実測単価、段階 D の記録には無い)。合計 ≈ 2.06〜2.46 node 時間。walltime 上限 30 分 × 8 = 4.0 + 検査で上限 ≈ 4.6。2 以上なので計測の投入前にユーザー確認。実装子の稼働と確認は並行し、確認前は計算ノードへ何も投げない (焦点走も含む)。

## 3. 実装の範囲 (実装子 1 本、所有 path)

- `orchestrator/campaign/silo_policy_coverage.py`: `_source(..., backoff_fixed_patch: bool = False)` — stock 木にだけ `patches/silo-backoff-fixed.patch` を当て、当てた木で `backoff_extended_sweep._BACKOFF_FIXED_PATCH_MARKERS` と同じ marker を確認 (既存関数 `_assert_backoff_fixed_materialized` を import して使ってよい)。`_build_variant(..., stock_backoff_fixed: int | None = None)` — stock 時だけ genome に `BACKOFF_FIXED` を足す。非 stock での指定は ValueError。既存の呼び出し (引数なし) の挙動・configure argv は bytes 不変。
- `orchestrator/campaign/silo_policy_recon.py`: `_cases("compare", job, None)` (P2 の順)、role `fixed10` (`_one` で stock 系として patch 付き source と `BACK_OFF=1, BACKOFF_FIXED=10` の genome)、trace1・trace0 の両 build 後に owner TU の compile command の引数に `-DBACKOFF_FIXED=10` と `-DBACK_OFF=1` が正確に 1 回ずつあることを検査し、無ければ status `backoff-fixed-not-effective` で bench せず停止 (行に command を残す)。`main` の `run --phase compare`。新 subcommand `compare-aggregate --compare <8 files> --out <file>` (投影なし): schema/PIN/toolchain/固定 workload の一致、8 job の distinct と (hostname, started_at) の distinct、各 job の case 列と role 列と予定順の一致、IR 本文 sha256・因子、abort0 本文 sha256、stock・B0-L-W0・fixed10 の genome flags、全行の非空の前後 source evidence 一致、fixed10 の実効 define 記録、を照合してから P1 を計算。
- 既存の段階 D の `run --phase initial/remeasure`・`aggregate` の挙動と出力は不変。
- tests: `orchestrator/tests/test_silo_policy_recon.py`・`test_silo_policy_coverage.py`、行番号 pin の追随だけ `orchestrator/tests/test_ccbench_spawn_sites.py` (期待値の意味は変えない)。

### DW-O13 (検査入力の実在)

実効 define 検査の入力 = trace build の `compile_commands.json` の owner TU (axis.SOURCE_REL) の引数。段階 D の `initial-0.json` の `trace0.command` は 4 行とも `-DBACK_OFF=1` を持ち (jq で実測)、これは `ccbench_universal_definitions` (cmake/Options.cmake:60、cc/silo/CMakeLists.txt:18 で使用) 由来。patch はこの関数へ `BACKOFF_FIXED=${CCBENCH_BACKOFF_FIXED}` を足すので、`-DBACKOFF_FIXED=10` は同じ引数列に到達可能。正例 = patch 付き source + BACKOFF_FIXED=10 の実 configure (焦点走で確認)。負例 = patch なし source (define が載らない)。

## 4. 変異の事前登録 (DW-M01、9 本)

| ID | 位置 | 壊し方 | 期待 (kill する test の性質) |
|---|---|---|---|
| m-fx-flag | recon `_one` の fixed10 genome | BACKOFF_FIXED を落とす / 値を変える | fixed10 の genome・configure に BACKOFF_FIXED=10 を要求する test |
| m-fx-patch | coverage `_source` | backoff_fixed_patch を無視 (patch を当てない) | patch 付き source に marker があることの test |
| m-fx-define | recon の実効 define 検査 | 検査を常に真 | define の欠けた compile command で `backoff-fixed-not-effective` になる test |
| m-cmp-max | compare-aggregate の分母 | max → min | 分母が最良参照である test |
| m-cmp-null | 同 | 参照不適格時に残りの参照で計算 | 1 参照不適格で best_ref_ratio が null の test |
| m-cmp-order | 同 | 予定順照合を外す | 順序違いの入力で error の test |
| m-cmp-fxflags | 同 | fixed10 の genome 照合を外す | fixed10 flags 不一致で error の test |
| m-rotation | `_cases("compare")` | 巡回しない | job ごとの予定順の test |
| m-cmp-floor | compare-aggregate の超過判定 | `> 1.03` → `> 1.0` | 境界 (1.02) の test |

各変異の単一理由性 (前後・内側の別層が先に拒否しない) は実装後に確認し、成立しなければ登録を外して erratum に書く。期待 node は実装後の probe (dispatch、全件 SURVIVED) で観測した完全集合。
