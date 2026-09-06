4 件すべて修正し、指定の自走 harness は全 31 node が通過しました。

| 所見 | 判定 | 対応 |
|---|---|---|
| A-1 | closed | 検査済み kwargs を 1 段 snapshot。`Mapping` は独立 `dict`、`list` / `tuple` は `tuple`、その他は identity を維持しました。[launcher](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-c-fix3/orchestrator/campaign/s8b_floor_attempt_launcher.py:475) |
| A-3 | closed | protocol / receipt を downstream-valid な callable `dict` subclass に変更し、callable gate 固有の拒否 message を固定しました。gate 無効化時に両入力が後続検査を通ることも実測済みです。 |
| R-1 | closed | private sink の 3 record を、実体同形 6 key の値まで含む exact tuple 比較へ戻しました。[launcher tests](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-c-fix3/orchestrator/tests/test_s8b_floor_attempt_launcher.py:812) |
| R-2 | closed | observed 申告を non-null digest / primary value にし、terminal / observation 未呼出しと deferred reader の未封印を検査しました。 |

静的確認では、[official perf guard](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-c-fix3/orchestrator/tests/test_official_perf_closure.py:297) の 2 条件式は逐語不変です。[spawn-site pin](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-c-fix3/orchestrator/tests/test_ccbench_spawn_sites.py:212) も `_owned_post_probe` の `subprocess.run` 1 箇所のままです。adapter / core / profile / campaign / calibrator / docs は変更していません。M12 node も変更していません。

追加 wrapper は Pegasus の `qstat -Q` preflight が rc=1 となり、子未起動・dispatch rc=16 でした。これはテスト失敗ではありません。生成された dispatch scratch は削除済みで再生成可能です。commit は作成していません。

## 総括

- A-1 closed / A-3 closed / R-1 closed / R-2 closed。partial 0、regressed 0。
- fix3 差分: production +13 / -1、test +59 / -12。
- test は新設 0、変更 5 pytest node、4 test function。
- `test_s8b_floor_attempt_launcher.py::*`: 31 passed in 7.07s。
- pytest wrapper: Pegasus dispatch infrastructure failure、test child 未起動。