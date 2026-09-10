## 総括

**FIX-4: partial — 実装と静的分類は完了したが、pytest が dispatch 障害で 0 件のため closed とは判定しない。**

変更内容:

- [tools/check_docs.py:1294](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/tools/check_docs.py:1294)
  - 非 `worklog-phase<数字>-` 名でも、独立した entry 番号 token があれば `malformed` に分類。
  - 数値 token がなければ従来どおり `unnumbered`。
- [test_check_docs.py:9141](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/orchestrator/tests/test_check_docs.py:9141)
  - `worklog-synthetic.md` が clean のままである parameter を追加。
- [test_check_docs.py:9169](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/orchestrator/tests/test_check_docs.py:9169)
  - `worklog-broken-106-110.md` が `malformed filename` で拒否されるテストを追加。

既存テストの期待値、docs、`spool_fold.py` は変更していません。commit も作成していません。指定された分解形の文字を含む範囲は raw 表示も編集もしていません。

### 実 corpus

| 分類 | 件数 |
|---|---:|
| numbered | 416 |
| unnumbered | 9 |
| malformed | 0 |
| 合計 | 425 |

### 合成 archive 名の分類一覧

| ファイル | 分類 | 件数 | 名前 |
|---|---|---:|---|
| `test_check_docs.py` | numbered | 6 | `worklog-phase3-0730-1.md`、`worklog-phase3-0730-10-12.md`、`worklog-phase3-0730-10.md`、`worklog-phase3-0730-1000.md`、`worklog-phase4-0729-1000.md`、`worklog-phase4-0730-1001-0731-1003.md` |
| `test_check_docs.py` | unnumbered | 23 | `worklog-a-late.md`、`worklog-a.md`、`worklog-aa-newer.md`、`worklog-archive-later.md`、`worklog-archive-structure-later.md`、`worklog-archive-structure-malformed.md`、`worklog-archive-unreadable.md`、`worklog-external-unapproved.md`、`worklog-first.md`、`worklog-h2-collision.md`、`worklog-new.md`、`worklog-phase1-2.md`、`worklog-phase3-0722-0724.md`、`worklog-phase3-0730.md`、`worklog-rotation-new.md`、`worklog-rotation-prelude.md`、`worklog-second.md`、`worklog-synthetic-latest.md`、`worklog-synthetic.md`、`worklog-tab-scope-replay.md`、`worklog-z-early.md`、`worklog-z.md`、`worklog-zz-older.md` |
| `test_check_docs.py` | malformed | 5 | 新規負例 `worklog-broken-106-110.md`、既存負例 `worklog-phase10-0730-10-999-12.md`、`worklog-phase3-0730-0731-0732.md`、`worklog-phase3-0730-106-110-copy.md`、`worklog-phase3-106-110.md` |
| `test_spool_fold.py` | numbered | 0 | なし |
| `test_spool_fold.py` | unnumbered | 14 | `worklog-global-chain.md`、`worklog-global-duplicate.md`、`worklog-global-four-digit.md`、`worklog-global-future.md`、`worklog-global-gap.md`、`worklog-global-max.md`、`worklog-global-missing-task.md`、`worklog-global-substantive.md`、`worklog-global.md`、`worklog-impossible-date.md`、`worklog-legacy-a.md`、`worklog-legacy-b.md`、`worklog-old.md`、`worklog-rotated.md` |
| `test_spool_fold.py` | malformed | 1 | `worklog-phase3-2099-1.md`。既知の従来分類で、FIX-4 の影響ではない |

既存の非 `phase` fixture が新規則によって malformed へ移った例は 0 件です。

### 検査結果

- `python3 tools/check_docs.py`
  - rc=0
  - 出力: `check_docs: 違反なし`
- `python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_check_docs.py -rf`
  - rc=16
  - `Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1`
  - 実走件数: **0 件**
- 自動配置での再試行も同じ rc=16。pytest を直接起動する迂回はしていません。
- `python3 tools/check_codex_agents.py`: rc=0
- `git diff --check`: rc=0
- 作業ツリーの変更は許可された 2 ファイルだけです。