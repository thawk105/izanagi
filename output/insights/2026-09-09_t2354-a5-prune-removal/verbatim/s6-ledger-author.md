## 総括

- producer により指定 2 node を台帳へ追加しました。
- 指定 command は `rc=0`、`added=2`、`skipped_existing=7`、除外 0 でした。
- 変更ファイルは `orchestrator/tests/acceptance_duration_ledger.json` のみです。
- 全検算項目を満たしたため、変更は維持しています。

## 実行した command と rc

- 射影資料の確認:
  - `sed -n '1,240p' /home/SFC/tanab/.claude/jobs/1314c3cf/tmp/wave-t2354/a5-contract.junit.xml` — `rc=0`
  - producer 全文の `sed` 分割確認 3 回 — すべて `rc=0`
- 指定 producer command:
  - `python3 tools/update_acceptance_duration_ledger.py --add-only /home/SFC/tanab/.claude/jobs/1314c3cf/tmp/wave-t2354/a5-contract.junit.xml` — `rc=0`
- `git diff -- orchestrator/tests/acceptance_duration_ledger.json` — `rc=0`
- HEAD/current の件数・対象値を確認した `jq` 2 回 — いずれも `rc=0`
- 追加 2 行と count 更新を逆変換して HEAD と比較した `cmp -s` — `rc=0`
- `git status --short` — `rc=0`

## diff の検算

1. **追加 entry は指定 2 件だけ**
   - `git diff` で duration entry の追加が 2 件、削除・書き換えが 0 件であることを確認。
   - producer 出力も `added=2`、`skipped_existing=7`。

2. **既存 entry の値・順序・bytes**
   - current から追加 2 行を除き、`nodeid_count` のみ旧値へ戻した出力を HEAD と byte-exact 比較。
   - `cmp -s` は `rc=0`。既存 duration entry の削除・書き換えは **0 件**。

3. **`nodeid_count`**
   - HEAD: `22155`（mapping 実件数も `22155`）。
   - current: `22157`（mapping 実件数も `22157`）。
   - 既存件数 + 2 と一致。

4. **追加値**
   - cleanup failure: JUnit `0.122` 秒 → producer の二桁丸めで `0.12` 秒。
   - missing sibling: JUnit `0.127` 秒 → producer の二桁丸めで `0.13` 秒。
   - `0.0` placeholder は **0 件**。

## 未実走・未確認

- テストは再実走していません。親が提供した JUnit XML（9 node、failure/error/skipped 各 0）の内容のみ確認しました。
- `git add`、`git commit`、docs/checker 類は実行していません。