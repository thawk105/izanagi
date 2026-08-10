段 4「プラン v2」の 7 項目を、許可された 6 ファイルだけに実装しました。pytest は環境障害で 0 件実行のため、緑・closed は申告しません。

### 変更内容

- [campaign_lock.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/campaign_lock.py:27)
  - lines 27–37: 歴史的名称の注記と、裁定順の exact 8 path を設定。

- [contract_loader_binding.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/contract_loader_binding.py:2)
  - lines 2, 48–53, 324–341: module/class/function docstring のみを 8-path closure に更新。
  - capture/live/committed のロジックは未変更。

- [campaign_lock_test_support.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/campaign_lock_test_support.py:10)
  - lines 10–20: HEAD の実 Git blob digest から test-only binding を作る経路を追加。
  - lines 23–46: `binding=None` の既定値だけを変更。明示 `binding=` の意味は不変。

- [test_t671_source_binding.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_t671_source_binding.py:22)
  - exact 8-path 独立 golden と production equality。
  - live drift／committed mismatch を各8 caseに parameterizeし、対象 path も検査。
  - 記録 commit ≠ HEAD でも disk が記録 blob と一致すれば live 検証が通る正例。
  - dirty disk でも共有 fixture が記録 blob digest から生成できる回帰。
  - production 6 call／4呼出し口の exact AST census。

- [test_campaign_lock_codec.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_campaign_lock_codec.py:34)
  - digest fixture を closure サイズ非依存の SHA-256 に変更。
  - 各8 key欠落と旧 exact-2 map の拒否を追加。

- [test_artifact_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_artifact_admission.py:720)
  - lines 720–740: 既存 campaign が全て v1 で、classification exact mapping が不変であることを固定。
  - lines 933–944: exact-8 v2 authority の受理を明示。
  - line 1152: `[-1]` を旧対象の明示 path に置換。

### 検証

緑を主張する範囲はありません。実行済み nodeid は **0件**です。

以下を `tools/run_tests.py` で試行しましたが、いずれも pytest 起動前に `qstat -Q preflight rc=1`、runner rc=16 で停止しました。

- 変更した3テストファイル
- 同3ファイルの `--collect-only`
- `test_campaign_lock_codec.py::test_v2_exact_shape_and_canonical_encoding` 1 nodeid

したがって **実装済み・未実走**です。pytest assertion の赤や submodule index-lock 赤は観測していません。

読み取り専用の静的確認は完了しています。

- 変更6ファイルの AST parse/import: OK
- `git diff --check`: OK
- production binding census: 6 calls／4 call sites
- `output/**/campaign.lock`: 32本、全32本 v1
- docs変更、`git add`、commit: なし

### 所有外への波及可能性

production caller は未編集ですが、閉包拡張の影響を受けます。

- `ident.py`: capture+live、新規 authority変換、resume live
- `artifact_admission.py`: authority変換+committed検証

共有 fixture の consumer は次の15ファイルです。

- `test_artifact_admission.py`
- `test_autonomous_trial_completeness.py`
- `test_campaign.py`
- `test_campaign_lock_wal_consumers.py`
- `test_critic.py`
- `test_p3_autonomous_workload_trial.py`
- `test_p3_exploration_namespace.py`
- `test_p3_s4_loop.py`
- `test_p3_s4_loop_sort.py`
- `test_p3_s4_loop_trigger_gating.py`
- `test_s1_direct_comparison.py`
- `test_s6_sort_sweep.py`
- `test_s8a_trigger_sweep.py`
- `test_screening_driver.py`
- `test_t126_qualification_artifacts.py`

また、所有外の `test_layer3_report.py` は独立に production capture を使用しているため、closure対象 module が dirty な環境では引き続き波及する可能性があります。

## 総括

- enforcement source closure を裁定順の exact 8 path へ拡張した。
- production の fail-closed・停止点・記録commit基準の意味論は変更していない。
- exact-2拒否、exact-8受理、v1分類不変をテストへ固定した。
- dirty-tree偽赤対策は test-only HEAD blob経路で実装した。
- 静的検査は通過、pytestはdispatch基盤rc=16により0件実走。
- 残る赤はテスト結果ではなく実行基盤障害。実装済み・未実走でありclosedではない。