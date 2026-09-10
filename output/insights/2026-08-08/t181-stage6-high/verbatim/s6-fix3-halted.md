F9 は **partial のまま停止**しました。実装・テスト追加・commit は行っていません。

## 停止理由

依頼の「CR 版 docs が引き続き通る」という期待値が、現行 production path と一致しませんでした。

合成 repo で `workers.md` 全体を CR 区切りにして `main()` を実行すると、期待した空集合ではなく次の 12 findings になります。

- S02 / S03 / S06-A / S06-C の pin finding
- `DW-S02` / `S03` / `S05-A` / `S05-B` / `S05-C` / `S06-A` / `S06-B` / `S06-C` の H2 不在 finding

原因は、独立行判定より前の [_reference_id_sections()](/work/1/SFC/tanab/izanagi/.claude/worktrees/dw-t181-fix3/tools/check_docs.py:1710) と H2 inventory が LF を節境界として要求するためです。CR 全文を通すには F9 の `splitlines()` 一箇所だけでなく、共有の節抽出・inventory まで変更する必要があります。これは F9-only および S02/S03 挙動不変の制約を越えます。

「期待値そのものが誤りなら実装せず停止」の指示に従いました。

## Probe 結果

事前指定した期待集合と現行結果は次のとおりです。

- Unicode separator 5 種 × S06-A/C:
  - 期待: 対応する S06 finding の singleton
  - 現行: 10 ケースすべて空集合（迂回を再現）
- CRLF 全文:
  - 期待・現行とも空集合
- CR 全文:
  - 期待は空集合、現行は上記 12 findings
- 現行 [workers.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dw-t181-fix3/docs/dev-wave/workers.md):
  - S06-A 規範文は物理行 48 に exact-one
  - S06-C 規範文は物理行 67 に exact-one
  - production pin findings は空集合
- `python3 tools/check_docs.py`: `rc=0 / check_docs: 違反なし`

pytest/nodeid は未実走です。実装済み・未実走ではなく、**未実装・停止**です。

## 静的波及先

所有外で影響し得る箇所は以下です。

- caller: `_check_command_docs_guard()`
- 共有処理: `_visible_dispatch_inventory_text()`、`_reference_id_sections()`
- 共有 fixture: `_write_command_guard_docs()`、`_build_min_repo()`
- consumer: S02/S03/S06/O16 pin テスト、dispatch H2 inventory テスト
- test helper: `_run_check()`、`_finding_set()`

F9 以外の問題として、CR-only 文書を共有節抽出が扱えない点を「実装せず報告のみ」とします。closed 済み項目には触れておらず、worktree は clean です。

## 総括

- F9: **partial**
- closed: いいえ
- regressed: いいえ（変更なし）
- Unicode separator 迂回は再現済み
- 現行 workers.md の 2 規範行は production probe で通過
- CRLF 全文は通過、CR 全文は 12 findings
- F9-only では CR 正例を成立させられない
- 編集・commit・pytest 実走なし
- 残る懸念: CR 正例の意味または共有節抽出変更の scope 裁定が必要