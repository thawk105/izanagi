## 総括

指定された2ファイルだけを実装し、docs 編集・既存コード変更・commit は行っていません。

- [tools/codex_reasoning_ab.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py)
  - `build-snapshot` / `verify-snapshot`
  - `render-prompt`
  - `collect-run`
  - `score-run`
  - `aggregate`
  - `verify`
- [test_codex_reasoning_ab.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py)

既存 ledger は null `token_count.info` や task-complete 欠落を単独では拒否しません。新CLIはその token 定義と終了分類を import して再利用しつつ、T-181 run に限って ledger issues 全件、token/context/timestamp 欠落、effort/model/cwd、ID三者不一致を追加拒否します。effort 不明時の `max`・requested 値補完はありません。scorer は候補抽出のみで、primary 判定は行いません。

POS/NEG snapshot は実Git blob・実rolloutから構築して両方通過しました。POSの逆適用対象2ファイルは独立2経路で一致しています。prompt の置換数は POS=9、NEG=13 として source SHA・path-neutral identityを固定しました。

実走結果:

- `orchestrator/tests/test_codex_reasoning_ab.py`: **33 passed**
- 上記＋`test_codex_worker_ledger.py`＋`test_check_codex_output.py`＋meta-test `test_plain_runner_coverage.py`: **133 passed**
- plain runner: **33 passed**
- `python3 tools/check_codex_agents.py`: OK
- `python3 tools/check_docs.py`: 違反なし
- `git diff --check`: rc=0

親の全受入走は未実施であり、子の133件は代替しません。live 10 run、凍結manifest/artifact、盲検人手裁定も親の担当として未実施です。

静的な波及先は、親launcherの schedule schema（`pair_id`、`attempt`、argv SHA、inode、prelaunch size、launch envelope）、将来のtracked manifest consumer、既定の `orchestrator/tests` collectionです。共有fixtureや既存callerは変更していません。

既知の仕様不整合があります。NEGの歴史promptは `brief.md` と `adjudication-plan-v2.md` を要求しますが、裁定2.2のNEG untracked allowlistには両ファイルがありません。裁定どおり余分なファイルを追加しなかったため、現状のNEG live runは読取不能で即停止する可能性があります。親は実走前にこの2パスを追加するかprompt/snapshot契約を再裁定する必要があります。smoke用に作成した `/tmp` cloneはすべて削除済みで、生成物のみのため復旧対象はありません。