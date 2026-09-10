G1 を指定テストファイルだけに追加しました。production、docs、git index、commit には触れていません。

### 1. G1 追加テスト

追加箇所: [test_pegasus_dispatch_compute.py:1369](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/orchestrator/tests/test_pegasus_dispatch_compute.py:1369)

`test_overall_grace_allows_done_at_observed_run_deadline`

時刻展開:

- `t=0`: `QUE`。初期 deadline は `0 + 2 + 1 = 3`
- `t=1`: trusted `RUN`。baseline は deadline を `1 + 2 + 1 = 4` へ張り直す
- `t=2`: `UNRECOGNIZED`
- `t=3`: `UNRECOGNIZED`。baseline は `3 < 4` なので継続
- `t=4`: `DONE`。END 判定が deadline 判定より先なので `rc == 0`、qdel なし
- grace 脱落変異では張り直しが `1 + 2 = 3` となり、`t=3` で `overall-timeout`、qdel、`rc == 16`

assertion は `rc`、qdel 不在、`overall-timeout` 不在だけで、履歴全体や診断時刻を固定していません。

### 2. G2 完全な期待赤集合

G1 後は 66 test 関数、焦点再レビューの 89 node に 1 node を加えた計 90 node です。以下が静的追跡上の全赤集合で、記載外の node は赤になりません。

| 変異 | 区分 | 赤になる完全 nodeid | 赤になる理由 |
|---|---|---|---|
| 1. `submitted_at` 起点 | 受理集合 | `orchestrator/tests/test_pegasus_dispatch_compute.py::test_queue_wait_does_not_consume_observed_run_budget` | `t=2` RUNでも deadline が3のままになり、`t=3` RUNで timeout。`rc == 0` とqdel不在が赤 |
| 1 | 受理集合 | `orchestrator/tests/test_pegasus_dispatch_compute.py::test_overall_grace_allows_done_at_observed_run_deadline` | deadline が3のままになり、`t=3` UNKNOWNで timeout。rc・qdel・outcome が反転 |
| 1 | 診断のみ | `orchestrator/tests/test_pegasus_dispatch_compute.py::test_post_run_unknown_state_uses_first_observation_deadline` | rc=16・qdel・overall-timeout は同じだが、最終 `elapsed_s == 4.0` が3.0になって赤 |
| 1 | 診断のみ | `orchestrator/tests/test_pegasus_dispatch_compute.py::test_nonzero_qstat_run_stdout_does_not_restart_deadline` | trusted 側の rc・qdel・outcome は同じだが、最終 `elapsed_s == 4.0` が3.0になって赤 |
| 1 | 受理集合 | `orchestrator/tests/test_pegasus_dispatch_compute.py::test_trusted_run_after_nonzero_run_stdout_restarts_deadline` | `t=2` trusted RUNで延長できず、`t=3` RUNで timeout。成功期待とqdel不在が赤 |
| 2. grace 項脱落 | 受理集合 | `orchestrator/tests/test_pegasus_dispatch_compute.py::test_overall_grace_allows_done_at_observed_run_deadline` | deadline が4から3になり、`t=3` UNKNOWNで timeout。rc・qdel・outcome が反転 |
| 2 | 診断のみ | `orchestrator/tests/test_pegasus_dispatch_compute.py::test_post_run_unknown_state_uses_first_observation_deadline` | timeout が `t=4` から `t=3` へ早まり、`elapsed_s == 4.0` のみ赤 |
| 2 | 診断のみ | `orchestrator/tests/test_pegasus_dispatch_compute.py::test_nonzero_qstat_run_stdout_does_not_restart_deadline` | trusted 側の timeout が `t=4` から `t=3` へ早まり、`elapsed_s == 4.0` のみ赤 |
| 3. RUN ごとに張り直す | 受理集合 | `orchestrator/tests/test_pegasus_dispatch_compute.py::test_overall_walltime_plus_grace_bound_qdels_running_job` | deadline が `1→2→3` と延び、`t=3` ENDで成功。infra・qdel・overall-timeout期待が赤 |
| 3 | 受理集合 | `orchestrator/tests/test_pegasus_dispatch_compute.py::test_post_run_unknown_state_uses_first_observation_deadline` | 二度目のRUNで deadline が4から5になり、`t=5` ENDで成功。infra・qdel・outcome期待が赤 |
| 4. rc gate 恒真化 | 受理集合 | `orchestrator/tests/test_pegasus_dispatch_compute.py::test_nonzero_qstat_run_stdout_does_not_restart_deadline` | untrusted RUNが `t=1` に deadline を4へ延長し、`t=4` ENDで成功。untrusted側のinfra・qdel・outcome期待が赤 |
| 5. latch を `run_seen` へ戻す | 受理集合 | `orchestrator/tests/test_pegasus_dispatch_compute.py::test_trusted_run_after_nonzero_run_stdout_restarts_deadline` | `t=1` の偽RUNが latch を潰し、`t=2` trusted RUNで張り直せず、`t=3` timeout。成功期待が赤 |
| 6. deadline 判定を `if False` | 受理集合 | `orchestrator/tests/test_pegasus_dispatch_compute.py::test_overall_walltime_plus_grace_bound_qdels_running_job` | `t=1` timeoutせず、`t=3` ENDで成功。infra・qdel・outcome期待が赤 |
| 6 | 受理集合 | `orchestrator/tests/test_pegasus_dispatch_compute.py::test_post_run_unknown_state_uses_first_observation_deadline` | `t=4` timeoutせず、`t=5` ENDで成功。infra・qdel・outcome期待が赤 |
| 6 | 受理集合 | `orchestrator/tests/test_pegasus_dispatch_compute.py::test_nonzero_qstat_run_stdout_does_not_restart_deadline` | trusted側は `t=5`、untrusted側は `t=4` のENDまで到達して成功。両infra期待などが赤 |
| 6 | 受理集合 | `orchestrator/tests/test_pegasus_dispatch_compute.py::test_unknown_scheduler_state_remains_bounded_by_overall_timeout` | `t=1` timeoutせず、有限fixtureの `t=4` ENDで成功。infra・overall-timeout期待が赤 |

`hang_risk`:

- 変異3: `true`。実 scheduler がRUNを返し続けると、毎poll deadlineを未来へ送って上界を失います。
- 変異6: `true`。RUN観測後に終端しない実ジョブではoverall上界を失います。
- このテストファイルの fake scheduler は状態列消費後にDONEを返すため、静的にはいずれもhangしません。
- 変異1、2、4、5は `hang_risk=false` です。

### 3. 既存テストへの影響

G1は独立したテスト関数の追加だけで、既存fixture・期待値・skip・実行順を変更していません。現在差分中の期限関連テストも静的には次の期待を維持します。

- overall-bound: 初回RUNが`t=0`なので deadline は従来どおり`t=1`
- queue-wait正例: `t=2` RUNからdeadline=`5`、`t=4` DONEで成功
- post-RUN上界: `t=1` RUNからdeadline=`4`、`t=4` UNKNOWNでtimeout
- trusted/untrusted比較: trustedはdeadline=`4`、untrustedは初期deadline=`3`
- latch回帰: 偽RUN後の`t=2` trusted RUNからdeadline=`5`、`t=4` DONEで成功
- UNKNOWN上界: RUN分岐へ入らず、初期deadlineがそのまま有効
- 既存qstat-errorテストはERROR stdoutの既定が空であり、偽RUNとしてlatchしません

これは静的根拠であり、実測の緑は主張しません。

### 4. 検査

実行した静的検査:

- `git diff --check`
- 対象テストファイルのAST構文解析
- `git status --short`、`git diff --name-only`
- 全テスト関数と期限関連経路の静的照合

実行していない検査:

- pytestの全走・部分走
- `tools/run_tests.py`
- mutation harnessおよび変異実走
- `qsub`、`qdel`、`qstat`
- `check_codex_agents.py`、`check_docs.py`、provenance履歴監査

## 総括

G1の正例を追加し、grace脱落を診断値差ではなくrc・qdel・outcomeの受理集合差にしました。  
G1後90 nodeに対する6変異の完全な期待赤集合を、受理集合差と診断値差に分けて確定しました。  
ログインノード制約に従って動的検査とPBS操作は実行せず、production・docs・commitには触れていません。