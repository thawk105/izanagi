H1〜H3を実装しましたが、Pegasus dispatch 基盤障害によりテスト未実走のため、段5契約上はすべて `partial` です。docs 編集・commit・qsub/qstat/qdel は行っていません。

## 総括

| 項目 | 状態 | 結果 |
|---|---|---|
| H1 | partial | write の ENOENT を、同一 path の外側成功かつ内側副作用なしの場合だけ `*_CONTAINED_BY_ABSENCE` と判定。EACCES等は従来の `*_CONTAINED`、EEXIST は非封じ込めのまま |
| H2 | partial | co-tenant を「自分以外の uid>=1000」に限定。旧 process 観測、除外した system/own UID・件数・PID、load 閾値を receipt に保持 |
| H3 | partial | 外側で対象機能自体が拒否された場合を `*_NODE_CAPABILITY_UNAVAILABLE` として `inconclusive` のまま区別 |
| 回帰 | 未検出 | 静的検査と既存 receipt 再判定では未検出。ただし pytest 未実走のため確定ではない |

編集ファイル:

- [t316_sandbox_backend_probe.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py)
- [test_t316_sandbox_probe.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/orchestrator/tests/test_t316_sandbox_probe.py)

検査結果:

- 対象 nodeid: `orchestrator/tests/test_t316_sandbox_probe.py`
- 指定の `--force-dispatch` を2回実行
- いずれも dispatch preflight `qstat -Q rc=1`、runner rc=16
- pytest: passed 0 / failed 0 / 未実走
- `py_compile`: 成功
- `git diff --check`: 成功

緩和防止テストとして、外側正例失敗、同一path不成立、内側副作用あり、uid>=1000の他ユーザ、load超過、EEXIST、S5 build副作用の各経路を追加しています。既存テストの反転・緩和・skip・削除はありません。

S5 build の `no-go` は維持されています。計測 ID `0:900383.nqsv` の既存 receipt を変更後 verdict へ再入力し、`S5_BUILD_SYSTEM_COMMAND_SIDE_EFFECT_OBSERVED`、S5=`no-go`、overall=`no-go` を確認しました。

残る限界は、旧 receipt に新しい同一-path証拠とuid分類がないため、H1/H2を遡及再判定できないことです。親によるテスト dispatch と再 probe が必要です。