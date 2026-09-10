## 所見

### 1. real / blocker — `build_document()` の出力不変条件は破れている

正本は「出力を一切変えない」と定めています（[plan-v2.md:7](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t492-freeze-semantic-membership/plan-v2.md:7>)）。しかし `generator.sha256` は generator 自身の bytes から作られ（[s1_known_axes_freeze.py:646](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/s1_known_axes_freeze.py:646)）、`generate()` は override なしで呼びます（[s1_known_axes_freeze.py:796](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/s1_known_axes_freeze.py:796)）。

静的に算出した SHA-256 は次のとおりです。

- HEAD の generator: `1d4d45a3...c364e0`
- 作業ツリーの generator: `a7505a96...64ed5`
- 現行 freeze の記録値: `1d4d45a3...c364e0`（[known_axes_freeze.json:5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/output/s1-freeze/known_axes_freeze.json:5)）

したがって、既定引数の `build_document()`／`generate()` の `generator.sha256` 値は確実に変わります。「AST が同一」「self-hash の規則を変えていない」ことは値不変の証明になりません。実装報告の主張（[impl-out.md:17](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t492-freeze-semantic-membership/impl-out.md:17>)）は誤りです。

その他については、top-level field・挿入順・trigger entry の flags/name/predicate は、受理された入力では不変です。helper は membership を見るだけで文字列を正規化しません（[trigger_gate_binding.py:113](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/trigger_gate_binding.py:113)）。`sources` も増減せず、system gate は各5件、ident_all は各4件、trigger 全体27件、document 全体63件のままです。

成果物影響は、既存 freeze bytes 自体には差分がない一方、再生成すれば `generator.sha256` が変わります。再生成しなければ legacy `verify_document()` は generator mismatch を先に返し（[s1_known_axes_freeze.py:742](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/s1_known_axes_freeze.py:742)）、従来の source mismatch 診断を覆います。例外型は引き続き `FreezeError` ですが、診断文字列と到達する検査が変わります。T-080 active の certified 経路は generator cell を静的再構成比較から除外しているため、現行選択値は直ちには変わりません。

厳密な出力不変を維持するなら、自己 hash されるこのファイルを編集する現設計とは両立しません。「凍結済み artifact bytes は編集しない」「明示した `generator_sha` を与えた射影では非 metadata field が不変」等への再裁定が必要です。

### 2. real / 既裁定 scope 外 — membership 権威が proof chain に帰属しない

新 helper は live の `trigger_gate_binding` に依存します（[s1_known_axes_freeze.py:82](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/s1_known_axes_freeze.py:82)）。一方、trigger entry の共通 source は `axis_trigger_gating` と `s8a_trigger_sweep` だけで（[s1_known_axes_freeze.py:511](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/s1_known_axes_freeze.py:511)）、`trigger_gate_binding.py`／`reflux_ir.py` は含まれません。`selection_rules.system_gate` にも membership 規則が記録されていません（[s1_known_axes_freeze.py:669](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/s1_known_axes_freeze.py:669)）。

具体的には、authority を恒真化し、main/remeasure の両 provenance を `"izanagi_gate_pass = true;"` に揃えると、新しい二つの検査点はいずれも通ります。generator 本体の hash は変えずに済み、authority の変更を指す source record もありません。

その場合、known freeze、measurement の cell、holdout の `variant_binding`、材料 proof chain に非正準述語が入ります。同じ live authority を使う sink も恒真化されれば certified 選択まで誤受理し得ます。これは [plan-v2.md:23](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t492-freeze-semantic-membership/plan-v2.md:23>) で明示的に scope 外裁定済みなので、本 wave 単独の追加 blocker とはしません。ただし保証は「authority が正しい現行コードで、provenance だけが連動 drift する場合」に限定されます。

### 3. real / 既裁定 scope 外 — holdout 単体経路は検査を迂回する

`s8b_holdout_freeze` は known document を直接読み（[s8b_holdout_freeze.py:524](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/s8b_holdout_freeze.py:524)）、`build_variant_binding()` が6構成を意味検査なしで複製します（[s8b_holdout_freeze.py:472](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/s8b_holdout_freeze.py:472)）。verify も同じ known doc から再コピーして等値を見るだけです（[s8b_holdout_freeze.py:749](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/s8b_holdout_freeze.py:749)、[s8b_holdout_freeze.py:809](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/s8b_holdout_freeze.py:809)）。

したがって、非正準述語を持つ known doc と、それを pin して生成した holdout doc は holdout 単体では受理され、`variant_binding.entries.*.gate_predicate` が変わります。公開 oracle は別途 known verifier または T-080 schema gate を通すため、そこで certified 選択は拒否されます（[s8b_oracle_driver.py:406](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/s8b_oracle_driver.py:406)）。材料 holdout の意味健全性は残りません。これも [plan-v2.md:22](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t492-freeze-semantic-membership/plan-v2.md:22>) の既裁定 scope 外です。

### 4. real / 既裁定 scope 外 — canonical 集合内の連動 drift は通る

検査は32述語への membership だけです。例えば balanced の `name="g_rl"` に、`g_rt` 相当の `kReadValiTid` 述語を main/remeasure 双方で与えると、membership と equality は通ります（[s1_known_axes_freeze.py:501](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/s1_known_axes_freeze.py:501)）。pairing も ident_all と異なることしか確認しません（[s1_known_axes_freeze.py:612](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/s1_known_axes_freeze.py:612)）。

これは恒真検査ではありません。新規テストの `"izanagi_gate_pass = true;"` は実際に発火する具体入力です。一方、「連動 drift 全般」ではなく「32集合外への連動 drift」だけを止めます。放置すると certified/material/台帳の `name` は `g_rl` のまま、実際の gate 意味だけ `g_rt` に変わります。[plan-v2.md:30](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t492-freeze-semantic-membership/plan-v2.md:30>) で T-493 所有と裁定済みです。

### T-080 active の負例不足 — nit

コード上の到達性はあります。

`gate_check()` → receipt 解決（[s8b_oracle_driver.py:449](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/s8b_oracle_driver.py:449)）→ `static_gate_adapter()` → `_verify_known_schema()`（[t080_freeze_migration.py:2084](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/t080_freeze_migration.py:2084)）→ `_validate_schema()`（[t080_freeze_migration.py:1803](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/t080_freeze_migration.py:1803)）です。

ただし現行 active 経路では、known raw bytes の固定 hash が先に一致必須なので（[s8b_oracle_driver.py:196](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/s8b_oracle_driver.py:196)）、現行データに対する semantic check は必ず真です。新規 wiring テストは legacy `verify_document()`、G7 は名前どおり never-issued 経路であり、active の非正準負例はありません。現行成果物の受理集合は変わらないため nit としますが、次回 repin 前には `[known_axes.schema] ...正準集合外` の active 公開負例を追加すべきです。

## 握り潰し・import・既存防壁

新しい `FreezeError` の握り潰しは見つかりません。

- measurement は known の `FreezeError` を自分の `FreezeError` に包み直して拒否します（[s1_measurement_freeze.py:156](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/s1_measurement_freeze.py:156)）。
- T-080 は `known_axes.schema` の `MigrationError` に分類し（[t080_freeze_migration.py:1811](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/t080_freeze_migration.py:1811)）、`_gate_check_call()` はその分類を保持します（[t080_freeze_migration.py:1879](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/t080_freeze_migration.py:1879)）。driver は refusal に集約します。
- calibration は利用前に `verify_document()` を呼び（[s1_verify_extime_calibration.py:197](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/s1_verify_extime_calibration.py:197)）、main 境界で `FreezeError` を失敗終了へ変換します（[s1_verify_extime_calibration.py:451](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/s1_verify_extime_calibration.py:451)）。

import 循環も新設されていません。`trigger_gate_binding → reflux_ir → axis_trigger_gating` に戻り edge はなく、さらに `trigger_gate_binding` は従来から `pipeline` 経由で transitively import 済みでした（[pipeline.py:55](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/pipeline.py:55)）。`sys.path` 操作にも差分はありません。

main/remeasure equality、generator/source hash、pairing、再構成等値はいずれも削除されていません。新 schema gate が先行して診断を覆う場合はありますが、受理集合を広げる早期 return はありません。G7 も historical generator replay 後に refusal 4件・known source mismatch 1件を維持しています（[test_s8b_oracle_driver.py:2732](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/tests/test_s8b_oracle_driver.py:2732)）。

pytest は実行していません。以上は差分・コード・凍結 JSON の静的検査です。

## 総括

**NO-GO**

- must-fix 1: `build_document()` 出力不変と自己 hash 変更の矛盾を親裁定で解消し、`generator.sha256` の実際の変更と downstream refusal 変更を正本・検査へ反映する。