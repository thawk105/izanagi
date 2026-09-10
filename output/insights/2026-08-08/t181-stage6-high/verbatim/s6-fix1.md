実装は完了しました。変更は指定された2ファイルだけで、docs 編集・commit はしていません。ただし pytest は実行基盤の `rc=16` により未実走なので、契約どおり全項目を `partial（実装済み・未実走）` とします。

## 対応表

| 所見 | 状態 | 対応 |
|---|---|---|
| F1 | partial | reasoning pin と必須 H2 inventory を raw HTML 対応可視化へ統一。`<x>` wrapper test を direct/production に追加 |
| F2 | partial | S06-A/C の規範文を逐語定数化し、値列検査とは独立した exact-one pin を追加。例示リンク・別 key decoy 負例を追加 |
| F3 | partial | 前方境界へ `. / ?` を追加。URL/path/note を受理し、canonical high/max を抽出する正例を追加 |
| F4 | partial | `DW-O16` 節だけを抽出し、可視 effort 値が空であることを pin。O16=max production 負例を追加 |
| F5 | partial | raw HTML、S06-C production exact、decoy、URL/path、O16 の全指定ケースを追加。pytest 未実走 |

主な実装は [check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dw-t181-fix/tools/check_docs.py:268) と [test_check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dw-t181-fix/orchestrator/tests/test_check_docs.py:5157) です。

## 受理集合の対比

変更前後で次のようになります。

- raw HTML 内へ隠した S06-A/C: 受理 → 拒否
- 規範文を同値 decoy へ置換: 受理 → 拒否
- `DW-O16` の `reasoning=max`: 受理 → 拒否
- URL/path中の `reasoning=`: 過剰拒否 → 受理
- canonical S02/S03=max、S06-A/C=high、S06-B literalなし、不可視 comment/fence decoy: 挙動維持
- 曖昧値・複数値・別の実 key: 拒否を維持

`values != [expected]` は残してあり、既存 S02/S03 finding 逐語も変更していません。`DEV_WAVE_AGGREGATE_BYTES` と `REFERENCE_LIMITS` も未変更です。

## 期待 finding 集合

- current docs / URL・path正例: `{}`
- raw HTML S06-A: `{S06-A pin finding, S06-A H2=0 finding}`
- S06-A decoy: `{S06-A pin finding}`
- S06-C=max: `{S06-C pin finding}`
- DW-O16=max: `{DW-O16 effort finding}`

read-only probe では上記の pin 結果、raw HTML後の S06-A inventory/section count=0、canonical values=`["high", "max"]` を確認しました。

## 検査

- `python3 tools/check_docs.py`: `check_docs: 違反なし`
- `python3 tools/check_codex_agents.py`: OK
- AST parse: 2ファイルとも成功
- `git diff --check`: 成功
- focused 15 nodeid実走: 未実走。`tools/run_tests.py` が admission 後に compute dispatch を選び、`qstat -Q preflight rc=1`、`rc=16`
- collect-only再試行: 同じ `rc=16`

pytest直起動や内部 admission markerによる迂回はしていません。

## 静的な波及可能性

- 所有外 caller: production `_check_command_docs_guard()` が operations text を追加で渡します。private helper の既存2引数 callerは optional引数により互換です。
- 共有 fixture: `_write_command_guard_docs()` のS06合成本文を規範文へ更新しました。
- consumer test: command guard全般、必須reference section検査、reasoning pin test群が影響範囲です。
- `_visible_markdown_text()` 自体は変更していないため、provenance・top-level item・condition dispatch等の既存consumerには波及させていません。
- operations全体は走査せず、O16節だけを対象にしています。O01の正当な起動雛形は現行 `check_docs` 緑で維持されています。

## 総括

F1〜F5はすべて実装済みですが、pytest未実走のため状態は `partial` です。
指定外ファイル、docs、予算定数、既存finding逐語には触れていません。
静的検査・production checker・focused probeは期待どおりです。
残る懸念は、親環境で追加nodeidと `test_check_docs.py` 全体を実走することだけです。