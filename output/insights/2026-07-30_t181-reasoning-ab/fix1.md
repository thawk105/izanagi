## 総括

段6の must-fix をすべて閉じ、指定された2ファイルだけを変更しました。docs 編集・commit・既存 ledger/checker/run_tests 変更はありません。

- [codex_reasoning_ab.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:493)
  - Git objects/refs/reflog/remote/alternates/packed-refs の閉包
  - 訂正版 POS/NEG allowlist と prompt path 完全一致
  - 独立 golden 2経路
  - prelaunch launch receipt、arm同一性、arm-neutral path
  - raw artifactからの receipt/score replay
  - session行集合一致、turn graph、正token、process wall-clock
  - logical slot/全attempt/retry親子/上限検査
  - label-masked packet、verdict freeze、条件付きmapping公開
  - primary・新規finding・全attempt資源・決定rowのT-181台帳
- [test_codex_reasoning_ab.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:398)
  - stale timestamp、token 0件、all-zero usage、abort、turn不一致、attempt=4、NEG allowlist、verdict row-swap、否定scope、曖昧決定、tilde fence、Git answer object再注入を独立固定

実走結果:

- `orchestrator/tests/test_codex_reasoning_ab.py`: **27 passed**
- `test_codex_worker_ledger.py`、`test_check_codex_output.py`、meta-test `test_plain_runner_coverage.py`: **100 passed**
- `python3 tools/check_codex_agents.py`: OK
- `python3 tools/check_docs.py`: 違反なし
- `py_compile`、両ファイルの whitespace check: rc=0相当

実装must-fixの未達はありません。親担当の live 10 run、変異matrix、既定受入全走、記録・docs・commitは未実施であり、子の127件は代替しません。scope外のheld-out正例、非劣性設計、backend identity、runtime silent-miss検出も未実装のままです。

波及可能性として、親launcherはschema v2、JSON形式の`.done`、`create-launch-receipt`、必須`--sessions-root`、`attempts_root`、schedule/packet/verdict/judgment artifactへ追随が必要です。旧post-hoc freshness CLIは廃止したため既存callerは互換でありません。共有fixtureは変更しておらず、新fixtureは当該テスト内だけです。consumerは将来のtracked manifest、親launcher、既定の`orchestrator/tests`収集面です。作業用 `/tmp` snapshotは生成物だけを削除済みで、復旧対象はありません。