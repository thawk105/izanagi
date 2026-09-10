## 対応

**partial**

R4 の実装とテスト追加は完了しました。pytest は dispatch 基盤障害で未実走のため、closed とはしていません。regression は確認していません。

## 実装した変更

- [tools/spool_fold.py:62](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:62)
  - `^ {0,3}-[ \t]+\*\*supersede:` の専用正規表現を追加。
- [tools/spool_fold.py:65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:65)
  - U+200B、U+200C、U+200D、U+2060、U+FEFF の除去投影を追加。
- [tools/spool_fold.py:775](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:775)
  - HTML comment 除去済み可視行からゼロ幅文字を除去し、専用正規表現で R4 を判定。
- [orchestrator/tests/test_spool_fold.py:1364](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/orchestrator/tests/test_spool_fold.py:1364)
  - 指定された拒否・受理ケースを追加。

`FAILURE_SUPERSEDE_ITEM_RE`、`_insert_failure_recurrences`、挿入位置、topology、行区切り検査は今回変更していません。既存 tracked テストの期待値も変更していません。

## 拒否・受理の一覧

対象 nodeid:

`orchestrator/tests/test_spool_fold.py::test_failure_recurrence_supersede_misuse_is_rejected_but_prose_mention_is_accepted`

拒否を固定:

- 裸の `- **supersede:`
- HTML comment 分割6形
- 行頭空白1・2・3個
- marker 直後のtab
- ラベル内部のゼロ幅文字5種

受理を固定:

- fenced code block 内のdecoy
- 行頭空白4個のインデント行
- 全角 `ｓｕｐｅｒｓｅｄｅ`
- 通常prose中の supersede 言及

## 走らせた検査

- 上記単独 nodeid: **rc=16**
  - `tools/run_tests.py` 経由
  - `qstat -Q preflight rc=1` によりpytest起動前停止
- `orchestrator/tests/test_spool_fold.py` 全体: **rc=16**
  - 同じ理由でpytest未実走
- 上記テスト関数の手動probe: **rc=0**
  - pytestの緑とは扱っていません
- `python3 -m py_compile tools/spool_fold.py orchestrator/tests/test_spool_fold.py`: **rc=0**
- `git diff --check`: **rc=0**
- `python3 tools/check_docs.py`: **rc=0**（パイプ不使用、違反なし）
- `python3 tools/check_codex_agents.py`: **rc=0**

## 受理集合への影響

`再発` 節内でMarkdown上 `- **supersede:` と等価になる指定prefixだけを追加拒否します。4-space code block、fence、全角ラベル、通常proseは引き続き受理します。production の fail-open 化や段4裁定Eを超える拡張はありません。

docs は編集しておらず、commit も作成していません。

## 総括

R4 の迂回経路は実装上閉じ、指定された正負制御をテストへ固定しました。現状は**実装済み・pytest未実走**です。