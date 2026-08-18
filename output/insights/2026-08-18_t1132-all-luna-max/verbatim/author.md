実装済み・未実走です。指定どおり pytest、checker、build は実行していません。`git diff --check` のみ問題なしです。

## 総括

- 変更ファイル

  - [launch_authority.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-stage2-luna/tools/dev_waves/launch_authority.py): v1/v2 parser、live v2 guard、文法別 model mapping 検査を実装。
  - [check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-stage2-luna/tools/check_docs.py): DW-O01 literal をv2へ更新。DW-S06-A/Cのpinを`max`へ更新。不在検査と`-m <model>` exact 1件検査は不変。
  - [test_dev_wave_launch_authority.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-stage2-luna/orchestrator/tests/test_dev_wave_launch_authority.py): v2全7経路、v1 historical互換、live拒否、slug拒否、直列化不変を回帰化。
  - [test_check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-stage2-luna/orchestrator/tests/test_check_docs.py): v2 literalと`reasoning=max`へ期待値を更新。`high`の残存は拒否・decoy用fixtureのみ。
  - `docs/`、branch、commit、lane choices、argv契約は未変更。

- v1/v2判別とlive guard

  - `_MODEL_LINE_V1_RE`と`_MODEL_LINE_V2_RE`を独立定義し、可視top-level規範行が両文法を通じてexact 1件であることを要求。
  - v2も`gpt-[A-Za-z0-9._-]+`でslugを制限。
  - snapshotに`model_authority_version`を保持。
  - `commit=None`はv2のみ受理。明示commitではv1/v2双方を受理。
  - v1は`other_model == consult/sol`、v2はconsult 2要素とotherの全一致を検査。`derive_launch()`でも再検査し、後段でのmapping変異をfail-closedにした。

- `as_dict()`と`_aggregate_digest`

  - 両関数の実装は変更していない。
  - 新しい文法版fieldは`as_dict()`へ含めていない。
  - 直列化keyは従来どおり`authority_commit`、`sections`、`digest`のみ。
  - canonical JSONから従来式のdigestを再計算する回帰を追加した。

- 「段3の2レンズ異model」検査

  - live v2では7通りすべてが`gpt-5.6-luna`であることへ変更。
  - historical v1では`consult/sol != consult/luna`かつ他5段が`gpt-5.6-sol`であることを別途固定し、旧保証を削除していない。

- 追加した回帰テスト。すべて未実走。

  - `orchestrator/tests/test_dev_wave_launch_authority.py::test_v2_all_stage_and_lane_models_resolve_to_single_model`
  - `orchestrator/tests/test_dev_wave_launch_authority.py::test_authority_snapshot_serialized_contract_and_digest_are_unchanged`
  - `orchestrator/tests/test_dev_wave_launch_authority.py::test_v2_snapshot_mapping_inconsistency_fails_closed`
  - `orchestrator/tests/test_dev_wave_launch_authority.py::test_live_v1_is_rejected_but_historical_v1_is_reconstructed`
  - `orchestrator/tests/test_dev_wave_launch_authority.py::test_v2_model_slug_drift_fails_closed`の3 parameter

- 親docs未landによる期待赤

  - checker finding:
    - `DW-O01`のv2 model権威行不一致
    - `DW-S06-A`の`reasoning=max` pin不一致
    - `DW-S06-C`の`reasoning=max` pin不一致
  - launch-authority nodeid:
    - `test_snapshot_and_derive_current_authority_positive`
    - `test_review_effort_matches_independent_docs_cross_check`
    - `test_focus_effort_matches_independent_docs_cross_check`
    - `test_all_stage_models_match_independent_docs_cross_check`
    - `test_unicode_separator_outside_normative_candidate_is_accepted`の全10 parameter
    - `test_lane_validation_is_not_inferred_from_model_value`
  - check-docs nodeid:
    - `test_dev_wave_reasoning_effort_pins_accept_current_workers_contract`
    - `test_dev_wave_reasoning_effort_pins_accept_s06_b_inherited_without_literal`
    - real `workers.md`を使う`test_dev_wave_reasoning_effort_*`群のうち、`_mutated_workers_text`使用nodeと`test_dev_wave_reasoning_effort_pins_ignore_comment_and_fence_examples`、`test_dev_wave_reasoning_effort_pin_rejects_hidden_whole_s06_sections`
    - `test_dev_wave_model_pins_accept_current_docs_contract`
    - `test_normative_exact_section_pins_accept_real_repo`
    - `test_real_repo_clean`

- 所有外への静的波及

  - `tools/codex_worker_launch.py`のlive起動は、親がv2 docsをcommitするまでauthority preflightで拒否される。
  - 同ファイルのhistorical receipt再監査はv1を引き続き再構成でき、`historical.as_dict()`比較の形も不変。
  - `orchestrator/tests/test_codex_worker_launch.py`のlive launcher成功系は、docs未land中は同じpreflight拒否の影響を受ける。直接consumerには`test_positive_p1_normal_job_is_accepted`、`test_authority_bound_launch_uses_derived_model_and_effort`、`test_manifest_lock_covers_load_replace_critical_section`、`test_docs_authority_alone_rejects_consistent_effort_mutation`、`test_append_manifest_header_gate_fails_without_checker_mask`がある。
  - 共有fixtureでは`_prepare_repo`、`_build_min_repo`、`_mutated_workers_text`がdocs切替の影響面。
  - `DW-S05-A`の`reasoning=max`は親のdocs変更対象。checkerには従来からS05 effortの独立pinがなく、新設してscopeを広げてはいない。

- 実装できなかった点

  - なし。親所有のdocs更新、commit、テスト実測は未実施。
  - `dev-wave` skillの段5境界に従い、コードとテスト以外は変更していない。