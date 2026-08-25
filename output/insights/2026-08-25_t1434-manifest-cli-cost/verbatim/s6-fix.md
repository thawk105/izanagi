実装は完了していますが、Pegasus dispatch 障害でテスト item が一件も開始されなかったため、状態は「実装済み・未実走」です。

## F1〜F8 の実装

- F1: [tools/codex_reasoning_ab.py:9597](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-manifest-cli-cost/tools/codex_reasoning_ab.py:9597)、[tools/codex_reasoning_ab.py:10625](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-manifest-cli-cost/tools/codex_reasoning_ab.py:10625)
  - 未起動 technical row と pair mate の4 token fieldを exact int 0、`model_calls` を exact int 0に限定。
  - marker があっても矛盾値は `not-incurred` にせず、material failure reason にします。

- F2: [tools/codex_reasoning_ab.py:11864](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-manifest-cli-cost/tools/codex_reasoning_ab.py:11864)
  - `verify-snapshot` から `--task-manifest` を外す fallback を採用。
  - snapshot 自体には先行 digest を保存する領域がなく、新機構を発明せず再ラベル経路を閉じるためです。未知引数として rc=2 で拒否されます。

- F3: [tools/codex_reasoning_ab.py:11528](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-manifest-cli-cost/tools/codex_reasoning_ab.py:11528)
  - 追記前に既存 verdict log 全 row を `_validate_verdict_row(..., task_manifest=...)` へ通します。

- F4: [tools/codex_reasoning_ab.py:8761](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-manifest-cli-cost/tools/codex_reasoning_ab.py:8761)、[tools/codex_reasoning_ab.py:10078](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-manifest-cli-cost/tools/codex_reasoning_ab.py:10078)、[tools/codex_reasoning_ab.py:10738](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-manifest-cli-cost/tools/codex_reasoning_ab.py:10738)
  - material manifest の最初の byte observation から tree、digest、schedule descriptor 状態を保持。
  - aggregate helper で path を再読しません。最終 `manifest_sha256` も同じ observation に固定しました。

- F5: [tools/codex_reasoning_ab.py:8887](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-manifest-cli-cost/tools/codex_reasoning_ab.py:8887)、[tools/codex_reasoning_ab.py:8943](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-manifest-cli-cost/tools/codex_reasoning_ab.py:8943)、[tools/codex_reasoning_ab.py:9097](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-manifest-cli-cost/tools/codex_reasoning_ab.py:9097)
  - schedule 検査が返す検証済み price snapshot tree を schedule rows とともに保持し、その同一 object を cost 層へ渡します。
  - production aggregate 経路から cost loader による二回目の snapshot read を除去しました。

- F6: [tools/codex_reasoning_ab.py:3451](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-manifest-cli-cost/tools/codex_reasoning_ab.py:3451)、[tools/codex_reasoning_ab.py:11868](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-manifest-cli-cost/tools/codex_reasoning_ab.py:11868)
  - snapshot oracle との束縛を採用。
  - `render-prompt` は外部 manifest の provenance を使用し、外部 digest では `--snapshot-oracle` を必須化して exact digest と case を検査します。
  - receipt に `task_manifest_sha256` と `snapshot_manifest_sha256` を記録します。外部 manifest だけを渡す経路は fail-closed です。

- F7: [tools/codex_reasoning_ab.py:9613](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-manifest-cli-cost/tools/codex_reasoning_ab.py:9613)、[tools/codex_reasoning_ab.py:9796](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-manifest-cli-cost/tools/codex_reasoning_ab.py:9796)
  - 観測不能というだけの `unavailable` は cost subtree の `failure_reason` にのみ残し、共有 `reasons` へ追加しません。
  - 型違反、負値、token 関係矛盾などの malformed input は従来どおり共有 reason となり、`valid=false` です。

- F8: [tools/codex_reasoning_ab.py:9850](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-manifest-cli-cost/tools/codex_reasoning_ab.py:9850)
  - 軸 row に `unavailable_count`、`not_incurred_count`、`scheduled_attempt_count` を追加。
  - `attempt_count` は引き続き observed 分母のみを表します。

digest 欠落診断にも、旧成果物は再生成が必要である旨を追加しました。[tools/codex_reasoning_ab.py:2731](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-manifest-cli-cost/tools/codex_reasoning_ab.py:2731)

## F7 の線引き

`valid` から外したもの:

- token が全てゼロで独立した観測証拠がない
- receipt replay 失敗により token を観測できない
- それらに伴う explanatory cost の欠落

`valid` を落とすまま残したもの:

- token field の欠落、bool、文字列など exact int 違反
- 負 token
- `cached_input_tokens > input_tokens`
- `reasoning_output_tokens > output_tokens`
- 未起動 marker と非ゼロ tokenまたは非ゼロ `model_calls` の矛盾
- 検証済み price tree の欠落や snapshot metadata の不整合

## 強化したテスト

主な nodeid と閉じた変異は以下です。

- `test_f1_supervisor_ledger_rejects_nonzero_not_launched_accounting[...]`
  - technical row と pair mate、4 token field と `model_calls` の非ゼロ変異。

- `test_m18_prelaunch_marker_never_hides_nonzero_accounting[...]`
  - marker 優先で矛盾値を `not-incurred` にする M18。

- `test_m19_verify_snapshot_rejects_task_manifest_option_by_fallback`
  - `verify-snapshot` の再ラベル M19。

- `test_f3_m15_append_verdicts_rejects_existing_log_manifest_exchange`
  - 既存 verdict log の digest 検査を外す変異。

- `test_f4_aggregate_uses_loaded_descriptor_state_without_manifest_reread`
  - descriptor helper の再読と、最終 manifest hash の別 observation。

- `test_m10_cost_snapshot_loader_reads_and_validates_one_byte_observation`
  - schedule 検証から cost 計算まで snapshot read exact 1、同一 tree identity。

- `test_m20_render_prompt_binds_external_task_manifest`
  - 外部 manifest を無視する変異、snapshot oracle 未束縛、digest mismatch。

- `test_m17_m21_p05_unavailable_cost_is_noncertifying_and_denominators_are_explicit`
  - unavailable が `valid` を落とす M17、分母内訳を落とす M21、P05。

- `test_f7_malformed_cost_input_remains_materially_invalid`
  - F7 修正で malformed input まで非 gate 化する過剰緩和。

- `test_p01_bound_cost_is_mapping_driven_decimal_partial_and_uncertified`
  - sol/luna の `accounted_amount`、全 component の token、単価、amount を exact 固定。

- `test_m03_cost_json_tree_contains_no_float`
  - `9_007_199_254_740_993` token を使い、float では保持できない桁を固定。

- `test_m04_cost_rounding_is_eight_place_half_even`
  - 2 component が個別には `0.00000000`、未丸め合計は `0.00000001` となる値で丸め順序を固定。

- `test_m07_cache_write_is_unaccounted_and_never_a_zero_component`
  - sol `5`、luna `0.25`、比率 exact 20を固定。

- `test_m08_p02_p04_null_v3_and_legacy_emit_no_cost_keys`
  - direct helper 検査に加え、digest 付き null v3 と v2 legacy を `make-packets` へ通す正例を追加。

- `test_m16_cli_external_manifest_is_loaded_before_alias_resolution`
  - option を持つ全10 verbについて、同一 external manifest object が dispatch 先へ届くことを検査。

- `test_task_manifest_digest_is_recorded_through_packet_freeze_and_reveal`
  - default ではなく external manifest を使い、producer が既定 digest を hard-code する変異を検出。

- `test_m15_supervise_pair_rejects_schedule_manifest_exchange`
- `test_m15_material_entrypoints_reject_manifest_exchange[aggregate]`
- `test_m15_material_entrypoints_reject_manifest_exchange[verify]`
- `test_m15_make_packets_rejects_schedule_manifest_exchange`
- `test_m15_freeze_verdicts_rejects_log_manifest_exchange`
- `test_m15_reveal_mapping_rejects_private_manifest_exchange`
  - M15 を consumer 別に分割。

- `test_material_replay_rejects_task_manifest_exchange_at_digest_consumers`
- `test_material_replay_rejects_schedule_task_manifest_exchange_at_digest_consumers`
- `test_material_replay_rejects_ledger_task_manifest_exchange_at_digest_consumers`
  - material、schedule、ledger の独立検査。

- `test_default_and_explicit_default_task_manifest_cli_results_are_equal`
  - default 同値だけでなく、external manifest の digest と task identity が明確に異なることを追加検査。

## 実装しなかったもの・止めたもの

- `_certification_scope` は変更していません。
- docs、凍結成果物、`tools/t189_price_snapshot.py`、output の永続成果物は変更していません。
- schema generation の改訂、cache-write 数量 receipt、resource gate 接続は親裁定どおり scope 外です。
- commit、add、stash、checkout は実行していません。
- ランナーが一時生成した dispatch 診断ディレクトリ2件と insights の一時コピーは除去しました。いずれもランナーまたは射影元から再生成可能です。
- テストは dispatch infrastructure failure で停止しました。直接 pytest へ迂回していません。

## 実走結果

実行コマンド:

```text
python3 tools/run_tests.py orchestrator/tests/test_codex_reasoning_ab.py
```

最終試行結果:

- runner rc: `16`
- child started: `false`
- passed: 計数不能
- failed: 計数不能
- skipped: 計数不能
- 実行された test item: `0`
- 原因: `qstat -Q preflight rc=1`
- 残る赤の nodeid: 未確定
- 新たに壊れた nodeid: 未確定

したがって、緑や closed とは申告しません。

静的確認のみ以下を完了しています。

- 両編集ファイルの AST parse 成功
- test function 378件、重複 nodeid 0件
- `git diff --check` 成功
- 最終 `git status --short` は指定された2ファイルのみ変更

## 波及可能性の静的列挙

- `verify-snapshot --task-manifest` は意図的な CLI breaking changeです。
- external `render-prompt` は snapshot oracle file が必要になります。
- prompt receipt に digest field が追加されるため、receipt の exact field set consumer に波及します。
- normalized cost axis row の field setと、unavailable-only axis の出現範囲が広がります。
- unavailable report は従来より `valid=true` になり得ますが、malformed report は引き続き invalid です。
- 矛盾した旧 prelaunch ledger は新 validator で拒否されます。
- digest 無し旧 artifact の診断文が変わります。
- `_validate_schedule` の返却 list は内部的に検証 context を保持する list subclass になりました。通常の sequence 操作は維持しています。
- material manifest と price snapshot の読取回数・読取時点が固定され、途中差し替え時の挙動が fail-closed 側へ変わります。
- mixed-manifest verdict log は append 時点で拒否され、後段まで進みません。

## 総括

F1〜F8 と指定された検出力強化を、許可された2ファイル内で実装しました。特に F2 は裁定 fallback、F6 は snapshot oracle 束縛を採用し、F7/F8 は「費用を gate にしない」と「分母内訳を明示する」を対で実装しています。

ただし指定テストは Pegasus infrastructure failure により未実走です。現時点の正確な状態は、**実装済み・未実走、closed ではない**です。