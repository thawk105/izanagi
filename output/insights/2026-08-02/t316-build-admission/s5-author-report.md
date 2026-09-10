## 受理・拒否挙動

変更前:

- structural quarantine を通れば、coder 由来コードも provenance 未分類のまま build 可能。
- `evaluate()` / `run_campaign()` に admission は不要。
- `quarantine(write=True)` は validation 前にファイルを書き換えていた。

変更後:

- `CODER_DERIVED` は driver CLI の `--allow-coder-derived-build` がない限り `BuildAdmissionError` で既定拒否。
- `STOCK_OR_PINNED` / `MACHINE_SWEEP` / `HUMAN_REVIEWED` は従来どおり受理。
- `evaluate()` / `run_campaign()` の admission 未指定は `TypeError`。
- preview / `--no-build` は build しないため従来どおり利用可能。
- quarantine reject 時はファイルを書き換えない。

受理集合の変更は coder-derived build の既定拒否だけで、指示外の拡大・縮小はしていません。

## 実装内容

主要変更:

- [build_admission.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/build_admission.py:9)
  - 閉じた provenance enum、immutable admission、exact-type 再検証、既定拒否を新設。
  - ambient 環境変数は参照していません。
  - WAL receipt は `build_admission: {provenance_class, coder_derived_opt_in}` のみに限定。
- [pipeline.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/pipeline.py:419)
  - `evaluate()` に必須 keyword-only admission を追加し、identity・WAL・build より前で検証。
- [loop.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/loop.py:44)
  - `run_campaign()` に必須 admission を追加し、全評価へ伝播。
- [screening_driver.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/screening_driver.py:127)
  - screening 入口でも副作用前に再検証。
- [t126_driver.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/qualification/t126_driver.py:30)
  - qualification の pinned source を `STOCK_OR_PINNED` として明示。
- [p3_s4_loop.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/p3_s4_loop.py:179)
  - structural validation 後、成功時だけ write する順序へ反転。
- [diff_quarantine.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/diff_quarantine.py:1)
  - structural containment のみ、source digest は identity、auditor は advisory、意味 admission は未実装という実態へ訂正。
- P3 coder loop、sort/trigger loop・sweep、kickoff、red driver に CLI opt-in を追加。

テスト変更:

- [test_campaign.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/tests/test_campaign.py:1405): M1–M5、loop、screening、sort/trigger sweep、preview の build-spy 負例・正例。
- [test_p3_s4_loop.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/tests/test_p3_s4_loop.py:109): reject 前書き込みの回帰試験。
- [test_t126_qualification_driver.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/tests/test_t126_qualification_driver.py:52): qualification の分類と build-spy 負例。
- [test_p3_exploration_namespace.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/tests/test_p3_exploration_namespace.py:241): P3 caller の admission AST 検査。
- 既存の direct caller fixture を `test_p3_s4_loop_trigger_gating.py`、`test_s1_direct_comparison.py`、`test_s6_sort_sweep.py`、`test_s8a_trigger_sweep.py`、`test_s8b_oracle_driver.py`、`test_screening_driver.py` で更新。

## `run_campaign()` caller census

実 call expression は15箇所でした。裁定記載の「16箇所」は `rg 'run_campaign\('` が [loop.py の関数定義](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/loop.py:44)も数えた場合と一致します。

| Caller | Class | コード上の根拠 |
|---|---|---|
| [demo.py:51](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/demo.py:51) | `STOCK_OR_PINNED` | stock tree の genome 列挙 |
| [demo.py:59](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/demo.py:59) | `STOCK_OR_PINNED` | 同一 stock campaign の recovery |
| [backoff_sweep.py:149](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/backoff_sweep.py:149) | `MACHINE_SWEEP` | 人間定義の flag 候補を機械列挙 |
| [backoff_repro.py:98](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/backoff_repro.py:98) | `MACHINE_SWEEP` | sweep 結果の機械的再測 |
| [p2_2.py:138](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/p2_2.py:138) | `STOCK_OR_PINNED` | stock source 上の genome 列挙 |
| [sanity_silo.py:51](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/sanity_silo.py:51) | `STOCK_OR_PINNED` | stock sanity genome |
| [p3_kickoff.py:110](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/p3_kickoff.py:110) | `CODER_DERIVED` | coder 作成 no-op patch |
| [p3_kickoff.py:116](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/p3_kickoff.py:116) | `CODER_DERIVED` | coder 作成 static patch |
| [p3_s4_loop.py:675](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/p3_s4_loop.py:675) | `CODER_DERIVED` | LLM が hole 実装を生成 |
| [p3_s4_loop_sort.py:240](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/p3_s4_loop_sort.py:240) | `CODER_DERIVED` | LLM comparator 実装 |
| [p3_s4_loop_trigger_gating.py:421](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/p3_s4_loop_trigger_gating.py:421) | `CODER_DERIVED` | LLM trigger predicate |
| [p3_s4_red.py:146](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/p3_s4_red.py:146) | `CODER_DERIVED` | coder 発 RED patch |
| [p3_s4_red.py:155](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/p3_s4_red.py:155) | `STOCK_OR_PINNED` | stock source＋fixture trace |
| [s6_sort_sweep.py:330](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/s6_sort_sweep.py:330) | `CODER_DERIVED` | coder-derived comparator 候補群。M4 対象 |
| [s8a_trigger_sweep.py:377](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/s8a_trigger_sweep.py:377) | `CODER_DERIVED` | coder-derived trigger 候補群。M4 対象 |

非テスト `evaluate()` caller 3箇所も `loop`、`screening_driver`、`t126_driver` の全てで admission を確認しました。

## 検査結果

`hostname` は `pegasus02` でした。規律に従い、pytest・build・mutation はログインノードでは一切実行していません。したがって緑の主張はなく、実走 nodeid は0件、赤の内訳もありません。

実行済み静的検査:

- 変更した全 Python fileの `python3 -m py_compile`: 成功
- `git diff --check`: 成功
- `python3 tools/check_codex_agents.py`: 成功
- `python3 tools/check_docs.py`: 成功
- AST census:対象 `run_campaign()` 15 call 全て admission あり。対象 `evaluate()` の admission 欠落は、M3用の意図的 TypeError test 1箇所だけ。
- `build_admission.py` の `os.environ` / `getenv` 参照: 0件

親が計算ノードで実走すべき範囲は、新設T-316 nodeid群、quarantine・qualification・P3 AST試験、変更した共有fixtureの各test file、および以下のmeta-testです。

- `test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted`
- `test_plain_runner_coverage.py::test_allowlist_has_no_stale_or_self_runnable_entries`
- `test_dev_waves_isolation_contract.py::test_every_node_that_touches_process_external_resources_stays_serialised`

## 静的な波及可能性

- `critic/digest.py` は `build_start` payload を `.get()` で読むため、追加 receipt fieldを無視でき、consumer変更は不要です。
- `s8b_floor_campaign.run_campaign()` は同名の別APIであり、今回の `campaign.loop.run_campaign()` census外です。
- `buildcache.build()` を直接呼ぶ calibration、coverage、profile、S8b、kickoff seed等は裁定対象の共通 pipeline seam外です。今回の変更対象には含めていません。
- shared test fixtureへ admissionを追加したため、変更したtest file全体での計算ノード実走が必要です。
- `external/ccbench` を要する検査は未実走であり、sandbox/submodule由来の偽赤も観測していません。

## 親の裁定を仰ぐ点

- provenance classが判断不能な caller はありません。
- 「16 caller」と静的に確認できる実 call 15箇所との差は、`run_campaign()` 定義を含む数え方と判断しました。別の16番目を想定していた場合は親側で確認が必要です。
- pipeline外の直接 `buildcache` callerまで admission対象を広げるかは本裁定のscope外です。

`docs/**`、handoff、worklogは編集せず、`git add` / `git commit` も実行していません。

## 総括

実装範囲: immutable provenance admission、coder由来buildのCLI opt-in既定拒否、全対象caller配線、quarantine順序修正、実態に沿うdocstring訂正を実装しました。

テスト結果: 静的検査と全変更fileの構文検査は成功。Pegasusログインノードのためpytest・mutationは未実走です。

残る懸念: 親による計算ノード上の対象test・meta-test・M1〜M5 mutation実走と、caller数の数え方の確認が必要です。