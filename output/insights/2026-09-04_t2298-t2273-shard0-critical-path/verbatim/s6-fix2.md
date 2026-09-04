## 所見対応表

| 所見 | closed | partial | regressed | 根拠 |
|---|---:|---:|---:|---|
| MF-2A | ✓ |  |  | receiver に関係なく `write_bytes` / `write_text` / `open` / `replace` / `rename` を禁止し、helper 呼出しを exactly 1 に固定 |
| MF-2B | ✓ |  |  | `write → flush → fsync → replace`、同一 temp fd、fsync 時点の payload 完成を検査 |
| 退行 |  |  | なし | 実装本体・fixture・17 consumer は不変 |

## 変更一覧

変更は [test_p3_b4_raw_record_producer.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py) の検査 2 本だけです。

- [test_certified_evidence_seed_publishes_metadata_only_through_atomic_helper_ast:1625](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1625)
  - receiver/path 推論を使わない禁止呼出し検査へ変更。
  - `_write_certified_evidence_metadata(...)` は exactly 1 回かつ正規 metadata path。
- [test_certified_evidence_metadata_is_fsynced_and_atomically_replaced:1681](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1681)
  - stream wrapper で write/flush を記録。
  - 操作列、同一 fd、write payload、fsync 時点の bytes、replace source/target を検査。

保護対象は修正前後の AST 正規化ハッシュを比較しました。

- 実装本体＋fixture 2 本: `f7c2cf07…f6dae7` で一致
- 17 consumer: `c224a3d7…e8c2b8` で一致
- 編集 hunk も上記 2 検査内だけです。

## 変異 i / j と殺す検査

| 変異 | killer | 単一理由 |
|---|---|---|
| i: helper 前に `shared.joinpath("evidence.json").write_bytes(...)` | seed AST 検査 | helper 件数は 1 のまま、receiver 非依存の禁止 `write_bytes` が exactly 1 件となる |
| j: `os.fsync` を `stream.write` 前へ移動 | atomic replace 検査 | 観測列が `fsync → write → flush → replace` となり、要求順序に違反する |

変異 j では、fsync 時点の snapshot が空 bytes になることも確認しました。

## 実走

`tools/run_tests.py` 経由で対象 2 nodeid を実行しましたが、Pegasus dispatch の `qstat -Q` preflight が `rc=1`、runner は `rc=16`、`child_started=false` でした。

したがって、検査修正は実装済み・pytest 未実走です。

代替自己検証は成功しています。

- AST parse／MF-2A 条件: pass
- atomic 検査の正常系を分離実行: pass
- 変異 i: kill
- 変異 j: kill
- U+0300〜U+036F: 0 件

## 総括

MF-2A、MF-2B はともに closed。実装本体と 17 consumer に変更はありません。残るのは実行基盤復旧後の pytest 実走だけです。