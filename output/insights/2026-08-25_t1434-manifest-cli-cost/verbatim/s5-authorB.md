## 実装した変更

- [tools/codex_reasoning_ab.py:12](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-manifest-cli-cost/tools/codex_reasoning_ab.py:12): `Decimal`、`ROUND_HALF_EVEN`、`localcontext` を追加。
- [tools/codex_reasoning_ab.py:9490](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-manifest-cli-cost/tools/codex_reasoning_ab.py:9490): snapshot bytes を一度だけ読み、固定 SHA-256 と validator を同じ bytes に適用する cost loader を追加。
- [tools/codex_reasoning_ab.py:9531](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-manifest-cli-cost/tools/codex_reasoning_ab.py:9531): token 可用性の三値判定を追加。
- [tools/codex_reasoning_ab.py:9616](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-manifest-cli-cost/tools/codex_reasoning_ab.py:9616): mapping-driven の試行別部分計上額を実装。
- [tools/codex_reasoning_ab.py:9701](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-manifest-cli-cost/tools/codex_reasoning_ab.py:9701): 観測済み試行だけを数える軸集計を追加。
- [tools/codex_reasoning_ab.py:10011](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-manifest-cli-cost/tools/codex_reasoning_ab.py:10011): bound v3 かつ schedule descriptor 有りの場合だけ費用計算を発火。
- [tools/codex_reasoning_ab.py:10320](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-manifest-cli-cost/tools/codex_reasoning_ab.py:10320): `resource_ledger` 行へ `normalized_cost` を追加。
- [tools/codex_reasoning_ab.py:10423](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-manifest-cli-cost/tools/codex_reasoning_ab.py:10423): top-level `normalized_cost_axis_ledger` を追加。

出力には通貨、per-million 単価表、凍結 version、`cache_write` 未計上、partial coverage、`not-certified` を併記します。`_certification_scope` は変更していません。

## 三値の可用性をどう判定したか

- `observed`: 4 token field が exact int、非負、かつ全 0 ではない。さらに `cached_input_tokens <= input_tokens` と `reasoning_output_tokens <= output_tokens` を要求。
- `unavailable`: replay 失敗、field 欠落、bool・文字列などの非 exact int、負値、観測根拠のない全 0。
- `not-incurred`: `prelaunch_failure is not None`、または未起動の pair mate。

`attempt_count` と軸の `accounted_amount` には `observed` だけを入れます。`unavailable` と `not-incurred` には金額 keyを出しません。

## 恒偽として実装しなかった拒否条件

次の独立した `ValidationError` gate は cost 層に追加していません。

- 未対応 operation と field grammar: [tools/t189_price_snapshot.py:617](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-manifest-cli-cost/tools/t189_price_snapshot.py:617) の `_validate_receipt_mapping` が固定 mapping と照合。
- mapping への `reasoning_output_tokens` 混入: 同じ固定 mapping 照合が上流で拒否。
- 非 decimal、非有限、0 以下の単価: [tools/t189_price_snapshot.py:627](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-manifest-cli-cost/tools/t189_price_snapshot.py:627) の `_validate_prices` が拒否。

cost interpreter 側には「上流で担保」のコメントを置き、対応 operation の意味だけを実装しました。

## 追加・変更したテスト

追加先は [test_codex_reasoning_ab.py:13636](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-manifest-cli-cost/orchestrator/tests/test_codex_reasoning_ab.py:13636) 以降です。

主な nodeid:

- `test_m10_cost_snapshot_loader_reads_and_validates_one_byte_observation`
- `test_p01_bound_cost_is_mapping_driven_decimal_partial_and_uncertified`
- `test_m01_unavailable_zero_tokens_never_enter_cost_denominator`
- `test_m02_prelaunch_zero_tokens_are_not_incurred_and_not_counted`
- `test_replay_failure_tokens_are_unavailable_and_not_counted`
- `test_cost_token_field_unavailable_matrix`
- `test_m03_cost_json_tree_contains_no_float`
- `test_m04_cost_rounding_is_eight_place_half_even`
- `test_m05_reasoning_tokens_are_validated_but_never_added_to_output_cost`
- `test_m06_cached_input_cannot_exceed_input_for_cost`
- `test_m07_cache_write_is_unaccounted_and_never_a_zero_component`
- `test_m08_p02_p04_null_v3_and_legacy_emit_no_cost_keys`
- `test_schedule_descriptor_absence_emits_no_cost_keys`
- `test_m09_unknown_model_has_one_direct_cost_rejection`
- `test_cost_constant_false_rejections_are_owned_by_snapshot_validator`

既存テストは改変せず、新設テストだけを末尾の制約 meta-test より前へ追加しました。

## 実走結果

pytest は実走できていません。

- 焦点 nodeid 群: runner `rc=16`、`child_started=false`、pytest 実行 0 件。
- `test_m04_cost_rounding_is_eight_place_half_even` 単独再試行: 同じく `rc=16`、pytest 実行 0 件。
- 原因: Pegasus の `qstat -Q preflight rc=1`。queue 状態も観測不能でした。
- pytest 緑: 0 件。
- pytest 赤: 0 件。
- infrastructure failure: 2 回。
- 制約 meta-test、既存 consumer test、ファイル全体: 未実走。

read-only 診断では以下を確認しました。

- 2 ファイルの AST parse 成功。
- sol `0.00051000`、luna `0.00002750`。
- 全 0 は `unavailable`。
- half-even tie は `0.00000000`。
- 軸 `attempt_count=1`、`cache_write` component 無し。
- 凍結 snapshot は SHA-256 `a0b2c716...b3b1`、2591 bytes のまま。

runner が生成した今回分の dispatch request・receipt・script は正確な生成先から削除しました。再実行すれば再生成可能な一時成果物です。

## 変異 M01〜M10 の単一理由性の確認

| 変異 | 確認結果 |
|---|---|
| M01 | cost seam では単一。全 0 を `unavailable` とし、部分計上額と分母の双方に入らないことを一つのテストで固定。通常の launched receipt には上流の全 0 診断もあるが、人工 0 行の cost 分母は上流では守られない。 |
| M02 | 単一。prelaunch row は `not-incurred` となり、対応 axis 自体が生成されない。 |
| M03 | 単一。cost subtree と軸金額を decimal string に固定し、float 混入を再帰検査。 |
| M04 | 単一。8 桁の tie 値で half-even と half-up を分離。 |
| M05 | cost seam では単一。reasoning 0 と 10 の金額同一性、および 11 の範囲拒否を固定。射影外の ledger 内部まで含む上流重複は確認対象外。 |
| M06 | direct helper では理由が一つ。ただし [tools/codex_reasoning_ab.py:8173](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-manifest-cli-cost/tools/codex_reasoning_ab.py:8173) に上流の cached/input 拒否がある。end-to-end の単一理由性は確認できないため、厳密な登録条件なら取り下げ推奨。 |
| M07 | 単一。`unit_prices.cache_write` は残る一方、component には存在しないことを固定。 |
| M08 | 単一。all-null v3 と legacy v2 の正例で cost key 不在を固定。拒否ではなく過剰発火を検出する。 |
| M09 | direct helper では理由が一つ。ただし [tools/codex_reasoning_ab.py:8932](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-manifest-cli-cost/tools/codex_reasoning_ab.py:8932) が unknown model を先に拒否する。end-to-end mutation としては恒偽なので取り下げ推奨。 |
| M10 | 単一。cost loader の path read 回数を exact 1 に固定。同じ bytes から validator の fresh tree を返す。 |

pytest 未実走のため、上表はコードとテスト構造の静的確認であり KILLED 実測ではありません。

## 波及可能性の静的列挙

射影範囲で確認した波及先は次です。

- 呼び出し元: [verify_manifest](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-manifest-cli-cost/tools/codex_reasoning_ab.py:11112)、`aggregate_manifest`。
- 共有 fixture: `_bound_price_schedule`、`_aggregate_rows`、`_full_manifest`、`_synthetic_task_manifest`。
- 既存 consumer test:
  - `test_bound_price_reaches_supervisor_replay_verify_and_aggregate_consumers`
  - `test_verify_replays_complete_fake_codex_experiment`
  - `test_aggregate_verified_uses_oracle_kind_and_keeps_task_model_axes_separate`
  - `test_bound_price_aggregate_rejects_attempt_price_mismatch`
  - `test_zero_component_total_only_aggregate_counts_by_arm_and_case`
  - `test_m9_post_treatment_failure_remains_in_denominator`
  - `test_asymmetric_technical_pair_retry_marks_mate_and_keeps_resources`
  - `test_f3_2_pair_invalidated_post_treatment_occurrence_is_reliable`
  - `test_incomplete_or_verifier_reason_nulls_quality_ledgers`
  - `test_single_turn_constant_is_not_emitted_as_resource_metric`
- projected file 外の exact top-level schema consumer は未走査です。

実装子 A の task-manifest loader、digest 連鎖、CLI option、consumer 伝播部分は編集していません。既存 fixture も書き換えていません。ただし回帰 pytest は未実走です。

## 現行の受理・拒否挙動と、変更後の差分

変更前:

- bound v3 は固定 price snapshot 検査後に受理するが、費用 key は生成しない。
- all-null v3、v2、descriptor 無しも費用 key 無しで受理。
- 起動前失敗の人工 0 と replay 失敗の `None` を resource 行へ写すだけ。

変更後:

- bound v3、descriptor 有り、token 観測済みなら per-run と軸に部分計上額を生成。
- 観測不能 row は 0 金額に変換せず、分母にも入れない。
- malformed token 関係は bound report を invalid にする。
- all-null v3、v2、descriptor 無しは従来と同じ受理集合・同じ cost key 不在。
- `_certification_scope`、task manifest 契約、uncertified 性は不変。

## 総括

B-1〜B-9 の実装と M01〜M10/P01/P02/P04 のテスト追加は完了しました。残した編集は指定された 2 ファイルだけで、commit は作成していません。凍結 snapshot bytes も不変です。

ただし pytest は dispatch infrastructure failure により 0 件実走です。したがって「実装済み・pytest 未実走」であり、`closed` や緑とは申告しません。M06 と M09 は upstream 重複または到達不能性があるため、変異登録の取り下げを推奨します。