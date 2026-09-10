F6〜F8 を実装しました。変更は指定された 2 ファイルのみで、docs 編集・commit はしていません。pytest は実行基盤の `rc=16` により未実走のため、契約に従い全件 `partial（実装済み・未実走）` とします。

## 対応表

| 所見 | 状態 | 対応 |
|---|---|---|
| F6 | partial | S06-A/C の規範文を可視節内の完全一致行として exact-one 検査。blockquote、list、見出し、前後置、末尾空白、重複を production 負例化 |
| F7 | partial | 規範文を保持したまま可視な `` `reasoning=max` `` を追加する production 負例を S06-A/C 別 node で追加 |
| F8 | partial | 規範文を `` `reasoning=high/max` `` に置換し、`main()` の finding 集合だけを比較する専用 node を追加。中間 regex assertion なし |

実装箇所は [check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dw-t181-fix2/tools/check_docs.py:3444) と [test_check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dw-t181-fix2/orchestrator/tests/test_check_docs.py:5300) です。

## 受理集合

- F6 修正前に通った「参考（旧規範）: 全文」と blockquote 全文は、修正後は拒否されます。
- 規範文が prefix/suffix/末尾空白なしの独立行として一度だけ存在する現行契約は引き続き受理されます。
- S02/S03 は従来どおり substring pin のままで、受理・拒否挙動と finding 逐語を変更していません。
- `values != [expected]` はそのまま残し、別 effort 混入を拒否する相補層を維持しています。
- F7/F8 は既存の拒否集合を変更せず、変異 receipt の単一理由性を補うテスト追加です。

現行 [workers.md:48](/work/1/SFC/tanab/izanagi/.claude/worktrees/dw-t181-fix2/docs/dev-wave/workers.md:48) と [workers.md:67](/work/1/SFC/tanab/izanagi/.claude/worktrees/dw-t181-fix2/docs/dev-wave/workers.md:67) は、直前が空行、直後が次の本文行です。`sed -n l` で句点直後に行終端 `$` があり、末尾空白がないことも確認しました。

## 期待 finding 集合

- 現行 docs: `{}`
- F6 S06-A の各 prefix/suffix/重複負例: `{DEV_WAVE_DW_S06_A_REASONING_HIGH_FINDING}`
- F6 S06-C の各負例: `{DEV_WAVE_DW_S06_C_REASONING_HIGH_FINDING}`
- F7 S06-A/C の追加 max: 対応する S06 finding だけ
- F8 `reasoning=high/max`: `{DEV_WAVE_DW_S06_A_REASONING_HIGH_FINDING}`

これ以外の finding は回帰扱いです。

## 検査

通過済み:

- `python3 tools/check_docs.py`: `check_docs: 違反なし`
- `python3 tools/check_codex_agents.py`: OK
- 変更 2 ファイルの AST parse: OK
- `git diff --check`: OK
- 差分: 2 files、128 insertions / 1 deletion

`tools/run_tests.py` で次の 8 node を投入しましたが、`qstat -Q preflight rc=1`、runner `rc=16` となり、pytest 本体は未実走です。

- 現行 workers 契約
- F6 独立行 production node
- F7 S06-A extra-effort node
- F7 S06-C extra-effort node
- F8 ambiguous-value node
- 既存 S06-A=max node
- 既存 S06-C=max node
- 既存 URL/path 正例 node

新規 4 node の collect-only も同じ `rc=16` でした。pytest 直起動や admission の迂回はしていません。

## 静的な波及可能性

- production caller は `_check_command_docs_guard()` の一経路です。
- direct helper consumer は同テストファイルの `_reasoning_effort_pin_findings()` です。
- 共有 `_write_command_guard_docs()` fixture は既に規範文を独立行で生成しており変更不要です。
- reasoning pin 群、command guard 全体、`test_real_repo_clean` が直接 consumer です。
- `_visible_dispatch_inventory_text()` や H2 inventory は変更していないため、F1/F3/F4/F5 の層には手を加えていません。
- `tools/codex_reasoning_ab.py` は歴史 benchmark の旧 source hash を凍結保持しています。snapshot のため更新していませんが、current checkout を入力に再捕捉する用途では差分として観測されます。

## 総括

F6〜F8 はすべて実装済みですが、pytest 未実走のため `partial` です。
F6 は規範文を可視な完全一致独立行として exact-one にしました。
F7 は S06-A/C 固有の M3 receipt、F8 は M10 単一理由 receipt を追加しました。
S02/S03、値列検査、既存 finding、予算定数、closed 済み挙動は変更していません。
残る懸念は、親環境で新規 node と `test_check_docs.py` 全体を実走することです。