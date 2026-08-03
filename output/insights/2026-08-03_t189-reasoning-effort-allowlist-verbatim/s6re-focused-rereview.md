判定は **NO-GO**。FX1〜FX6 のコード修正は妥当だが、現在の `mutation-spec.json` が段4の V6 と V9 を再現していないため、このまま変異本走へ進めない。

## 1. 所見対応表

| 対象 | 判定 | 独立確認した根拠 |
|---|---|---|
| R1-1 V5 E2E 不在 | closed | 永続 spec を `load_worker_spec()`→`build_child_argv()`へ流すテストが追加された。[test_dev_waves_worker.py:90](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/tests/test_dev_waves_worker.py:90)、[worker.py:590](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/tools/dev_waves/worker.py:590)、[worker.py:231](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/tools/dev_waves/worker.py:231) |
| R1-2 V7〜V9 正例が正本を反復 | closed | 面2・3は独立リテラル五値になった。[test_dev_waves_cli.py:150](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/tests/test_dev_waves_cli.py:150)、[test_dev_waves_schema.py:287](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/tests/test_dev_waves_schema.py:287)。面1もリテラル parameterize。[test_codex_worker_launch.py:554](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/tests/test_codex_worker_launch.py:554) |
| R1-3 通常 import 未検査 | closed | 通常 package import と直接 load の両定数を比較する。[test_effort_levels.py:45](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/tests/test_effort_levels.py:45) |
| R1-4 T-183/T-184 所有参照欠落 | closed | docstring に恒久対応の所有先が明記された。[effort_levels.py:7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/tools/dev_waves/effort_levels.py:7) |
| R2-1 V3/V4 anchor 重複・V6 二地点 | partial | R2 の長い V3/V4 anchor は現在各1箇所。ただし現行 spec は V6 を V06/V07 に分割している。[schema.py:801](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/tools/dev_waves/schema.py:801)、[schema.py:858](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/tools/dev_waves/schema.py:858)、[mutation-spec.json:95](/work/1/SFC/tanab/dev-wave-jobs/t189-reasoning-allowlist/mutation-spec.json:95) |
| R2-2 V5 node 短絡・E2E 欠落 | closed | spec/argv 負例が別関数になり、worker E2E も追加された。[test_dev_waves_schema.py:271](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/tests/test_dev_waves_schema.py:271)、[test_dev_waves_schema.py:279](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/tests/test_dev_waves_schema.py:279)、[test_dev_waves_worker.py:90](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/tests/test_dev_waves_worker.py:90) |
| R2-3 V7/V9 fixture mask | closed | 両正例とも正本と独立したリテラル五値。[test_dev_waves_cli.py:151](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/tests/test_dev_waves_cli.py:151)、[test_dev_waves_schema.py:288](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/tests/test_dev_waves_schema.py:288) |
| R2-4 V8 先回り assertion | closed | 正例関数は直接 `_run_case()` を呼び、同関数が subprocess を起動する。[test_codex_worker_launch.py:558](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/tests/test_codex_worker_launch.py:558)、[test_codex_worker_launch.py:421](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/tests/test_codex_worker_launch.py:421) |
| R2-5 V10 が TypeError になる | closed | spec の `new` は `effort = item["effort"]` であり、membership の `unknown` へ遷移する。[mutation-spec.json:185](/work/1/SFC/tanab/dev-wave-jobs/t189-reasoning-allowlist/mutation-spec.json:185)、[test_dev_waves_schema.py:294](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/tests/test_dev_waves_schema.py:294) |
| R2-6 meta-test 未実走 | partial | 自走 runner は存在するが、fix 報告自身が pytest/plain runner 未実行と記録している。[test_effort_levels.py:72](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/tests/test_effort_levels.py:72)、[s6fix-report.md:64](/work/1/SFC/tanab/dev-wave-jobs/t189-reasoning-allowlist/s6fix-report.md:64) |
| FX1 負例分割 | closed | 独立した `test_worker_spec_rejects_unknown_effort` / `test_child_argv_rejects_unknown_effort` が実在。上記 R2-2 根拠。 |
| FX2 永続 spec E2E | closed | load→parse→build→validate の実経路を使用。上記 R1-1 根拠。 |
| FX3 独立リテラル正例 | closed | 上記 R1-2 根拠。 |
| FX4 pre-assertion 削除 | closed | `_run_case()` 前に membership assertion はない。上記 R2-4 根拠。 |
| FX5 ownership 追記 | closed | [effort_levels.py:11](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/tools/dev_waves/effort_levels.py:11) |
| FX6 通常 import 検査 | closed | [test_effort_levels.py:45](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/tests/test_effort_levels.py:45) |

## 2. 変異帰属の再判定

| ID | old の一意性 | 現在の期待赤 node | mask / 判定 |
|---|---|---|---|
| V1 | 1箇所。[codex_worker_launch.py:2476](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/tools/codex_worker_launch.py:2476) | `test_unknown_reasoning_is_rejected_before_child_launch` | 手前 mask なし。成立。 |
| V2 | 1箇所。[cli.py:93](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/tools/dev_waves/cli.py:93) | `test_serve_rejects_unknown_effort_as_invalid_choice` | 手前 mask なし。成立。 |
| V3 | R2 の長い anchor は1箇所。[schema.py:801](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/tools/dev_waves/schema.py:801) | `test_worker_spec_rejects_unknown_effort` | 直接 node は V4 に mask されない。E2E は V4 が意図的に守る。成立。 |
| V4 | R2 の長い anchor は1箇所。[schema.py:858](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/tools/dev_waves/schema.py:858) | `test_child_argv_rejects_unknown_effort` | 直接 node は V3 に mask されない。E2E は V3 が意図的に守る。成立。 |
| V5 | V3→V4 の累積適用で各1箇所 | V3/V4 の2 node＋`test_persisted_unknown_effort_is_rejected_by_child_argv_path` | 両層同時時だけ E2E が赤になる。成立。 |
| V6 | CLAUDE/CODEX tuple は各1箇所。[effort_levels.py:18](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/tools/dev_waves/effort_levels.py:18) | Codex負例、CLI負例、spec負例、argv負例、worker E2E、exact-vocabulary の計6 node | 二 replacement の一つの V6 なら成立。現行 spec は二変異へ分割しており不成立。 |
| V7 | CLAUDE tuple は1箇所 | `test_serve_accepts_every_allowed_effort`、`test_worker_spec_and_child_argv_accept_every_allowed_effort`、`test_effort_vocabularies_are_exact_and_ordered` | `max` は独立リテラルなので削除時に実入力される。成立。 |
| V8 | CODEX tuple block は1箇所 | `test_all_repo_policy_reasoning_values_are_accepted[max]`、`test_effort_vocabularies_are_exact_and_ordered` | `_run_case()`→`subprocess.run()`まで到達して CLI の拒否で赤。成立。 |
| V9 | CLAUDE tuple は1箇所 | V7 と同じ3関数（loop 内 `low`。`[low]` suffix は付かない） | コード上は成立。ただし現行 spec は `low` でなく `xhigh` を削除しており、事前登録 V9 は不在。 |
| V10 | assignment は1箇所。[schema.py:802](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/tools/dev_waves/schema.py:802) | `test_effort_shape_errors_precede_membership_errors` | `new = effort = item["effort"]` なら `string→unknown`。diagnostic pin として成立。semantic kill には数えない。 |
| V11 | launcher set block は1箇所。[launcher.py:85](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/codex_roles/launcher.py:85) | `test_launcher_reasoning_policy_is_subset_of_repo_policy` | 直接 subset meta-test。成立。 |

### V3/V4/V5/V6 で使う old

短い membership blockだけでは2箇所に存在する。V3/V4/V5 は次を使えば各1箇所になる。

V3:

```python
    model = _required_string(item["model"], _MODEL_RE, label="model")
    effort = _required_string(item["effort"], _EFFORT_RE, label="effort")
    if effort not in CLAUDE_EFFORTS:
        raise DevWavesError(ReasonCode.INVALID_ARGS, {
            "label": "effort", "kind": "unknown",
        })
```

V4:

```python
    if not _MODEL_RE.fullmatch(model) or not _EFFORT_RE.fullmatch(effort):
        raise DevWavesError(ReasonCode.INVALID_ARGS, {"label": "child-argv", "kind": "model-effort"})
    if effort not in CLAUDE_EFFORTS:
        raise DevWavesError(ReasonCode.INVALID_ARGS, {
            "label": "effort", "kind": "unknown",
        })
```

V6 は次の2 replacementを同じ変異内で累積適用する。各 old は1箇所。

```python
CLAUDE_EFFORTS: tuple[str, ...] = ("low", "medium", "high", "xhigh", "max")
```

```python
CODEX_REASONING_EFFORTS: tuple[str, ...] = (
    "low",
    "medium",
    "high",
    "xhigh",
    "max",
)
```

### V5 の三条件

三条件を満たす。

- V3だけを外す: `load_worker_spec()` は通るが、`build_child_argv()` 内の `validate_child_argv()` が拒否する。
- V4だけを外す: `load_worker_spec()`→`parse_worker_spec()` が先に拒否する。
- V3+V4を外す: argv が返り、テスト末尾の `AssertionError` に到達する。

実 spawn も `spawn_worker()` が spec を loadし、`_spawn_stopped()` が同じ `build_child_argv()` を使う。[worker.py:595](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/tools/dev_waves/worker.py:595)、[worker.py:393](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/tools/dev_waves/worker.py:393)。daemon 側も spawn 前に同じ build を呼ぶ。[daemon.py:1223](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/tools/dev_waves/daemon.py:1223)

### V7/V9 と全体検索

V7 (`max` 削除) で赤になる全 node は次の3件である。

- `test_serve_accepts_every_allowed_effort`
- `test_worker_spec_and_child_argv_accept_every_allowed_effort`
- `test_effort_vocabularies_are_exact_and_ordered`

V9 (`low` 削除) も、上記3 nodeだけを選ぶ node-scoped runnerなら同じ集合になる。ただし `test_dev_waves_integration.py` 全体を runner に含めてはならない。共有 `_profile()` が `effort="low"` を供給し、valid wave は `build_child_argv()` に到達するためである。[test_dev_waves_integration.py:244](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/tests/test_dev_waves_integration.py:244)、[daemon.py:1194](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/tools/dev_waves/daemon.py:1194)

全ファイルを含めると、少なくとも次の32関数族（parameterize の全該当ケース）が追加で失敗する。

```text
test_accepted_reconciliation_rebinds_repo_identity_and_main_branch
test_accepted_reconciliation_rejects_dirty_repo_without_child_rerun
test_active_check_failure_occurs_only_after_passive_gates
test_artifact_aggregate_cap_stops_before_next_wave_side_effect
test_auto_unavailable_or_permission_abort_never_rebuilds_dangerous_argv
test_blocked_receipt_with_main_move_is_failed_not_blocked
test_budget_accumulates_across_waves_and_deadline_boundary_is_clipped
test_cancel_identity_mismatch_records_ambiguous_not_signalled
test_cancel_running_child_persists_signal_prepare_then_observe
test_capacity_gate_stays_closed_when_an_artifact_vanishes_mid_measure
test_child_failure_injection_stops_before_next_wave
test_dedicated_provenance_and_code_dirty_reasons_are_wired
test_each_outcome_has_one_terminal_mapping_and_never_starts_next_child
test_fake_handshake_failure_persists_exact_terminal_reason
test_fake_manifest_run_id_is_bound_to_path_namespace
test_fake_manifest_wave_index_is_bound_to_wNNN_namespace
test_fold_success_scenario_declares_a_verified_direct_child_fold
test_independent_gate_failure_stops_next_wave
test_malformed_child_output_is_output_invalid
test_max_run_bytes_counts_wal_and_all_artifacts_but_excludes_git_worktree
test_one_wave_success_accepts_exact_fake_receipt_and_landing
test_real_daemon_sigkill_after_accepted_reconciles_without_child_rerun
test_real_daemon_sigkill_restart_closes_recovery_gate_at_three_points
test_resume_never_duplicates_child_or_land
test_second_distinct_submit_is_busy_while_run_active
test_shutdown_running_child_uses_same_prepared_signal_path
test_spawn_identity_read_failure_kills_and_reaps_exact_popen
test_supervisor_wal_fsync_failure_orders_real_worker_spawn_side_effect
test_terminal_state_precedes_quiescence_and_wait_idle_leaves_no_run_thread
test_three_wave_success_uses_distinct_pid_start_and_session_markers_without_transcript_carryover
test_valid_receipt_with_wrong_binding_is_receipt_invalid
test_vanished_rewrite_scratch_is_skipped_but_lost_artifact_fails_closed
```

したがって V9 は3 nodeを明示した node-scoped runnerに固定するのが単一理由性を保つ。`test_codex_reasoning_ab.py` の `max`、provenance fixture の `reasoning=xhigh`、workflow-model fixture の `effort=low`、role-runtime の `reasoning.effort=low` は別APIであり、この正本を参照しない。

### V8 の subprocess 到達

`max` は parameterize のリテラルに残り、テスト本体は直ちに `_run_case()` を呼ぶ。[test_codex_worker_launch.py:554](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/tests/test_codex_worker_launch.py:554)。同 helper は `subprocess.run()` を実行するため、`max` 削除時は実 launcher CLI の `choices=` で rc=2 になり、`returncode == 0` assertion が赤になる。[test_codex_worker_launch.py:421](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/tests/test_codex_worker_launch.py:421)

## blocker — 現行 mutation spec が段4の事前登録と一致しない

- 根拠: 段4は V6 を一つの正本追加変異、V9 を `low` 削除と定義する。[s4-adjudication.md:132](/work/1/SFC/tanab/dev-wave-jobs/t189-reasoning-allowlist/s4-adjudication.md:132)、[s4-adjudication.md:140](/work/1/SFC/tanab/dev-wave-jobs/t189-reasoning-allowlist/s4-adjudication.md:140)。現 spec は V6 を V06/V07 に分割し、V09 では `xhigh` を削除している。[mutation-spec.json:95](/work/1/SFC/tanab/dev-wave-jobs/t189-reasoning-allowlist/mutation-spec.json:95)、[mutation-spec.json:115](/work/1/SFC/tanab/dev-wave-jobs/t189-reasoning-allowlist/mutation-spec.json:115)、[mutation-spec.json:150](/work/1/SFC/tanab/dev-wave-jobs/t189-reasoning-allowlist/mutation-spec.json:150)
- 失敗シナリオ: 現 spec は全 anchor count が1で、`xhigh` 削除も同じ3テストに検出されるため、harness は KILLED を返し得る。しかし `low` 過剰拒否は一度も注入されず、V7以降のIDも段4とずれる。
- 成果物影響: mutation ledger と材料レポートが、未実施の V9 および分割された V6 を事前登録どおりの proof と誤表示し、受理集合の証明鎖が不正になる。

修正すべき対応は、V06/V07を一つの V6へ統合し、以後を V7〜V11へ戻し、V9 の `new` を `("medium", "high", "xhigh", "max")` にすること。

## 3. 回帰確認

- 本 wave 前から存在した assertion の反転・緩和・skip・削除はない。schema の既存 WorkerSpec fixture は既定 `"high"` の helperへ等価移動しただけ。[test_dev_waves_schema.py:233](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/tests/test_dev_waves_schema.py:233)
- worker `_spec()` の `effort` は keyword-only、既定値は `"high"`。[test_dev_waves_worker.py:48](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/tests/test_dev_waves_worker.py:48)。既存16呼出しは全て先頭2引数だけを positional にしており、追加引数による位置ずれはない。
- Codex launcher test helperの既定も `"high"` のまま。[test_codex_worker_launch.py:332](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/tests/test_codex_worker_launch.py:332)
- CLI は top-level `test_*` が15関数、`_run()` の呼出しも15件で、欠落・余分とも0。[test_dev_waves_cli.py:389](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t189-reasoning-allowlist/orchestrator/tests/test_dev_waves_cli.py:389)
- `integrated-snapshot.patch` と `final-integrated.patch` の section hashを比較し、指定された実装本体5ファイルはすべて同一だった。fix で変わった production file は `effort_levels.py` の docstringだけ。
- 現在の staged diff は `final-integrated.patch` と SHA-256 が一致する。`git diff --cached --check` は rc=0。
- 実装・既存テストに新しい回帰は静的には認めない。

## 総括

- GO / NO-GO: **NO-GO** — fix コードは妥当だが、現行 mutation spec の V6分割・V9誤変異を直す必要がある。
- closed / partial / regressed: **14 / 2 / 0**
- 帰属が成立しない変異の ID: **V6, V9**（現行 mutation spec 基準）
- 親が old 逐語の一意性に注意すべき ID: **V3, V4, V5, V6**
- pytest: **走らせていない。静的検査のみ。**