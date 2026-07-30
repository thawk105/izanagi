単位 A の fix 実装を完了しました。編集は指定された [launcher](/home/SFC/tanab/github/izanagi/.claude/worktrees/t180-author-a/tools/codex_worker_launch.py) と [tests](/home/SFC/tanab/github/izanagi/.claude/worktrees/t180-author-a/orchestrator/tests/test_codex_worker_launch.py) のみで、commit は作成していません。

主な変更は、usage peak latch、null event の不完全扱い、sealed artifact 再計算、外部期待値、rollout 伸長表示、`/proc` unknown、launcher-process wall clock、receipt create-only、repo/base/header 束縛、spawn 後 cleanup、逐次 fake、manifest 早期追記です。

| ID | 状態 | 根拠 |
|---|---|---|
| A-1 | closed | CLI-reported peak を latch。巻き戻しを inconsistent として拒否。M19 負例追加 |
| A-2 | closed | `info=null` も model call に計数し、metering incomplete として拒否 |
| A-3 | closed | sealed usage/output を再計算。`--expect-prompt-sha256`、全 `--expect-max-*` 等を追加。自己申告 limits を明示 |
| A-4 | closed | seal の rollout hash/bytes を保持し、checker が `rollout_grew_since_seal` を出力 |
| A-5 | closed | `/proc` scan・個別読取・PID identity の unknown を fail-closed 化 |
| A-6 | partial | 単位 B 所有の ledger 一意性。未編集 |
| A-7 | closed | launcher 起動時から計測し、preflight、公開、self-check、receipt write/fsync staging を判定へ包含 |
| A-8 | closed | temp write後の `os.link()` による atomic create-only。並行 call-site 負例あり |
| A-9 | closed | cwd包含、commit実在、manifest header 3 field の再照合 |
| A-10 | partial | 裁定どおり scope 外の manifest seal ceremony。変更なし |
| A-11 | closed | 到達不能分岐を削除し、truth-table 検査へ集約 |
| B-1 | closed | header を spawn 前照合。spawn 後例外で group cleanup と launcher-error receipt を生成 |
| B-2 | closed | hard-cap 表現を除去。`wall_clock_scope="launcher_process"` と脱出子非包含を明記 |
| B-3 | closed | 最終 drain・公開・self-check 後に再評価してから receipt を公開 |
| B-4 | closed | M3/M8/M9/M10/M11を再照準し、M17/M18/M19負例を追加。変異本走は親工程 |
| B-5 | closed | fake を逐次 append 化し、実CLIの stdout event と cache-write field を再現 |
| B-6 | closed | missing/incomplete/inconsistent または全 limit trigger で overshoot=true。checkerも再導出 |
| B-7 | closed | identity未取得を unknown とし、termination verified を恒真化しない |
| B-8 | closed | checker が `codex_version` を再取得しない射程を docstring に明記 |
| F-P1 | closed | session三者相関成立時、attempt完了前に manifestへ追記。実行中確認テストあり |

波及可能性:

- 単位 B の `codex_worker_ledger.py` は manifest schema 自体には影響しませんが、A-1/A-6の統合結果は親の単位 B 統合後に再確認が必要です。
- `check-receipt` は JSON診断をstdoutへ出すようになり、旧pre-fix receiptは追加されたclosed fieldsを持たないため拒否されます。リポジトリ内に別callerは静的検索で見つかりませんでした。
- 将来のDW-O01/T-184 callerは、実在するbase commit、repo配下cwd、および必要に応じた外部期待値を渡す必要があります。
- 共有fixture・所有外consumer testの変更はありません。

## 総括

- closed 18件、partial 2件、regressed 0件。
- 実走範囲: `orchestrator/tests/test_codex_worker_launch.py` 全52 nodeid。
- 指定コマンド結果: `52 passed in 21.24s`。
- `check_codex_agents.py`: OK、`check_docs.py`: 違反なし、`git diff --check`: OK。
- 未了は単位B所有のA-6と、裁定scope外のA-10のみです。