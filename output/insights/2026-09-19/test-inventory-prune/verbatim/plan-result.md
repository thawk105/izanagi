## 削除候補一覧

**削除案 v1 は B2 の重複入力1件だけ。関数削除は0件。** 親による変異 pre/post の成立を実装条件とする。

以下、test file の省略パスはすべて `orchestrator/tests/` 相対。台帳秒は実測し直した値ではない。

|分類|file:開始行-終了行 qualname|削除 node 数|台帳秒|根拠|
|---|---|---:|---:|---|
|B2|`test_s8b_holdout_freeze.py:2383-2384 test_v2_candidate_rejects_later_run_using_derived_earlier_eligibility[drop-candidate-selection]`|1|33.000|入力列の index 2 は index 0 と型・repr とも `True`。本文は id に分岐せず同じ拒否を検査する。|

変更対象は decorator 内の入力と対応 id のみ。

```diff
-    [True, False, True],
-    ids=["min-to-max", "use-reported-eligible", "drop-candidate-selection"],
+    [True, False],
+    ids=["min-to-max", "use-reported-eligible"],
```

関数全体 `2381-2416` は残す。残す node は `[min-to-max]` と `[use-reported-eligible]`。**関数全体の台帳100秒を削減値に使わない。** inline 配列なので、編集は2行だが物理行数の純減は0行。

A、B1、C の削除候補は0件。D は全件保持する。

B1 の7組は、本文 AST が同じでも次の相違があるため、いずれも削除しない。

|組・member の位置|binding の確認結果|判定|
|---|---|---|
|`test_s6_sort_sweep.py:79` / `test_s8a_trigger_sweep.py:86`|`W` はそれぞれ `orchestrator.campaign.s6_sort_sweep` / `s8a_trigger_sweep`|別 module の `run_sweep`|
|`test_paper_story_a1_headline.py:1366` / `test_paper_story_a1_headline_sizing.py:2074`|`_run`、`_validate_self_test_selection`、`EXPECTED_SELF_TEST_NAMES` は各 test module の別定義|各 suite の self-run 防壁|
|`test_b10_extended_figure_provenance.py:891` / `test_plot_b10_extended_backoff.py:354`|前者の `_pinned_measurement_paths` は `HASHES`、後者は `REAL_PROVENANCE` の `external_inputs` を読む|異なる資料からの導出|
|`test_real_repo_serialization.py:894` / `test_s8b_oracle_driver.py:623`|共通の ignore helper は同 module。ただし前者の `_t080_output_snapshot` は独立した走査実装、後者は `git_visible_output_metadata_snapshot(root, ROOT)` に委譲|主たる snapshot 実装が異なる。protected 側だけ残す案は不可|
|`test_t1434_t1222_science_slice.py:468` / `test_t189_oracle_wiring_slice.py:170`|各 file の `_require_pinned_jobs_files` と `_pinned_jobs_paths`。前者は `_artifact_value()`、後者は `_slice_value()`|別入力集合の完全性|
|`test_t1434_t1222_science_slice.py:452` / `test_t189_oracle_wiring_slice.py:154`|上記と同じ別 binding|別入力集合の欠落拒否|
|`test_s6_sort_sweep.py:297` / `test_s8a_trigger_sweep.py:387`|`W` は別 production module|別 module の `perf_for`|

真の重複関数がないため、導入履歴による先後選択は不要。

## (A) 全件判定表

**112件すべて本文確認済み。a=112、b=0、未確認=0。**

ここで a は「不在 literal が合成入力・負例・表示文字列、または scanner が path/flag を誤認した生きた検査」を表す。実在資料の basename prefix や `file:function` を単体 path とみなした例も含む。台帳秒の降順。

|#|file:行|判定|根拠|
|---:|---|:---:|---|
|1|`test_official_perf_closure.py:920-935`|a|合成 `unreviewed.py` と既存 source 除去による drift 検出|
|2|`test_s8b_floor_campaign.py:8014-8200`|a|実 production AST の build site と gateway registry を照合|
|3|`test_official_perf_closure.py:871-907`|a|実 source の guard 改変と合成 caller 追加の検出|
|4|`test_dev_wave_land.py:8275-8310`|a|合成 repo で実行した Git argv の許可範囲|
|5|`test_audit_dangling_commits.py:3286-3308`|a|合成 path 50,000件の owner 集合を検査|
|6|`test_dev_wave_land.py:8590-8632`|a|合成 commit 列で runner 復元後の land 受理|
|7|`test_growth_test_holds_contract.py:2440-2457`|a|実 node の `--noconftest` bypass 拒否|
|8|`test_growth_test_holds_contract.py:2534-2553`|a|実 node の通常 pytest 経路で hold skip を検査|
|9|`test_dev_wave_land.py:1602-1668`|a|合成 runner 変更を provenance より先に拒否|
|10|`test_dev_wave_land.py:8557-8587`|a|最終 main の runner 変更を拒否|
|11|`test_dev_wave_land.py:8635-8671`|a|Git lookup 障害を注入し retryable 判定を検査|
|12|`test_dev_wave_land.py:9266-9333`|a|合成 active fold で D987 拒否時の lease 維持|
|13|`test_dev_wave_land.py:1486-1505`|a|合成 red nodeid の結果・JSON 出力|
|14|`test_dev_wave_land.py:1508-1532`|a|合成 flake nodeid と receipt digest の取扱い|
|15|`test_dev_wave_land.py:1535-1555`|a|合成 red/flake nodeid 集合の分離|
|16|`test_related_work_search.py:1585-1602`|a|実 CLI の help と subcommand argv を検査|
|17|`test_dev_wave_land.py:1804-1833`|a|合成 repo から runner を除去する拒否負例|
|18|`test_dev_wave_land.py:1836-1863`|a|child-green でも runner 欠落を拒否|
|19|`test_dev_wave_land.py:1959-1995`|a|tested-main lookup 障害の retryable 判定|
|20|`test_dev_wave_land.py:1926-1956`|a|runner lookup 障害の拒否と main 不変|
|21|`test_dev_wave_land.py:5624-5646`|a|合成 checker が動かした HEAD を検出|
|22|`test_dev_wave_land.py:9890-9921`|a|合成 fold interrupt 後の lease・main 保護|
|23|`test_dev_wave_land.py:11347-11370`|a|欠落 receipt 例外を注入して rc31 を検査|
|24|`test_mutation_harness.py:1051-1076`|a|nodeid は parser 入力文字列|
|25|`test_dev_wave_land.py:5649-5685`|a|HEAD 移動時の provenance 拒否順序|
|26|`test_dev_wave_land.py:7979-8013`|a|合成 standalone fold state の自動回復拒否|
|27|`test_dev_wave_land.py:6515-6532`|a|合成 plan failure に対する FF 前の拒否|
|28|`test_dev_wave_land.py:1998-2029`|a|runner lookup が tested-main を使用することを検査|
|29|`test_dev_wave_land.py:6739-6764`|a|実 `_validate_generated_docs` が組む argv を検査|
|30|`test_t139_approval_payload.py:178-185`|a|fixture の D282 見出しを複製する拒否負例|
|31|`test_pytest_failure_digest.py:397-421`|a|合成 failure 群の budget・省略会計|
|32|`test_t139_approval_payload.py:232-247`|a|合成 D999 見出しによる section 境界攻撃|
|33|`test_t139_approval_payload.py:169-175`|a|D282 を全角数字へ変える拒否負例|
|34|`test_dev_wave_submodule_init.py:196-202`|a|実 CLI の help 出力|
|35|`test_ccbench_spawn_sites.py:2981-3013`|a|片側 gate の合成 source を拒否|
|36|`test_mutation_harness.py:1079-1092`|a|合成 nested parametrize id の group suffix 分離|
|37|`test_t793_report.py:80-88`|a|合成後続決定による supersession 検出|
|38|`test_t793_report.py:109-116`|a|無関係な合成後続決定の正例|
|39|`test_dev_waves_git_state.py:140-148`|a|合成 repo に作る worktree の実 path・branch|
|40|`test_t793_report.py:91-97`|a|否定文中の D291 参照も fail-closed|
|41|`test_dev_waves_git_state.py:1121-1134`|a|合成 fragment の rename を拒否|
|42|`test_ccbench_spawn_sites.py:2957-2978`|a|gate のない合成 build source を検出|
|43|`test_ccbench_spawn_sites.py:3016-3034`|a|未登録の合成 source を deferred 扱いしない|
|44|`test_t793_report.py:100-106`|a|合成 fence 内 D291 参照の検出|
|45|`test_pytest_failure_digest.py:424-456`|a|合成100 failure の renderer 呼出回数|
|46|`test_plot_a2_certification.py:1631-1651`|a|実図版資料から caption source の provenance を生成|
|47|`test_plot_a2_certification.py:1565-1576`|a|fig5 bundle の実在・closure・caption 検査|
|48|`test_plot_a2_certification.py:1654-1662`|a|fig7 bundle の実在・closure 検査|
|49|`test_campaign_lock_codec.py:636-677`|a|未知 grammar path・順序・型の拒否負例|
|50|`test_flaky_test_holds_contract.py:831-841`|a|未記録の合成 nodeid を拒否|
|51|`test_pytest_failure_digest.py:267-284`|a|合成 nodeid と diagnostic tail の escape|
|52|`test_campaign_import_invariant.py:1453-1501`|a|合成 `x.py` source の alias 解析|
|53|`test_p3_b4_wiring_probe.py:605-627`|a|合成 module の import-time 副作用検出|
|54|`test_campaign_lock_codec.py:607-633`|a|未知 grammar path を追加する拒否負例|
|55|`test_ccbench_spawn_sites.py:3423-3446`|a|合成 with-tuple の検査済み値伝播|
|56|`test_campaign_import_invariant.py:1353-1407`|a|合成 bootstrap の欠落・順序・path 異常|
|57|`test_ccbench_spawn_sites.py:3037-3061`|a|合成2 sink の各々に gate が必要|
|58|`test_ccbench_spawn_sites.py:3400-3420`|a|合成 with-name の検査済み値伝播|
|59|`test_ccbench_spawn_sites.py:3936-3960`|a|無関係な global/nonlocal の合成正例|
|60|`test_ccbench_spawn_sites.py:4010-4031`|a|別 macro の gate 流用を合成 source で拒否|
|61|`test_campaign_import_invariant.py:1410-1450`|a|合成 path 式の dirname/parents 深さを検査|
|62|`test_campaign_import_invariant.py:1504-1541`|a|合成 alias の安全例と曖昧な再束縛|
|63|`test_ccbench_spawn_sites.py:3531-3549`|a|合成 closure の local fixed shadow を分類|
|64|`test_ccbench_spawn_sites.py:3626-3641`|a|合成 conditional alias の unchecked 側を検出|
|65|`test_ccbench_spawn_sites.py:3718-3734`|a|合成 default walrus の再束縛を検出|
|66|`test_ccbench_spawn_sites.py:3756-3771`|a|合成同一式 walrus の再束縛を検出|
|67|`test_ccbench_spawn_sites.py:3774-3792`|a|無関係な nested default の合成正例|
|68|`test_ccbench_spawn_sites.py:3795-3813`|a|read-only match guard の合成正例|
|69|`test_ccbench_spawn_sites.py:3816-3835`|a|合成 class-global helper 再束縛を検出|
|70|`test_ccbench_spawn_sites.py:3838-3856`|a|呼ばれる nonlocal 再束縛の合成負例|
|71|`test_ccbench_spawn_sites.py:3877-3892`|a|合成 lambda default walrus の検出|
|72|`test_ccbench_spawn_sites.py:3895-3912`|a|偽 guard 後も残る再束縛の合成負例|
|73|`test_ccbench_spawn_sites.py:3915-3933`|a|次 case へ持ち越す再束縛の合成負例|
|74|`test_ccbench_spawn_sites.py:3963-3990`|a|gate のない合成 with binding を unresolved にする|
|75|`test_related_work_search.py:3035-3071`|a|未知 option・重複 timeout 等の意図した拒否入力|
|76|`test_campaign_import_invariant.py:1556-1583`|a|合成 canonical import・docs command の正例|
|77|`test_campaign_import_invariant.py:1586-1609`|a|合成 module 名 join の再束縛・scope 判定|
|78|`test_campaign_import_invariant.py:1651-1659`|a|合成違反を空 exception ledger が隠せない|
|79|`test_ccbench_spawn_sites.py:3512-3528`|a|合成 opaque closure を unresolved にする|
|80|`test_ccbench_spawn_sites.py:3552-3567`|a|branch 内だけの evidence を合成 source で拒否|
|81|`test_ccbench_spawn_sites.py:3570-3585`|a|sink 後の evidence 検査を合成 source で拒否|
|82|`test_ccbench_spawn_sites.py:3588-3603`|a|検査済み名の合成再代入を拒否|
|83|`test_ccbench_spawn_sites.py:3606-3623`|a|loop 内の合成再束縛を拒否|
|84|`test_ccbench_spawn_sites.py:3644-3658`|a|short-circuit で省略可能な合成 gate を拒否|
|85|`test_ccbench_spawn_sites.py:3661-3679`|a|同名の合成偽 method を evidence と認めない|
|86|`test_ccbench_spawn_sites.py:3682-3698`|a|合成 local helper shadow を拒否|
|87|`test_ccbench_spawn_sites.py:3701-3715`|a|合成引数による helper shadow を拒否|
|88|`test_ccbench_spawn_sites.py:3737-3753`|a|合成 match guard walrus を検出|
|89|`test_ccbench_spawn_sites.py:3859-3874`|a|合成 star import による binding 不確実性|
|90|`test_flaky_test_holds_contract.py:803-818`|a|`.txt` nodeid と不正 hold object の拒否|
|91|`test_t793_addendum_p_envelope.py:27-32`|a|実 draft の p03 見出しを除去する負例|
|92|`test_t793_addendum_p_envelope.py:35-41`|a|実 draft へ p04 見出しを追加する負例|
|93|`test_t793_addendum_p_envelope.py:44-50`|a|実 draft の p01 見出しを重複させる負例|
|94|`test_calibration_freeze_stage6_candidate_gate.py:425-454`|a|合成 path 集合に対する inventory 選択|
|95|`test_calibration_freeze_stage6_candidate_gate.py:457-562`|a|合成 caller 追加・alias・getattr を検出|
|96|`test_campaign_import_invariant.py:1544-1547`|a|合成 docs command の legacy namespace 検出|
|97|`test_campaign_import_invariant.py:1550-1553`|a|合成 absolute sibling import を検出|
|98|`test_campaign_import_invariant.py:1612-1620`|a|合成 TYPE_CHECKING import の正例|
|99|`test_ccbench_spawn_sites.py:3993-4007`|a|合成 opaque genome の unresolved 判定|
|100|`test_claude_transport.py:597-625`|a|不正 policy path 等を渡す拒否負例|
|101|`test_dev_waves_git_state.py:1137-1142`|a|合成 rename record の fold-owned 判定|
|102|`test_dev_waves_git_state.py:1145-1156`|a|合成 NUL 区切り rename/copy の parser|
|103|`test_mutation_fanout_contract.py:587-594`|a|nodeid は match-key parser の入力|
|104|`test_mutation_fanout_contract.py:597-608`|a|nested id と group suffix の parser 入力|
|105|`test_p3_s4_loop_trigger_gating.py:2289-2299`|a|`docs/x.md:role` の文字列 parser|
|106|`test_pytest_failure_digest.py:978-996`|a|合成 `FAILED` 行による node 注入防止|
|107|`test_ccbench_spawn_sites.py:3064-3158`|a|合成 exception reraise の受理 corpus|
|108|`test_ccbench_spawn_sites.py:3161-3298`|a|合成 exception swallow の拒否 corpus|
|109|`test_ccbench_spawn_sites.py:3301-3374`|a|合成例外型再束縛の拒否 corpus|
|110|`test_dev_wave_land.py:4127-4200`|a|合成 repo の中断 fold 回復と successor 順序|
|111|`test_plot_a1_sized_paired.py:471-486`|a|実 fig9 bundle・README hash・closure の検査|
|112|`test_plot_b10_static_tail_formal.py:414-423`|a|実 fig8 bundle・closure・caption の検査|

fig5/7/8/9 は `.png`、`.pdf`、`.provenance.json` の実在を確認した。addendum draft の `### p03 —` と `### p01 —` も各1件存在する。欠落対象を mock で恒真にした b は見つからなかった。

## 除外した候補

|理由|件数|扱い・代表例|
|---|---:|---|
|excluded-suites|30 file|scanner 対象外。提供 list A/B/C/D との追加交差は0|
|protected、全 inventory|634関数|削除対象外|
|protected、分類別|A 2 / B 1 / C 0 / D 6|分類間重複あり。合算して unique 件数にしない|
|sibling、提供 list 内|A 1 / B 2 / C 0 / D 27|floor-campaign の A 1件、reasoning-ab の B 2件。D は floor 8件・reasoning-ab 19件|
|B1 意味的非重複|7組・14 member|protected member 1件を含む。前節の binding 相違|
|B2 型違い|26 row|下表。拒否負例に加え int/float の受理境界検査も保持|
|C 機構が現存|1関数|`test_campaign.py:10615-10630`|
|D、削除裁定外|291関数|代表検査による再分類は後節。全件保持|

B2 の27 row の比較結果。位置は inventory の decorator 行、row は0-based。

|file:行 / row|比較した repr|判定|
|---|---|---|
|`test_campaign_lock_codec.py:402` / 2↔1|`0` / `False`|型違い、保持|
|同 / 4↔0|`1.0` / `True`|型違い、保持|
|`test_codex_reasoning_ab.py:7338` / 1↔0|`1.0` / `True`|型違い、保持・sibling|
|`test_codex_reasoning_ab.py:7613` / 1↔0|`1.0` / `True`|型違いの受理検査、保持・sibling|
|`test_env_contract.py:191` / 3↔2|`0` / `False`|型違い、保持|
|`test_env_contract.py:325` / 3↔0|`False` / `0`|型違い、保持|
|同 / 4↔2|`1.0` / `True`|型違い、保持|
|`test_p3_autonomous_workload_trial.py:10511` / 3↔2|`1.0` / `True`|型違い、保持|
|`test_p3_s4_loop.py:3248` / 1↔0|`1.0` / `1`|型違いの受理境界、保持|
|同 / 3↔2|`20.0` / `20`|型違いの受理境界、保持|
|同 / 5↔4|`1000.0` / `1000`|型違いの受理境界、保持|
|`test_p3_s4_loop.py:6434` / 2↔1|`1` / `True`|型違い、保持|
|`test_p3_s4_loop_trigger_gating.py:2001` / 3↔2|`0` / `False`|型違い、保持|
|同 / 4↔1|`1` / `True`|型違い、保持|
|`test_paper_story_a1_paired.py:1255` / 6↔1|`0` / `False`|型違い、保持|
|`test_paper_story_a1_paired.py:3307` / 1↔0|`('driver_rc', 1)` / `('driver_rc', True)`|型違い、保持|
|`test_paper_story_a1_paired.py:3878` / 4↔3|`(1, False)` / `(True, False)`|型違い、保持|
|`test_reflux_origin_binding.py:744` / 3↔1|`True` / `1`|型違い、保持|
|`test_s8b_descriptor.py:77` / 2↔1|`1` / `True`|型違い、保持|
|`test_s8b_holdout_freeze.py:2381` / 2↔0|`True` / `True`|真の重複、後側だけ削除案|
|`test_s8b_oracle_artifacts.py:91` / 3↔2|`('reps', 0)` / `('reps', False)`|型違い、保持|
|`test_s8b_selector_output.py:309` / 1↔0|`choice_id=True` / `choice_id=1`|dict 内の型違い、保持|
|`test_s8c_generation_projection.py:307` / 1↔0|`1.0` / `True`|型違い、保持|
|`test_s8c_generation_projection.py:573` / 2↔1|`True` / `1`|型違い、保持|
|`test_s8c_result_judge.py:548` / 1↔0|`('n', True)` / `('n', 1)`|型違い、保持|
|`test_t471_restore_bound.py:136` / 4↔3|`1.0` / `True`|型違い、保持|
|`test_trigger_gate_binding.py:91` / 4↔2|`1.0` / `True`|型違い、保持|

C は削除しない。D641 は D158 の **official が env を参照しない部分だけ**を supersede し、exploration の「resolve 時には worktree container を拒否しない」挙動を明示的に温存する。`orchestrator/campaign/layout.py:375` の resolver は現存し、`reject_worktree_container=False` を渡す。`resolve_campaign_output_root("exploration", …)` からも到達可能。

## 対象 module 集計

|対象 production module|削除 test 数|行数|台帳秒|test file 集合|
|---|---:|---|---:|---|
|`orchestrator/campaign/s8b_holdout_freeze.py`|関数0・parameter case 1|編集2行、純減0行|33.000|残る file：`orchestrator/tests/test_s8b_holdout_freeze.py`。削除 file：なし|

当該 test file は関数108件を保持する。

変異 runner の直接 import 集合として、AST で次の20 file を確認した。すべて `orchestrator/tests/` 相対。削除禁止 suite も、runner として実行することとは区別する。

```text
test_autonomous_trial_completeness.py
test_s8b_attempt_registry.py
test_s8b_budget_approval_preflight.py
test_s8b_floor_evacuation.py
test_s8b_holdout_freeze.py
test_s8b_oracle_driver.py
test_s8b_oracle_judge.py
test_s8b_oracle_manifest.py
test_s8b_oracle_n_pilot.py
test_s8b_oracle_report.py
test_s8b_ratified_freeze.py
test_s8b_ratified_verify.py
test_s8b_repo_scan_invariant.py
test_s8b_selector_input.py
test_s8b_terminal_evidence.py
test_s8b_verdict.py
test_s8c_acceptance_receipt_v2.py
test_s8c_preregistration_invariant.py
test_s8c_preregistration_predicates.py
test_t080_freeze_migration.py
```

これは直接 import の確定集合であり、helper 経由・動的 import を含めた閉包の保証ではない。親の runner 選定時に補完する。

## 変異事前登録案

対象は `orchestrator/campaign/s8b_holdout_freeze.py` の1 spec。以下の old はそれぞれ `grep -Fc` で **1件**を確認した。各変異は独立に適用する。

負例 M1：最早適格 run の選択を最遅へ変える。位置1981行。

old:

```python
    required_run_id, _required_rel = min(eligible, key=lambda item: item[0])
```

new:

```python
    required_run_id, _required_rel = max(eligible, key=lambda item: item[0])
```

負例 M2：選択 identity 不一致の拒否を無効化する。位置1983行。

old:

```python
    if required_run_id != selected_run_id:
```

new:

```python
    if False and required_run_id != selected_run_id:
```

等価対照 E1：先頭の encoding comment に comment のみ追加する。位置1行。

old:

```python
# -*- coding: utf-8 -*-
```

new:

```python
# -*- coding: utf-8 -*-  # mutation-control
```

静的な検出根拠は次のとおり。

|変異|削除予定 node|残る検出 node|assertion 単位の根拠|
|---|---|---|---|
|M1|`test_v2_candidate_rejects_later_run_using_derived_earlier_eligibility[drop-candidate-selection]`|同関数 `[min-to-max]`、`[use-reported-eligible]`|fixture は選択 run より早い derived-eligible run を作る。`pytest.raises(M.FreezeError, match=…required_run_id=20260810T235900Z-…)` に対し、max は選択 run を選んで不一致拒否を通過する|
|M2|同上|同上|同じ `pytest.raises` が要求する拒否を無効化する。診断文だけを変える変異ではない|
|E1|なし|失敗 node なしを期待|Python の処理内容を変えない comment 追加|

各 case の前提 assertion は、selected/earlier の `floors` 一致、および earlier の `derived_eligible_for_refreeze is True`。削除予定 case と `[min-to-max]` は入力も本文も同一で、test/fixture 内に id による分岐は見つからなかった。

これらは **静的な検出予測**であり KILLED 実績ではない。親が変更前 HEAD で probe し、他層による拒否・mask・source hash pin による赤を除別する。目的の受理変化が確認できなければ、その負例は登録しない。

本登録は以下を満たすこと。

- pre の失敗 node 完全集合を `S`、削除予定 node を `d` とし、post は `S − {d}` と完全一致、かつ非空。
- M1/M2 とも削除予定 node と残存 node が受理挙動の変化で検出する。
- E1 は前後とも失敗 node なし。source bytes pin 等で赤なら等価対照成立とは扱わない。
- 明示した3 node の id は ASCII。全 runner の probe に非ASCII id が含まれた場合は、その変異案を本登録せず再選定する。
- runner は前後で同一の file 集合を使用する。

## (D) 裁定パッケージ案

41 file、291関数、356 node、225.392台帳秒。**全件保持。**

各 file で代表1本、`test_spool_fold.py` は2本を読んだ。件数・秒はその file の **scanner 候補全体**の値であり、全件が代表と同じ意味だと確定した値ではない。「Dでない」は読んだ代表が production 挙動を検査していたことを示す。

|file / 確認した代表行|候補件数|台帳秒|確定した代表の種別・pin 先|
|---|---:|---:|---|
|`test_audit_dangling_commits.py:1699`|13|1.343|Dでない。合成 repo の spool/archive path 除外挙動|
|`test_b10_backoff_grid_submit.py:137`|1|0.005|repo docs 文字列。`docs/b10-backoff-static-tail-preregistration.md` §8.2。shell syntax 検査も併存|
|`test_calibrator_certify.py:684`|1|0.030|Dでない。acquisition 拒否後に合成 `calibration.md` 等を作らない|
|`test_campaign_import_invariant.py:1107`|3|0.018|Dでない。合成 `docs/guide.md` を含む scanner end-to-end|
|`test_check_branch_landed.py:216`|24|2.745|Dでない。合成 archive/FOLDED.md に対する receipt 不在判定|
|`test_check_branch_rescue.py:889`|4|2.840|Dでない。合成 `docs/unreachable-object-ledger.md` の stale 通知|
|`test_check_wave_startup.py:302`|27|0.956|Dでない。合成 `docs/handoff/active.md` の startup gate|
|`test_codex_agents.py:345`|5|0.667|Dでない。fixture の `.claude/agents/auditor.md` 改変に対する hash drift 検出|
|`test_codex_reasoning_ab.py:1456`|19|0.115|argv 拒否挙動＋合成 launch identity hash の literal。docs bytes pin ではない。sibling|
|`test_codex_worker_launch.py:3412`|4|3.842|Dでない。receipt の failure class・合成 output.md の不正組合せ拒否|
|`test_codex_worker_launch_budget.py:967`|1|0.130|Dでない。合成 output.md を引数にした budget argv 伝達|
|`test_codex_worker_ledger.py:676`|6|0.073|Dでない。合成 worklog.md と session 会計の照合|
|`test_dev_wave_codex.py:467`|2|1.130|Dでない。合成 prompt/output.md と job directory の分離|
|`test_dev_wave_land.py:2592`|48|29.833|Dでない。合成 foreign handoff への衝突を拒否|
|`test_flaky_test_holds_contract.py:326`|2|0.039|Dでない。実 failures.md を fixture へ複写し registry export の導出を検査|
|`test_floor_pair_driver.py:636`|1|0.001|定数。SPEC/PLAN/WINDOW/SUMMARY の schema 4値|
|`test_floor_pair_job_contract.py:91`|1|0.000|docs 派生値＋実挙動。`docs/decisions.md` D2138 の3 spec hash と shell `select_pin`|
|`test_p3_b4_proposal_binding.py:556`|1|0.001|定数。`B4_PROPOSAL_BINDING_NON_GUARANTEES` の逐語 tuple|
|`test_paper_story_a1_headline.py:1232`|1|0.200|固定 Git 区間の non-touch manifest。docs・code・台帳を含む変更不存在検査|
|`test_paper_story_a1_paired.py:903`|1|0.020|実 bytes の SHA256 literal。v2 policy、2026-08-26/27 preregistration 一式、headline code・sizing tools|
|`test_pegasus_dispatch_compute.py:662`|1|0.001|定数。success/failure relay limit 4096/65536|
|`test_plot_a1_sized_paired.py:388,471`|2|0.000|混在。合成図版 path 拒否＋実 fig9 bundle/README hash/closure|
|`test_plot_a2_certification.py:1471`|8|1.407|Dでない代表。実 CLI→render→publish と caption source hash。実 docs 検査も同 file に混在|
|`test_plot_b10_static_tail_formal.py:414`|1|0.000|実 fig8 bundle と figures/README の caption・closure。literal hash 固定だけではない|
|`test_ruleops.py:477`|35|5.400|Dでない。合成 insight `.md` 群に対する inventory の scope・schema|
|`test_s8b_experiment_numbers.py:61`|1|0.001|定数。`APPROVED_EXTIME_S=5`、`APPROVED_REPS=5`|
|`test_s8b_floor_campaign.py:1163`|8|67.100|Dでない。production campaign 出力の result.md と perf receipt 整合。sibling|
|`test_s8b_ratified_freeze.py:1923`|1|17.000|Dでない。合成 root 間の emitter bytes/Git identity 決定性|
|`test_s8c_preregistration_core.py:2618`|1|0.001|定数。`DECIDER_VERSION="s8c-decider/v9"`|
|`test_s8c_preregistration_invariant.py:723`|1|43.000|Dでない。check_docs 本番 main に架空 docs path・腐敗行番号を注入する負例|
|`test_s8c_preregistration_predicates.py:4048`|1|0.052|Dでない。合成 `docs/archive/ruling-fixture.md` だけでは C11 を充足しない|
|`test_skip_classification.py:315`|1|0.001|repo docs の集合記載。`orchestrator/tests/README.md` 条件付き未実走節|
|`test_spool_fold.py:500,1753`|56|47.257|混在。合成 worklog 番号導出＋実 failures.md 複写への byte-exact 挿入挙動。単なる静的 pin ではない|
|`test_t1434_t1222_science_slice.py:409`|1|0.001|派生 path 集合の literal。T-1222/T1434 の外部 jobs prompt・receipt・oracle 資料|
|`test_t189_oracle_wiring_slice.py:132`|1|0.002|派生 path 集合の literal。T-1222/T1393 の外部 jobs prompt・receipt|
|`test_t189_task_catalog.py:210`|2|0.015|Dでない。合成 `docs/archive/worklog-fixture.md` から catalog と receipt を導出|
|`test_t2187_adaptive_const_probe.py:4130`|1|0.001|実 docs SHA256。`docs/backoff-policy-performance-preregistration.md` と production reader|
|`test_t793_publication_ledger.py:87`|1|0.001|定数。publication family root・ledger kind・schema|
|`test_task_run_aggregate.py:433`|1|0.160|Dでない。合成 reports/cli.md の create-only publish|
|`test_trial_registry.py:9042`|1|0.001|定数。manifest/registration schema v3|
|`test_wave_land_window.py:1967`|1|0.003|Dでない。合成 handoff.md を使い撤去 command を拒否|

裁定対象として優先して整理できるのは、定数のみを比較する7 file・7関数と、実資料 hash/path 集合の pin。production 挙動を通る代表を「低価値な docs pin」として一括削除裁定へ送らない。

## 波及と所有分割

author は **1単位**で十分。

|所有単位|変更可能 file|変更内容|
|---|---|---|
|author-1|`orchestrator/tests/test_s8b_holdout_freeze.py` のみ|重複 `True` と対応する `"drop-candidate-selection"` id を除去|

関数本文、期待値、helper、fixture、import の変更は不要。新たに未使用になる helper/fixture/import もない。file 内 test が0になる file はなく、file 削除候補は0。

対象 qualname/id の参照検索では、test 自身以外に duration 台帳の3 node が見つかった。conftest・他 test の golden からの名指し参照は見つからなかった。holdout-freeze は add-only 凍結8 suite に含まれない。

duration 台帳は本 wave では編集しない。削除 node の既存 entry を残したまま受入可能かは親の検査で確定する。追随編集が必須と判明した場合、この1件も指定条件に従って削除集合から外す。

inline 配列のため、これは「parameter row の除去」であって物理行丸ごとの削除ではない。物理行削除だけに限定する運用なら、この候補は実装不可として外す必要がある。

## 未確認と限界

- A は112/112、B1 は7/7組、B2 は27/27 row、C は1/1件を意味確認した。
- D は41/41 file の代表を確認した。A として読んだ分を含め、D 該当本文は45件確認、残る246件は個別には読んでいない。file 集計を意味分類の全件確定値に読み替えない。
- `inventory.json` は開いていない。ファイル変更・pytest・変異実行はしていない。
- 行番号と逐語 anchor は読取時点の作業 tree に対するもの。親が main 前進を取り込んだ後、再照合が必要。
- 変異の20 file は直接 import の静的集合。動的 import、間接 consumer、失敗 node 完全集合、非ASCII id の混入は親の probe で確定する。
- 台帳33秒は削除 node 固有値。受入 wall time や setup 費用が同じだけ減るとは主張しない。
- 1 module でも runner 集合は広い。変異 pre/post の所要は未実測であり、33秒の継続的削減に対する実装・検証費用は親の段4判断事項。

## 総括

削減見込みは **parameter case 1件・node 1件・関数0件・file 0件・物理行純減0行・台帳33.000秒**。worker 時間換算で **0.00917時間**、brief の17,958.8秒に対して約 **0.184%**。同じ台帳基準なら受入合計は17,925.8秒、約4.9794 worker 時間となる。

must-fix は、変異 pre/post で削除 node の検出集合を残存 node が保持すること、非ASCII id を含まない本登録、台帳追随不要の確認。成立するまで削除を確定しない。

scanner の B1 全7組と B2 の26/27 row をそのまま重複扱いする案は、独立実装や型境界の検出力を失うため採用不可。