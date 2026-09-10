実装単位 A を完了しました。所有外ファイル、docs、index、commit には触れていません。

### 実装内容

- [parse.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-s4-unit-a/orchestrator/verifier/parse.py)

  - `C` を exact 7-field の v2 専用に変更。
  - 5-field v1 を専用メッセージの `ParseError` で拒否。
  - `E <txid>` を必須化。
  - `count-mismatch` / `missing-end` / `duplicate-end` の `TxnFramingViolation` を追加。
  - 負 txid、負の宣言件数、余分な C/E field、E txid 不一致を拒否。
  - X/I を R/W 件数から除外。
  - 直後の重複 E のみ structured issue とし、直後でない重複 E は `ParseError` を維持。

- [model.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-s4-unit-a/orchestrator/verifier/model.py)、[core.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-s4-unit-a/orchestrator/verifier/core.py)、[report.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-s4-unit-a/orchestrator/verifier/report.py)

  - `Integrity.framing_violations: int = 0` を追加。
  - `Integrity.clean()` に zero 条件を追加。
  - kind 別件数と先頭 5 件の expected/observed を notes へ出力。
  - JSON/text report に固定名 `framing_violations` を追加。
  - cycle がある場合の `non-serializable` 優先順位は維持。

- fixture 16 本

  - 一時 converter で v2 化。
  - exact path 集合、入力 v1/no-E、C/R/W 限定、同一 txid 計数を検査。
  - metadata と E を除く逆射影が移行前 HEAD bytes と完全一致。
  - converter は削除済み。

- [test_verifier.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-s4-unit-a/orchestrator/tests/test_verifier.py)

  - HEAD 基準の `_tmp_trace(` 28 出現（helper 定義 1、実 call 27）を照合し、既存 call の literal をすべて明示 v2 化。
  - helper に自動変換や既定件数は追加していない。
  - characterization を `test_characterization_txn_tail_loss_is_indeterminate` へ反転。
  - `{−1, 1}`、X/I 非計数、framing 三種、E 不一致、非直後 E、`0 0` 正例、cycle 優先などを追加。
  - fixture 全 16 本の `framing_violations == 0` を exact 集合込みで固定。

### 検査結果

軽量な pytest 非依存 runner:

- 範囲: `orchestrator/tests/test_verifier.py::*`、全 70 node
- 結果: `69 passed, 0 failed, 1 skipped`
- skip: `orchestrator/tests/test_verifier.py::test_real_silo_serializable` — 既存 Silo sample 不在

主要な新設・改名 node はすべて PASS しました。

- `::test_v1_c_record_is_rejected`
- `::test_negative_txid_is_rejected_before_gap_math_can_cancel_it`
- `::test_declared_read_and_write_counts_must_match`
- `::test_missing_end_is_indeterminate`
- `::test_duplicate_end_is_indeterminate`
- `::test_end_txid_mismatch_is_parse_error`
- `::test_non_immediate_duplicate_end_remains_parse_error`
- `::test_zero_read_zero_write_frame_is_valid`
- `::test_x_and_i_records_do_not_count_as_reads_or_writes`
- `::test_characterization_txn_tail_loss_is_indeterminate`
- `::test_all_v2_fixture_files_have_clean_framing`
- `::test_cycle_verdict_takes_priority_over_framing_violation`

pytest 経由は実装済み・未実走です。

- `python3 tools/run_tests.py orchestrator/tests/test_verifier.py -q`
- `python3 tools/run_tests.py orchestrator/tests/test_verifier.py --collect-only -q`

どちらも pytest 起動前に Pegasus `qstat -Q` preflight が失敗し、runner rc=16 でした。所有内テストの赤ではありません。収集規約は代わりに AST で全 70 test 名の一意性・zero-arg を確認しましたが、pytest collection の代替とは数えていません。

その他:

- `python3 tools/check_codex_agents.py`: PASS
- `python3 tools/check_docs.py`: PASS
- `git diff --check`: PASS
- 所有外変更: 0
- commit / `git add`: 未実施

### 所有外の要修正・期待赤

静的に以下への波及を確認しました。

- `orchestrator/campaign/silo_ladder_rung1.py`

  - acceptance に `framing_violations == 0` が必要。
  - integrity exact key-set に新 counter が必要。
  - 凍結 v1 bundle の再検証経路は段 4 R3 に従う退役が必要。

- `orchestrator/tests/test_t152_write_intent_coverage.py`

  - `INTEGRITY_COUNTERS` mirror への追加が必要。

- `orchestrator/tests/test_silo_ladder_rung1_driver.py`

  - 合成 integrity と合成 trace literal の v2 化が必要。

- `orchestrator/tests/test_campaign.py`

  - 3 箇所の trace literal がまだ v1。

- `orchestrator/tests/test_silo_ladder_rung1_evidence.py`

  - 凍結 v1 bytes を verifier へ再投入する correctness leg の退役対象。

これらは単位 B 所有であり、本単位では編集していません。統合前に出る schema/literal 起因の赤は期待赤です。

## 総括

trace verifier を v2 専用化し、R/W 件数と必須 E の framing integrity、負 txid 拒否、X/I 非計数、report counter、fixture 16 本と verifier テストの移行を実装しました。所有内の軽量 runner は 69 PASS・0 FAIL・既存 sample 不在の 1 SKIPです。pytest/collection は Pegasus 基盤 rc=16 のため実装済み・未実走で、親の統合 pytest と所有外 consumer 更新が残件です。