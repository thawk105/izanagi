指定テストの `match` を厳格化しました。[test_t139_blobref_git_trust.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-s2/orchestrator/tests/test_t139_blobref_git_trust.py:133) のみ変更しています。

| nodeid | 変更前 | 変更後 |
|---|---|---|
| `::test_missing_fixed_git_path_has_identifiable_resolution_error` | `git executable.*解決できない` | `^git executable を解決できない$` |
| `::test_external_alternate_object_store_is_rejected` | `alternates` | `^alternates を持つ repository は受理しない$` |
| `::test_http_alternate_object_store_is_rejected` | `alternates` | `^alternates を持つ repository は受理しない$` |
| `::test_promisor_remote_is_rejected` | `promisor remote` | `^promisor remote を持つ repository は受理しない$` |
| `::test_promisor_pack_marker_is_rejected` | `promisor object` | `^promisor object を持つ repository は受理しない$` |
| `::test_partial_clone_configuration_is_rejected` | `partial clone` | `^partial clone repository は受理しない$` |

点検結果：

- 上記候補はすべて、隣接する「検査／解決できない」例外まで拾いうるため厳格化しました。
- promisor remote の whitespace／boolean-alias 負例は、既に `promisor remote を持つ repository` まで指定しており、`promisor remote 設定...` 系には一致しないため変更していません。
- digest-binding 側の `ref.sha256`／`ref.commit`／`ref.path` は、それぞれ固有の型境界を指しており、同語を共有する隣接例外による mask がないため変更していません。
- production の [blobref.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-s2/orchestrator/preregistration/blobref.py) は1行も変更していません。docs、output、commit も変更・作成していません。

検査は AST parse、拒否 message／検査失敗 message の非一致確認 5/5、`git diff --check` が成功しました。  
`python3 tools/run_tests.py orchestrator/tests/test_t139_blobref_git_trust.py -q` は `qstat -Q preflight rc=1`、runner `rc=16` でテスト開始前に停止したため、**実装済み・未実走**です。

## 総括

- MA4 を mask していた部分一致を、拒否理由の完全一致へ変更。
- 同型の緩い照合を5 nodeid追加で厳格化。
- production／docs／output は無変更、commit なし。
- runner infrastructure failure のため pytest は未実走。