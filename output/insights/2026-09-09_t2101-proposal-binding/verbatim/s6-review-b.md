## テストの弱体化

must-fix はありません。

- test 差分全ハンクを確認しました。既存 assert、test、parametrize case の削除、期待値の反転・部分一致化、`skip`、`xfail`、`deselect`、`pytest.raises` 範囲拡大はありません。
- 既存 test の削除行は fixture 構築の置換だけです。
- [p3_b4_proposal_binding_support.py:53](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2101-proposal-binding/orchestrator/tests/p3_b4_proposal_binding_support.py:53) は proposal 内容から hash を導出し、[同:112](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2101-proposal-binding/orchestrator/tests/p3_b4_proposal_binding_support.py:112) で production issuer を実行しています。current commit、live projection digest、working-tree hash の焼込みはありません。
- 正負例は production loader と封印 publication を通過しており、binding 機構自体を stub 化して緑にする構造ではありません。

根拠: 読解。再現: `git diff --unified=3 2143a49c0..cd47c4651 -- orchestrator/tests`

## 過剰拒否

must-fix はありません。

- 実走: anonymous `memfd` 上の proposal を production loader に渡し、通常の base / sort / trigger、B-4 continuation 3 driver、通常 K2、B-4 continuation K2 がすべて受理されました。
- 読解: 新 gate は base [p3_s4_loop.py:2180](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2101-proposal-binding/orchestrator/campaign/p3_s4_loop.py:2180)、sort [p3_s4_loop_sort.py:490](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2101-proposal-binding/orchestrator/campaign/p3_s4_loop_sort.py:490)、trigger [p3_s4_loop_trigger_gating.py:970](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2101-proposal-binding/orchestrator/campaign/p3_s4_loop_trigger_gating.py:970) で、B-4 bootstrap または新引数が明示された場合だけ発火します。
- `run_one_iteration` / `drive_iteration` 本体は変更されていません。非 B-4 fixture、通常 CLI、sort / trigger の非 B-4 経路に新しい必須引数はありません。
- formal continuation の argv は [p3_b4_launcher.py:207](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2101-proposal-binding/orchestrator/campaign/p3_b4_launcher.py:207) で従来どおり terminal receipt のみを渡します。
- 実走: key 順、空白、非 ASCII escape だけが異なる JSON の canonical hash は一致し、`1` と `1.0` は不一致でした。実 publication を使う正例も [test_p3_b4_proposal_binding.py:65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2101-proposal-binding/orchestrator/tests/test_p3_b4_proposal_binding.py:65) にあります。

## 既存の拒否順序の pin

must-fix はありません。

対象 test 名:

- base: `test_b4_fixture_main_rejects_run_one_iteration_bypass_m13`
- sort: `test_b4_sort_no_build_and_fixture_routes_are_write_free`
- trigger: `test_b4_trigger_no_build_and_fixture_routes_are_write_free`

実走結果:

- `tools/run_tests.py` に上記 3 nodeid を指定しましたが、`output/pegasus-dispatch/submission.lock` が read-only で `rc=16`、`child_started=false` でした。pytest 緑はありません。
- 代わりに production `main` を直接呼ぶ read-only probe を実走しました。base fixture、sort/trigger の no-build と fixture はすべて既存理由で拒否され、各 pin spy と candidate spy は呼出し 0 回でした。
- 読解でも既存拒否は新 binding 検査より前です。base [p3_s4_loop.py:2486](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2101-proposal-binding/orchestrator/campaign/p3_s4_loop.py:2486)、sort [p3_s4_loop_sort.py:706](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2101-proposal-binding/orchestrator/campaign/p3_s4_loop_sort.py:706)、trigger [p3_s4_loop_trigger_gating.py:1256](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2101-proposal-binding/orchestrator/campaign/p3_s4_loop_trigger_gating.py:1256)。

## 波及の網羅

B1 [nit] 実装報告の波及列挙は分類単位で、consumer test の file 完全集合になっていません。

- 根拠: 読解。[stage5-author.md:65](/home/SFC/tanab/.claude/jobs/97d0d312/tmp/t2101/stage5-author.md:65)
- 再現: `rg -l '\bp3_b4_launcher\b|\bp3_s4_loop\b|\bp3_s4_loop_sort\b|\bp3_s4_loop_trigger_gating\b' orchestrator/tests --glob 'test_*.py' | sort`
- 結果: launcher 8 file、base 22 file、sort 13 file、trigger 10 file、和集合 26 fileです。
- 報告で明示された 4 test file 以外の参照先は次の 22 file です。

`test_artifact_admission.py`, `test_campaign.py`, `test_campaign_import_invariant.py`, `test_codex_agents.py`, `test_floor_pair_driver.py`, `test_layer3_report.py`, `test_p3_b4_material_report.py`, `test_p3_b4_raw_record_producer.py`, `test_p3_b4_wiring_probe.py`, `test_p3_build_authority_cli.py`, `test_p3_exploration_namespace.py`, `test_p3_s4_loop_job_contract.py`, `test_p3_s4_loop_sort.py`, `test_p3_s4_loop_trigger_gating.py`, `test_pytest_collection_config.py`, `test_s1_direct_comparison.py`, `test_s6_sort_sweep.py`, `test_s8a_trigger_sweep.py`, `test_s8b_oracle_driver.py`, `test_sort_swo_oracle.py`, `test_t671_source_binding.py`, `test_trigger_gate_binding.py`。

`_production_launch_context` は定義 1 件と呼出し 15 件でした。利用行は `438, 533, 1003, 1030, 1105, 1253, 1309, 1352, 1403, 1461, 1519, 1562, 1594, 2323, 2953` です。

## 新規 test file の要件

must-fix はありません。

- 新規 test file は `test_p3_b4_proposal_binding.py` 1 件で、[末尾:503](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2101-proposal-binding/orchestrator/tests/test_p3_b4_proposal_binding.py:503) に自走 harness があります。
- file 集合メタテストは [test_plain_runner_coverage.py:44](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2101-proposal-binding/orchestrator/tests/test_plain_runner_coverage.py:44) です。directory を動的列挙するため更新不要です。
- 新規 file は静的に 23 node。duration ledger 登録は 0 件です。
- 現行記録の `20042 / 21867` に 23 node を加えた反実仮想は `20042 / 21890 = 91.557789%` で、90% gate を維持します。この wave での登録は必須ではありません。

## 凍結面への接触

must-fix はありません。

実走した `git diff --exit-code 2143a49c0..cd47c4651 -- ...` は rc=0 でした。

変更なしを確認した面:

- [p3_b4_analysis_path.py:67](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2101-proposal-binding/orchestrator/campaign/p3_b4_analysis_path.py:67) の `_SOURCE_CLOSURE_PATHS`
- その closure 5 file
- [p3_b4_prerun_issuer.py:53](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2101-proposal-binding/orchestrator/campaign/p3_b4_prerun_issuer.py:53) の `B4_PRERUN_NON_GUARANTEES`
- docs、output、既存 prerun receipt schema

## must-fix 一覧

なし。

## 総括

must-fix 0、nit 1 です。受理集合は意図した B-4 bootstrap だけで狭まり、continuation、非 B-4、K2、既存拒否順序への過剰拒否は確認されませんでした。pytest は infrastructure failure で未実走ですが、read-only production probe はすべて成功しています。作業ツリーは clean のままです。