段 6 fix を実装し、指定 pytest と現行 repo 監査まで通過しました。commit・`git add`・`docs/` 配下の編集は行っていません。

## 総括

所見別の状態：

| 所見 | 状態 | 理由 |
|---|---|---|
| FIX-1 | closed | merge commit を combined diff `-c`、root・単一親を従来の `-m` で処理。main 側を取り込んだ到達不能 merge の負例も通過 |
| A-9 / B-5 | closed | 入口を「rc=0 のみ削除へ進む、rc≠0 は停止して §5 報告」に変更 |
| A-10 | closed | `UnicodeError` を rc=2 に分離し、専用 control が通過 |
| A-5 | closed（採用範囲） | 出力を「要確認の到達不能変更」に変更。`--help` と0件出力で検出対象外を明示 |
| B-3 / FIX-4 | partial | M1′・M5・M6へ再照準し、M1〜M6の `old` は各1回、expected nodeも各1件。変異 matrix 本走は親の担当として未実走 |
| A-2 / B-1 | not-fixed | blob/patch同値性への再定式化は裁定どおりscope外。既存変更・削除・同名別内容・gitlink更新を検出しない旨は明示済み |
| B-2 | not-fixed | 到達不能graphのfrontier/net delta評価はscope外 |
| A-4 | not-fixed | fold除外の証明ベース化はscope外 |
| A-6 | not-fixed | ref snapshot原子性はscope外 |
| A-11 | not-fixed | 削除・prune・gc前の強制配線はscope外 |
| A-3 / B-4 | closed | 誤ったpath履歴抑止案を親が撤回済み |
| A-1 / A-7 / B-0 / B-6 / B-7 | closed | 親裁定で欠陥主張をrefuted済み |
| A-8 | closed | 親の実測でcertified peak 181.8 MiB、`local-ok`分類済み |

主な変更：

- [audit_dangling_commits.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cleanup-submodule-recurrence/tools/audit_dangling_commits.py)
- [test_audit_dangling_commits.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cleanup-submodule-recurrence/orchestrator/tests/test_audit_dangling_commits.py)
- [cleanup-branches.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cleanup-submodule-recurrence/.claude/commands/cleanup-branches.md)
- [mutation-spec.json](/work/1/SFC/tanab/dev-wave-jobs/cleanup-submodule-recurrence/mutation-spec.json)

検査結果：

- 正規dispatch：両pytestとも `qstat -Q preflight rc=1`、wrapper rc=16、実行0件。
- task固有の許可に従った直接実行：
  - `test_audit_dangling_commits.py`: **8 passed**
    - positive control
    - reachable main負例
    - help限界明示
    - decode rc=2
    - main同名path負例
    - live branch同名path負例
    - merge combined負例
    - fold除外負例
  - `test_check_docs.py`: **273 passed**
- `python3 tools/check_docs.py`: rc=0、違反0件。
- `python3 tools/audit_dangling_commits.py`: rc=0、要確認0件。
- `python3 -m py_compile`：新規2ファイル、rc=0。
- `python3 tools/check_codex_agents.py`: rc=0。
- `git diff --check`: rc=0。
- M01〜M06：各 `old_count=1`。
- whole-file fixtureと実ファイル：3982 bytesでbyte一致。
- SHA-256：`0f202920c97ec97d7625c343d377686cc6511b2b78a01cb502077123fd49429a`。

入口の最終byte数は **3,982 bytes**（実効上限3,983）。既存安全義務は追加削減していません。

所有外への波及可能性：

- callerはcleanup dispatcherを読むcleanup-branches Skill。
- consumerは`tools/check_docs.py`のpin、`test_check_docs.py`の独立pin・whole-file fixture・byte/行長検査。
- 共有fixture変更はwhole-file command fixtureの同期のみ。期待値の緩和はありません。
- 新監査テストは`tmp_path`、`capsys`、`monkeypatch`のみ使用。
- mutation harnessは外部job artifactの更新済みspecを消費します。

やり残しは、親による変異matrix本走、焦点再レビュー、統合commit・provenance監査・landです。