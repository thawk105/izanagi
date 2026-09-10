## 総括

指定範囲の fix は実装済みですが、Pegasus 実行基盤の問題でテスト本体は未実走です。このため規約に従い、全所見を `partial（実装済み・未実走）` と判定します。docs・preregistration・scope 外ファイルは編集せず、commit も作成していません。

| 所見 | 状態 | 対応 |
|---|---|---|
| D1 | partial | 新規テスト 2 本へ `pytest.main()` self-runner を追加 |
| C2 | partial | malformed・不足・重複 field/role を `malformed-approved-blob-ref` で拒否 |
| D2 | partial | 正しい三つ組の解決失敗は受理し、`unresolved-approved-blob-ref` 診断だけを記録 |
| C3 | partial | fragment の有無にかかわらず canonical `after_bytes` を常時検査 |
| D4 | partial | M8 用 marker literal・固定 ID、M9 用 direct/resume 実 `after_bytes` 改ざんテストへ変更 |

主な実装は [approval_guard.py:48](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/orchestrator/publication/approval_guard.py:48) と [test_t793_approval_guard.py:106](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/orchestrator/tests/test_t793_approval_guard.py:106) です。`addendum_p_envelope.py` の production 実装は変更していません。

### `tools/spool_fold.py` の変更箇所

- [tools/spool_fold.py:1038](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/tools/spool_fold.py:1038) — `_discover()` で専用 reason code を Issue 化
- [tools/spool_fold.py:1055](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/tools/spool_fold.py:1055) — guard の構造化 `(code, message)` 変換
- [tools/spool_fold.py:1076](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/tools/spool_fold.py:1076) — decision fragment の検証と、常時 `after_bytes` 追加
- [tools/spool_fold.py:2212](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/tools/spool_fold.py:2212) — 通常 plan 作成時の実 `after_bytes` 検査
- [tools/spool_fold.py:2363](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/tools/spool_fold.py:2363) — direct apply / durable state 適用前の再検査

### 3 経路の「書かれる bytes」検査点

- `_discover()` 通常経路: fragment 検査は [tools/spool_fold.py:1038](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/tools/spool_fold.py:1038)、描画後 `after_bytes` は [tools/spool_fold.py:1103](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/tools/spool_fold.py:1103) で追加され、[tools/spool_fold.py:2212](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/tools/spool_fold.py:2212) で検査
- direct `apply_fold()`: [tools/spool_fold.py:2363](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/tools/spool_fold.py:2363)
- CLI resume: state 読込は [tools/spool_fold.py:2582](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/tools/spool_fold.py:2582)、`apply_fold()` 呼出は [tools/spool_fold.py:2592](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/tools/spool_fold.py:2592)、実検査は同じ [tools/spool_fold.py:2363](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t793-pubcore-impl/tools/spool_fold.py:2363)

### 検査結果

次を `tools/run_tests.py` 経由で投入しましたが、すべて collection 前に `rc=16` で停止しました。

- `test_t793_approval_guard.py` + `test_t793_addendum_p_envelope.py`
- `test_plain_runner_coverage.py`
- `test_spool_fold.py`

原因は `qstat -Q` の `EACCTAUTH Unknown user-id`。local 側も 1 GiB の最小予算を確保できない headroom だったため、実行済み nodeid はありません。既知赤 4 件も実行・観測されていません。

静的検査は以下を通過しました。

- 対象 5 ファイルの AST parse: 5/5
- whitespace diff check
- canonical `approved_blobs:` 12 role の構文受理
- canonical 固定 blob 全件の marker gate 正例
- self-runner signal の存在確認

`test_spool_fold.py` で decision fragment 経路として影響し得る nodeid は次の 9 本です。

```text
test_spool_fold.py::test_n02_undefined_placeholder_is_rejected
test_spool_fold.py::test_n03_duplicate_symbol_definition_is_rejected
test_spool_fold.py::test_n04_malformed_placeholder_residue_is_rejected
test_spool_fold.py::test_all_mutating_operation_blocks_resolve_placeholders
test_spool_fold.py::test_failure_supersede_body_resolves_cross_ledger_placeholder
test_spool_fold.py::test_failure_supersede_rejects_duplicate_line_within_same_fold
test_spool_fold.py::test_n17_fragment_allocation_order_is_explicitly_sorted
test_spool_fold.py::test_deferred_append_resolves_cross_ledger_placeholder
test_spool_fold.py::test_p02_three_ledgers_with_cross_references_apply
```