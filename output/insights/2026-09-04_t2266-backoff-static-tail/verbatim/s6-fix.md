## 所見 1 の直し

[T-2266 専用 hash gate](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2266-fix1/orchestrator/campaign/backoff_extended_sweep.py:227)を追加し、`none`、`adaptive`、固定 6 点の trace-disabled binary すべてに異なる SHA-256 を要求しました。既存 `_require_distinct_static_binary_hashes` の挙動は変更していません。

## 所見 2 の直し

[_T2266RepCapture](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2266-fix1/orchestrator/campaign/backoff_extended_sweep.py:520)で以下を fail-closed にしました。

- abort parser 呼出数と throughput rep 数の完全一致
- `rep_observations` の件数、`rep_index` 順序、throughput 対応
- 切り詰めを廃止し、全 rep を一対一で保存

WAL TPS との恒真な再比較は削除しました。WAL round の選択は従来どおり `run_cmd` と全 throughput 配列で行います。

## 所見 3 の直し

数値 point の `certified` を `false` に変更し、次を JSON の全体・各 point、および `.dat` provenance に記録しました。

- `correctness_verified: true`
- `performance_certified: false`
- `claim_scope: descriptive_backoff_shape_only`
- `source_measurement: trace_disabled`

correctness verify の通過要求は維持しています。

## 所見 4 の直し

[全 rep 統合テスト](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2266-fix1/orchestrator/tests/test_backoff_extended_sweep.py:346)を、実 `measure_point`、実 abort parser、実 `_T2266RepCapture`、immutable WAL、実 replay、実 `_load_t2266_report_points`、writer を通る形へ変更しました。

外部 process 出力と campaign の filesystem locator だけを fixture 化し、捕捉・parser・certified-view 検査・WAL consumer は stub していません。

変異確認後、両変異は復元済みです。

- 代表 abort 率の複製: rep 配列比較で `AssertionError`、exit 1
- 件数 gate の除去: `DID NOT RAISE RuntimeError`、exit 1

## monkeypatch の扱い

本番の実行時差し替えは残しました。既存 `rep_observations` seam は rep identity と throughput を運びますが `abort_rate` を含まないためです。

現在はこの seam で rep 順序を検証し、abort 率だけを parser 捕捉から結合します。差し替えは context manager 内に限定し、成功・例外の双方で `finally` により復元します。

## 走らせた検査

- `git diff --check`、対象 2 ファイルの `py_compile`: 成功
- 変更後および変異復元後の 3 テスト本文直接診断: 成功
- 上記 2 変異のテスト本文直接診断: それぞれ期待どおり赤
- 次の正規 nodeid 実走は rc=16、`child_started=false` のため未実走:
  - `test_t2266_none_and_adaptive_must_have_distinct_perf_binaries`
  - `test_t2266_real_rep_capture_flows_through_wal_consumer_for_every_rep`
  - `test_t2266_rep_capture_rejects_extra_abort_parser_call`
- `orchestrator/tests/test_backoff_extended_sweep.py` 全体も同じ rc=16 で未実走
- 原因は `qstat -Q` の UID 認証エラーです。したがって pytest は「実装済み・未実走」であり、緑とは申告しません。

## 受理集合の変化

- T-2266 は exact 8 genome の全 trace-disabled binary が相互に distinct な場合だけ受理します。
- abort parser 呼出数、runner observation 数、rep 順序、throughput 対応の不一致を新たに拒否します。
- trace-disabled 性能値を certified point としては受理しなくなりました。
- 既存 31 点格子、`EXTENDED_SWEEP_US`、既存 static hash gate の受理・拒否挙動は不変です。
- 恒真検査の削除による受理集合変更はありません。

## 波及可能性

- `_prebuild_backoff_binaries` の既存 caller は新引数の既定値が `False` のため従来挙動です。
- T-2266 の JSON consumer は `certified: false` と追加された claim metadata を扱う必要があります。
- `.dat` の 5 列構造は不変で、header metadata のみ増えます。
- `campaign_pipeline.measure_point` への差し替えは T-2266 campaign の context 内だけに影響します。
- 既存 B-10 report、31 点 plotting、共有 runner／pipeline は変更していません。
- stage 5 由来の Pegasus shell 2 ファイルは作業ツリーに残っていますが、この fix では編集していません。

## 総括

- T-2266 の全 8 binary に distinct hash を要求しました。
- abort 率と throughput rep の完全一致と順序を強制しました。
- 恒真だった WAL TPS 再比較を削除しました。
- correctness verify と性能認証を成果物上で分離しました。
- 全 rep テストを producer から WAL consumer、writer まで通す形にしました。
- 指定された 2 変異はいずれも赤となり、復元済みです。
- 正規 pytest は Pegasus 認証障害で子が起動せず、未実走です。
- 許可された 2 ファイルだけを編集し、commit、add、stash、branch 操作は行っていません。