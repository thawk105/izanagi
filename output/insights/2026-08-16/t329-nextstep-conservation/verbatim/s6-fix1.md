## 総括

FIX-1〜FIX-3を実装しました。実 corpus は期待値どおりで、canonical checker は rc=0 です。ただし pytest は dispatch 基盤障害で実走できなかったため、3件とも最終状態は `partial` です。commit・docs 編集は行っていません。

| 所見 | 状態 | 結果 |
|---|---|---|
| FIX-1 filename fail-open | partial | 正規文法へ限定。425件中 numbered 416、unnumbered 9、malformed 0 |
| FIX-2 旧書式 carry | partial | 末尾注記を含む31,935件を検出。指定4行も検出 |
| FIX-3 README保持量 | partial | generator化し、production callerは1回だけ逐次消費 |
| regressed | なしを確認 | `check_docs.py` rc=0。ただしpytest未実走 |

変更箇所:

- [tools/check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/tools/check_docs.py:783)
- [test_check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/orchestrator/tests/test_check_docs.py:9104)

追加・強化した検査は、MMDD欠落、entry token 3個、日付 token 3個、phase範囲名の維持、注記付き旧 carry、新書式の散文内出現、README論理項目の逐次生成です。意図的な分解文字2箇所は両方とも保持されています。

検査結果:

- `python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_check_docs.py -rf`
  - rc=16
  - `qstat -Q preflight rc=1`
  - 実走 nodeid: なし、0件
- 非強制 wrapperも同じ理由でrc=16、実走0件
- `python3 tools/check_docs.py`
  - rc=0
  - `check_docs: 違反なし`
- `python3 tools/check_codex_agents.py`
  - rc=0
- AST構文解析、`git diff --check`
  - rc=0

静的な波及可能性:

- filename分類はREADME範囲、archive carry収集、全域entry universe登録に波及します。
- 旧carry拡張は現行worklogと採番archiveの次の一手に波及します。新書式の`fullmatch`は維持しています。
- README generatorの唯一のproduction callerは逐次消費済みです。
- 新しいparameter nodeが増えたため、親の変異matrixでは最終commit上の期待node完全集合を再導出する必要があります。
- `spool_fold.py`、docs、既存期待値は変更していません。