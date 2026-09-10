## 総括

現行は「全 postrun 検査を通過した child rc=0」のみ受理し、非 0 は拒否していました。変更後は既存検査を一切外さず、これに「child 非 0、checker rc=0、status=`non-attributable-only`、receipt 全束縛一致」を追加受理します。checker の `green`、rc 1、rc 2、receipt 不整合、postrun 赤はすべて拒否します。

1. 実装した差分

- Δ1: 必須 `--log-file`、repo 外 preflight、stdout/stderr 捕獲、SHA-256 算出を実装。[dev_wave_wait.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t907-recovery/tools/dev_wave_wait.py:270)、[同 parser](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t907-recovery/tools/dev_wave_wait.py:382)、[同 preflight](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t907-recovery/tools/dev_wave_wait.py:780)
- Δ2: postrun 全緑後だけ checker を起動し、status・log hash・tested main/tip・schema・全 node classification・checker blob を照合。[dev_wave_wait.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t907-recovery/tools/dev_wave_wait.py:1326)、[同受入分岐](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t907-recovery/tools/dev_wave_wait.py:1645)
- Δ3: receipt v2、実 child rc、verdict、log/checker 束縛、red nodeids と整合検査を実装。[dev_wave_wait.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t907-recovery/tools/dev_wave_wait.py:1246)
- Δ4: land の v2 exact schema、verdict 別照合、tested main/checker blob 照合、結果 JSON への verdict/nodeids 伝播を実装。[dev_wave_land.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t907-recovery/tools/dev_wave_land.py:62)、[同 verifier](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t907-recovery/tools/dev_wave_land.py:518)、[同 LandResult](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t907-recovery/tools/dev_wave_land.py:132)
- 必須分岐、16 種の verdict 不整合、実 waiter→実 checker→実 land を追加。[wait tests](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t907-recovery/orchestrator/tests/test_dev_wave_wait.py:1418)、[land tests](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t907-recovery/orchestrator/tests/test_dev_wave_land.py:709)、[E2E](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t907-recovery/orchestrator/tests/test_dev_wave_land.py:915)

2. テスト

- 焦点走を `tools/run_tests.py` 経由で通常 2 回、`--force-dispatch` 付きで1回試行。
- すべて placement preflight の `qstat -Q` 障害で rc=16。pytest nodeid は収集・実行ともに0件です。
- collection meta-test も同じ rc=16で0件。
- `py_compile` 4ファイルと `git diff --check` は成功。
- したがって状態は「実装済み・未実走」であり、緑とは申告しません。

3. 所有外への波及可能性

- [docs/pegasus-runbook.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t907-recovery/docs/pegasus-runbook.md:808) の waiter 呼出例は `--log-file` 追加が必要です。docs は親所有のため未編集です。
- v1 receipt は land で拒否されます。稼働中 wave は新 waiter による再受入が必要です。
- `LandResult.as_json()` consumer は新しい2キーを受け取ります。repo 内の直接 consumer は対象テスト以外に見つかりませんでした。
- 共有 fixture `_FakeEffects`、`_Repo._acceptance_receipt`、CLI fixture はv2へ更新済みです。
- `test_check_docs.py`、`tools/check_docs.py` は親による runbook 更新後の波及確認候補です。

4. 裁定書外で判断した点

- 新しい外部 CLI は増やさず、checker receipt を `<receipt-file>.acceptance-red-check.json`、probe root を log の親 directory としました。
- その preflight stage を `acceptance-red-check-preflight` としました。
- `acceptance_red_nodeids` は内部では tuple、JSONでは listとして出力します。
- いずれも受理集合は広げません。

5. 残件・赤の内訳

- 観測済みテスト赤はありません。ただしテスト本体が0件のため未検証です。
- 未完は焦点走と collection meta-test。阻害要因は一貫して `qstat -Q preflight rc=1`／wrapper rc=16です。
- 変更は指定された4ファイルだけです。docs編集・add・commit・stash・checkoutは行っていません。