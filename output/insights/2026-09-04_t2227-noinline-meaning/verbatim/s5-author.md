## 変更した file と要点

- [condition_meaning_gate.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2227-noinline-meaning/orchestrator/campaign/condition_meaning_gate.py:178)
  - `BACKOFF_NOINLINE` を header-owned witness として登録。
  - factory は noinline の 0/0・1/0 だけ宣言。既存 8 macro は従来の 1/0 限定。
  - cache route を共有 build root から除外。
  - directory symlink と `.git` を追わない deep mirror を実装し、shadow owner TU を compile operand に指定。
  - 要求値 0 では値 1 を対照に使用。
  - validator は noinline の 0/1 順と1/0順を受理し、既存 8 macro は1/0固定。
  - evidence field、phase 名、`RELATED_DEFINE_DECODE_MACROS`、CLI、旧宣言型、新 reason code は変更なし。
- [paper_story_a2_certification.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2227-noinline-meaning/orchestrator/campaign/paper_story_a2_certification.py:577): factory を初期宣言にし、`BACKOFF_FIXED` legacy 上書きを維持。
- [s1_direct_comparison.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2227-noinline-meaning/orchestrator/campaign/s1_direct_comparison.py:266): factory を先に呼び、`None` の場合だけ legacy helper へ fallback。
- [t1683_rr5_cost_probe.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2227-noinline-meaning/tools/pegasus/probes/t1683_rr5_cost_probe.py:146): noinline を factory 宣言へ接続。`BACKOFF_FIXED=-1` は legacy のまま。
- [backoff.hh fixture](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2227-noinline-meaning/orchestrator/tests/fixtures/condition_meaning_gate/supplied/include/backoff.hh:1): patch と同じ3行を追加。
- [test_condition_meaning_gate.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2227-noinline-meaning/orchestrator/tests/test_condition_meaning_gate.py:717): registry、factory、deep mirror、0/1観測、供給・意味・admission、validator の正負例を追加。
- [test_paper_story_a2_certification.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2227-noinline-meaning/orchestrator/tests/test_paper_story_a2_certification.py:62): sentinel factory 配線を検証。
- [test_s1_direct_comparison.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2227-noinline-meaning/orchestrator/tests/test_s1_direct_comparison.py:62): factory 呼び出しと noinline meaning green を検証。
- [test_pegasus_calibration_workload.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2227-noinline-meaning/orchestrator/tests/test_pegasus_calibration_workload.py:104): 合成 workload で factory/legacy 宣言を検証。

変更は指定された9 fileだけで、commitしていません。

## 現行の受理・拒否挙動と変更後の差 (受理集合が狭まる向きだけであることの説明)

変更前は noinline の 0/0・1/0とも factory が `None` を返し、意味 arm は `unestablished` のまま admission を通過できました。

変更後は両要求に witness が発行され、0/1の枝選択を実 owner TU 経由で識別できれば green、できなければ red です。従来通過していたものが green の場合はそのまま通り、red の場合だけ新たに拒否されます。

cache route の別 build root 化は、登録前に noinline が使っていた経路を維持する修正です。登録の副作用による過剰拒否を防ぐもので、新しい受理面は作りません。既存8 macro、legacy declaration、CLI meaning-case、D1523、依存 file 実読検査は不変です。

## 実走した test (nodeid・結果) と未実走

pytest の緑結果はありません。すべて `tools/run_tests.py` 経由で試しましたが、`qstat -Q preflight rc=1`、`child_started=false`、`rc=16` となり、pytest 子は起動しませんでした。

単独実走を試みた範囲:

- `orchestrator/tests/test_condition_meaning_gate.py -q`
- `orchestrator/tests/test_paper_story_a2_certification.py -q`
- `orchestrator/tests/test_s1_direct_comparison.py -q`
- `orchestrator/tests/test_pegasus_calibration_workload.py -q`

新規 nodeid の targeted 実走も同じ理由で未起動:

- `test_backoff_noinline_header_owned_inert_meaning_observes_zero_and_one`
- `test_backoff_noinline_requested_one_supply_and_meaning_are_green`
- `test_header_shadow_preserves_directory_symlinks_and_git_link`
- `test_header_shadow_traversal_failure_is_structured`
- `test_backoff_noinline_factory_accepts_only_default_zero_binary_requests`
- `test_backoff_noinline_green_schema_rejects_nonbinary_and_same_value`

meta-test nodeid も未起動:

- `test_compile_time_branch_registry_and_fixtures_are_bound_to_real_patches`
- `test_v1_domain_and_claim_boundaries_are_exact`
- `test_condition_preflight_dominates_first_benchmark_build`
- `test_all_write_intent_macros_are_gated_before_stock_build`

compiler 不要の静的確認は成功しています。

- 8 Python file の AST parse
- 変更した4 test module の import
- 既存8 macro と noinline の factory 境界 smoke
- deep mirror の owner/header配置 smoke
- t1683 宣言配線 smoke
- `git diff --check`
- 結合文字検査

よって状態は「実装済み・pytest未実走」であり、closedとは申告しません。

## 変異 M1〜M10 を殺す test の対応表

| 変異 | 対応 test |
|---|---|
| M1 | `test_backoff_noinline_header_owned_inert_meaning_observes_zero_and_one`、`test_backoff_noinline_factory_accepts_only_default_zero_binary_requests` |
| M2 | `test_backoff_noinline_header_owned_inert_meaning_observes_zero_and_one` |
| M3 | noinline inert正例と要求1正例 |
| M4 | inert正例の preprocess argv が `request.owner_tu` を唯一の operand とする assert |
| M5 | `test_backoff_noinline_requested_one_supply_and_meaning_are_green`。cache route の build root 分離もassert |
| M6 | inert正例内の `_validate_arm_record_integrity` |
| M7 | `test_paper_condition_gate_is_p_strict_and_precedes_campaign` |
| M8 | `test_noinline_inert_meaning_record_comes_from_registry_factory` |
| M9 | `test_cost_probe_uses_factory_noinline_and_legacy_backoff_declarations` |
| M10 | 既存 `test_compile_time_factory_rejects_nonpaired_values` |

## 波及の静的列挙 (所有外 caller・共有 fixture・consumer test)

- 既存 factory caller: `s3_lock_coverage.py`、`s5_permutation_coverage.py`、`t152_write_intent_coverage.py`、`condition_gate_cli`。
- 新規配線 caller: A-2、s1、t1683。
- 非配線: backoff_sweep、backoff_repro、silo_ladder_rung1、paper_story_a1_paired は対象を要求しない。screening_driver は admission を成果物へ載せず、backoff_profile は関門を呼びません。
- fixture の直接 consumer: `test_condition_meaning_gate.py`、`test_t316_sandbox_probe.py`。
- `condition_gate_test_support` 経由の consumer: `test_build_site_gate.py`、`test_p3_build_authority_cli.py`、`test_p3_exploration_namespace.py`、`test_sort_swo_oracle.py`。
- registry/factory の制約 consumer test: `test_s5_permutation_coverage.py`、`test_t152_write_intent_coverage.py`。
- docs、policy JSON、patch、external、他 fixture は変更していません。

## 残る懸念

- Pegasus dispatch が復旧するまで、4変更 test file、meta-test、実 patch 木の compiler dogfood が未確認です。
- fixture は直接 include、実 CCBench は `transaction.hh` を介する二段 include なので、親段の実 patch 木走行が必要です。
- A-2 は別 scope の D1523 supply red が残る間、admission 全体は引き続き falseです。本変更の直接効果は noinline meaning record の確立です。
- repo外の A-2 attempt root、s1 output root、t1683 `--out` は未走査です。
- 依存 file 実読検査と新 reason codeは、裁定どおり実装していません。

## 総括

plan v2を指定9 fileへ実装し、既存8 macroとlegacy経路を維持したまま、`BACKOFF_NOINLINE` の header-owned 0/1枝選択 witnessをA-2・s1・t1683へ配線しました。

作業木は未commitです。静的確認は通過していますが、site dispatch障害のためpytest未実走です。