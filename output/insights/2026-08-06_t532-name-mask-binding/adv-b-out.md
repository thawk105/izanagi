静的検査のみ実施した。pytest・import smoke は走らせていない。

## 到達層の棚卸し

| 層 | `name` / `gate_predicate` の扱い | 本 wave の検査 |
|---|---|---|
| known 凍結生成・schema | 両方を読む。生成は [`_trigger_entries`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s1_known_axes_freeze.py:501)、検証は [`_validate_schema`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s1_known_axes_freeze.py:725) | 入る |
| T-080 static adapter | `_verify_known_schema` が repin 投影後に `_validate_schema` を呼ぶ ([t080_freeze_migration.py:1803](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/t080_freeze_migration.py:1803)、[同:2084](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/t080_freeze_migration.py:2084)) | 呼出しは実在 |
| measurement 凍結 | known を legacy 検証後、variant 全体と `s1b_pairing` を複製する ([s1_measurement_freeze.py:156](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s1_measurement_freeze.py:156)、[同:181](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s1_measurement_freeze.py:181)) | 呼ばれるが legacy は drift-red |
| holdout 凍結 | known を直接読み、6 entry を複製する ([s8b_holdout_freeze.py:472](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s8b_holdout_freeze.py:472)、[同:524](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s8b_holdout_freeze.py:524)) | 通らない |
| ratified 凍結 | known は source blob hash、entry は canonical hash として扱い、name-mask は解釈しない ([s8b_ratified_freeze.py:948](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s8b_ratified_freeze.py:948)、[同:1691](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s8b_ratified_freeze.py:1691)) | 通らない |
| oracle 実体化 | 外側の `configuration_id` で entry を選び、実際の `gate_predicate` を materialize。`name` は実装選択に使わない ([s8b_materialization.py:103](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s8b_materialization.py:103)、[s1_direct_comparison.py:526](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s1_direct_comparison.py:526)) | driver の上流 gate に依存 |
| manifest・report・試行台帳・judge | `configuration_id` と `entry_sha256` を運ぶ。inner `name` 欄はない ([s8b_oracle_manifest.py:54](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s8b_oracle_manifest.py:54)、[s8b_oracle_driver.py:1308](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s8b_oracle_driver.py:1308)、[s8b_oracle_judge.py:248](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s8b_oracle_judge.py:248)) | 独自には通らない |
| selector | `c04 → system_gate` の固定対応。variant binding 全体は hash に入るが意味検査しない ([s8b_selector_input.py:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s8b_selector_input.py:22)、[s8b_selector_freeze.py:311](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s8b_selector_freeze.py:311)) | 通らない |
| 材料レポート・layer3 | S-1 report は `comparison_id`、oracle report は `configuration_id` を表示。layer3 は trigger binding 行を読み飛ばす ([s1_report.py:925](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s1_report.py:925)、[layer3_report.py:109](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/layer3_report.py:109)) | 独自には通らない |
| `p3_s4_loop*`・pipeline・loop・wal | known の `name` ではなく、IR mask と emitter predicate/source の前向き束縛を検査 ([p3_s4_loop_trigger_gating.py:399](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/p3_s4_loop_trigger_gating.py:399)、[pipeline.py:71](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/pipeline.py:71)、[wal.py:827](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/wal.py:827)) | 同じ性質ではない |

## 所見 1 — DW-G05 の「g_rl/name が最終三成果物へ流れる」は実装と一致しない

**種別:** 成果物影響

**根拠:** brief は「`certified 選択の構成名・材料レポートの gate 記述・試行台帳の name 欄`」とする ([brief.md:62](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t532-name-mask-binding/brief.md:62))。しかし trial-start は逐語的に `"holdout_id", "configuration_id", "attempt"` のみ ([s8b_oracle_driver.py:1308](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s8b_oracle_driver.py:1308))、judge 出力も `"winner_configuration_id"` ([s8b_oracle_judge.py:248](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s8b_oracle_judge.py:248))。さらに現 checkout は「**certified 選択の consumer が存在しない**」([docs/worklog.md:748](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/docs/worklog.md:748)、[layer3_report.py:517](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/layer3_report.py:517))。

**成果物影響:** 食い違った predicate は実際の binary、`src_token`、`variant_id`、throughput、将来の `system_gate` median／winner を変えうる。また inner entry 全体の `entry_sha256` と selector の `binding_entry_sha256` は変わる。一方、試行台帳に `name="g_rl"` は記録されず、最終 key は常に `system_gate` であり、現時点では certified 選択値自体が存在しない。

**重大度:** must-fix（GO を止める）

**提案:** DW-G05 を「D50 が選んだ `system_gate` の意図実装と、実際に materialize される predicate が乖離し、hash・実測値・将来の `system_gate` 判定が変わる」に直す。`g_rl` 名の最終行、trial ledger の name 欄、現行 certified 到達は削除する。

## 所見 2 — `_validate_schema` は本番で呼ばれるが、現行 official 受理集合を一件も狭めない

**種別:** 本番非到達

**根拠:** 呼出しは実在する。T-080 は逐語的に `known_module._validate_schema(projected_known)` を呼び ([t080_freeze_migration.py:1812](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/t080_freeze_migration.py:1812))、oracle は最初に `verify_receipt` を解決する ([s8b_oracle_driver.py:97](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s8b_oracle_driver.py:97))。しかし現 freeze は `"floor": null`, `"budget": null` ([holdout_freeze.json:622](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/output/s8b-freeze/holdout_freeze.json:622)) で、正本も「official の受理集合は空集合のまま」と明記する ([docs/phase3.md:109](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/docs/phase3.md:109))。

**成果物影響:** 本 wave の有無で現行 certified 選択、oracle 材料レポート、official 試行台帳の受理値は変わらない。変わりうるのは拒否集合内の追加診断だけである。したがって plan の「本番到達に十分」([plan-out.md:254](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t532-name-mask-binding/plan-out.md:254)) は、呼出し可能性から将来の certification 防御へ一般化し過ぎている。

**重大度:** must-fix（P3 の根拠記述について GO を止める）

**提案:** P3 を「legacy exact known 文書を検査する dormant gate」と限定し、official 解禁／ratified 世代移行時にこの検査が実効受理集合を狭めることを T-531 の受入条件へ置く。現時点で誤 certification 経路を閉じたとは書かない。

## 所見 3 — legacy consumer への「波及」は受理変更でなく拒否理由の優先順位変更だけである

**種別:** 本番非到達

**根拠:** legacy `verify_document` は `_validate_schema(doc)` の後、live generator SHA を照合する ([s1_known_axes_freeze.py:740](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s1_known_axes_freeze.py:740))。凍結値は `1d4d45a3…` ([known_axes_freeze.json:5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/output/s1-freeze/known_axes_freeze.json:5))、静的 `sha256sum` では live が `a7505a96…` だった。caller は measurement ([s1_measurement_freeze.py:156](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s1_measurement_freeze.py:156))、extime ([s1_verify_extime_calibration.py:202](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s1_verify_extime_calibration.py:202))、oracle の adapter 非発火時 fallback ([s8b_oracle_driver.py:406](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s8b_oracle_driver.py:406))。

**成果物影響:** mismatched 文書なら新 schema 診断が generator drift より先に出るが、legacy の受理集合は既に空である。measurement freeze、S-1 材料レポート、oracle trial 行は新たに受理も拒否もされず、拒否文言だけが変わる。

**重大度:** nit

**提案:** plan の consumer 波及欄を「diagnostic reach」と表記し、P3 の実効性根拠には数えない。plan 自身の line 248 の caveat は維持する。

## 所見 4 — holdout・ratified・pilot・report replay は name-mask 検査を迂回する

**種別:** scope 穴

**根拠:** holdout は `known_axes = _load_json(...)` の後に entry をそのまま複製し ([s8b_holdout_freeze.py:524](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s8b_holdout_freeze.py:524)、[同:487](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s8b_holdout_freeze.py:487))、検証時も同じ複製との equality だけである ([同:809](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s8b_holdout_freeze.py:809))。共有 loader は「検証意味論 `(verify_document)` は所有しない」([s8b_freeze_io.py:2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s8b_freeze_io.py:2))。ratified と report も source／entry hash を検証するだけで、name-mask を再評価しない。

**成果物影響:** 非正準 producer から入れば `holdouts.<id>.variant_binding.entries.system_gate.{name,gate_predicate}` が食い違い、selector basis hash、prediction の `binding_entry_sha256`、floor/oracle manifest の `entry_sha256`、pilot の `system_gate` 実測値がその文書へ束縛される。現行 public oracle／certified 選択には到達しないが、holdout 台帳と pilot 材料参照は変わる。

**重大度:** scope 外の裁定パッケージ候補

**提案:** 本 wave を拡張せず、既に裁定済みの T-533→T-531 ([docs/worklog.md:2269](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/docs/worklog.md:2269)) の受入条件へ「canonical membership だけでなく T-532 の name-mask 束縛も holdout／ratified 境界で必須」と明記する。

## 所見 5 — 等価ロジックの production 取り残しはないが、既存 golden test が brief の棚卸しから漏れている

**種別:** consumer 取り残し

**根拠:** 既存 test は `masks = {"g_rt": 4, "g_rl": 8, "ident_all": 31}` として、凍結6 record の name→predicate を既に照合する ([test_reflux_ir.py:445](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/tests/test_reflux_ir.py:445))。一方、`p3_s4_loop_trigger_gating`、pipeline、loop、wal は name を扱わず、`TriggerGateBinding.mask` と emitter predicate の別性質を検査している。

**成果物影響:** 現行成果物への影響はゼロ。ただし将来 mask 31 の通常名を使う refreeze では、production helper が許してもこの hard-coded golden が先に赤くなる可能性がある。

**重大度:** nit

**提案:** brief の「既存は1箇所だけ」を production に限定する。golden test は独立 oracle として新公開関数へ置換せず、将来の refreeze 時に明示更新する。

Import については新規問題を認めない。`s1_known_axes_freeze` は既に module 先頭で `s8a_trigger_sweep` を import しており ([s1_known_axes_freeze.py:24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s1_known_axes_freeze.py:24))、T-080 は s1 module を遅延 import する。部分 checkout で依存 module が欠ければ `known_axes.schema` refusal に正規化されて fail-closed となるが、部分 checkout が成功経路になる設計ではない。

## 総括

- **NO-GO — plan v1／brief のままでは不可。**
- T-080 の呼出し経路は実在するが、現行 official 受理集合は空で、現在値を変えない。
- DW-G05 の最終フィールド流入と現行誤 certification 到達の記述は誤りである。
- 実装案自体は、影響記述を修正し T-533/T-531 へ残存層を明示すれば再判定可能。
- pytest は未実行であり、緑は主張しない。