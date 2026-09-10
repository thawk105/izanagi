3 件ともテストへ反映しました。編集対象は [test_dev_wave_land.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/orchestrator/tests/test_dev_wave_land.py) だけです。production・docs は変更せず、commit・staging 操作も行っていません。

| 所見 ID | closed・partial・regressed | 根拠 (file:line) |
|---|---|---|
| 訂正 1 / M2 | partial | 受領証 digest を main に固定し、tip digest と異なることも明示。[test_dev_wave_land.py:1523](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/orchestrator/tests/test_dev_wave_land.py:1523) |
| 訂正 2 / M5 | partial | `locked_main != tested_main`、locked main の変更ファイルは runner だけ、tested pair は同一 runner。lookup は `[tested_tip, tested_main]`、着地成功を期待。[test_dev_wave_land.py:1568](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/orchestrator/tests/test_dev_wave_land.py:1568) |
| 訂正 3 / 複合故障 | partial | runner divergence と checker lookup rc=128 を同時に仕込み、divergence が先行して `retryable_same_request=False` となることを固定。[test_dev_wave_land.py:1646](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/orchestrator/tests/test_dev_wave_land.py:1646) |

M2 の静的確認結果は「殺せる」です。equality 比較を `verdict == "non-attributable-only"` 内へ戻すと、child-green は equality を迂回しますが、受領証 digest は main blob と一致するため digest 検査も通ります。結果として land が受理し、拒否を期待するテストが赤になります。[dev_wave_land.py:1084](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/tools/dev_wave_land.py:1084)

静的な波及確認:

- production caller は `land()` 内の `_verify_acceptance_receipt` 1 箇所だけです。[dev_wave_land.py:5035](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/tools/dev_wave_land.py:5035)
- `_Repo.request` は AST 上 186 consumer、うち明示 revision は 6、既定利用は 180 です。既定の tip digest は変更していません。[test_dev_wave_land.py:354](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1283-runner-main-blob/orchestrator/tests/test_dev_wave_land.py:354)
- child-green、non-attributable、already-landed、forward-main、fold recovery、bootstrap の production 経路には変更なしです。
- 新規 nodeid が 1 件増えるため、pytest 収集・duration 台帳 consumer には追加分の波及可能性があります。

検査は `git diff --check` と全ファイル AST parse が成功しました。以下の 3 nodeid は `tools/run_tests.py` 経由で 2 回投入しましたが、いずれも `qstat -Q` preflight rc=1、runner rc=16、`child_started=false` で、テスト本体は実走していません。

- `test_land_rejects_child_green_runner_blob_divergence`
- `test_land_accepts_child_green_matching_main_and_tip_runner_blobs`
- `test_land_runner_divergence_precedes_checker_lookup_process_failure`

## 総括

- 裁定訂正 1〜3 はテストコードへ実装済みです。
- M2 と M5 を殺す条件は静的に成立しています。
- fixture の既定 tip digest は維持しています。
- production・docs は未変更、commit・staging も未実施です。
- Pegasus dispatch 障害のため実装済み・未実走であり、緑とは報告しません。