erratum-5 の実装を完了しました。

| 項目 | 状態 |
|---|---|
| signal CPU の率超過のみ `COMPETITOR`・INVALID・後続停止 | closed |
| 非 signal CPU の率超過を `ATTRIBUTION_UNRESOLVED`・VALID 継続 | closed |
| CPU 集合、tick、率、duration、control 帯外交差の記録 | closed |
| 同一窓で両方発生時の `COMPETITOR` 優先 | closed |
| partial / regressed | なし |

変更ファイル:

- [t419_probe_causality.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/tools/pegasus/probes/t419_probe_causality.py:2250): +128 / -7
- [test_t419_probe_causality.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-rerun/orchestrator/tests/test_t419_probe_causality.py:1045): +120 / -1
- 既存テスト node の期待値変更: 0件

追加したテスト node:

- `test_signal_cpu_rate_exceedance_is_competitor_invalid_and_stops_later_arms`
- `test_non_signal_cpu_rate_exceedance_is_unresolved_valid_and_records_intersection`
- `test_signal_and_non_signal_rate_exceedance_prefers_competitor`

確認結果:

- `python3.10 -m py_compile ...`: rc=0
- 純計算 `--self-test`: rc=0
- pytest: 0件（Pegasus ログインノードのため未実行）
- `git diff --check`: rc=0
- 445 primary read は `30 + 240 + 30 + 50 + 80 + 15 = 445` のままです。
- 0.95 / 0.05 / 46、25.0 tick/s、3 tick、canonical band、arm 順序、α巡回、hash 束縛は変更していません。
- 新しい定数はありません。caller は対象実装内と同テスト内のみで、共有 fixture は省略可能引数の追加だけです。結果 consumer への変更は additive field の追加です。

## 総括

- (a) 許可された2ファイルだけを変更し、signal CPU 限定 abort と非 signal 診断記録を実装しました。
- (a) docs・PBS・output・commit には触れていません。
- (b) 追加3 node は未実走のため、残リスクは計算ノード上の pytest 結果です。
- (c) 親は計算ノードで対象テストを実行し、実機結果の CPU集合・率・duration・control帯外交差を確認してください。