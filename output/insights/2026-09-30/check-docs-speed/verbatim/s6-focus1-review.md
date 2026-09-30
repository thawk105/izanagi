## 対応表

| 所見 | 状態 | 根拠 |
|---|---|---|
| F1：hold 呼出し位置 | closed | 追加テストはすべて呼出しより前にあり、呼出しは `__main__` guard より前です。[test_check_docs.py:13056](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed/orchestrator/tests/test_check_docs.py:13056)、[同:13087](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed/orchestrator/tests/test_check_docs.py:13087)、[同:13090](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed/orchestrator/tests/test_check_docs.py:13090)。指定された hold 契約の行番号条件にも合います。 |
| F2：LRU 寿命 | closed | `main()` の `finally` で読取 cache の reset に続いて改行位置 cache を消します。[check_docs.py:6685](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed/tools/check_docs.py:6685) |
| F3：先頭 entry の ID だけ保持 | closed | archive 内の遷移には局所リストを使い、archive オブジェクトには先頭分だけを渡しています。[check_docs.py:1106](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed/tools/check_docs.py:1106)、[同:3190](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed/tools/check_docs.py:3190)、[同:3199](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed/tools/check_docs.py:3199) |
| A1：大きな文字列の LRU 保持 | partial | `main()` 終了後の保持は解消しました。実行中は最大4件を保持し、大きな文字列を対象から外す案は未実装です。[check_docs.py:1384](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed/tools/check_docs.py:1384)、[同:6693](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed/tools/check_docs.py:6693) |
| A2：T4 の断片 assert | not-addressed | T4 の本文は変更されていません。[test_check_docs.py:13007](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed/orchestrator/tests/test_check_docs.py:13007)。裁定ではこの変更を不採用とし、repo 外の全文比較を根拠としています。 |
| A3：実 corpus・作成量 | partial | 追加テストの本文は変更されていません。[test_check_docs.py:12963](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed/orchestrator/tests/test_check_docs.py:12963)。裁定には焦点走の総所要がありますが、個別所要や helper の作成量は今回の指定資料から確定できません。 |
| B1：全 entry ID の保持 | closed | F3 と同じ修正です。[check_docs.py:3190](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed/tools/check_docs.py:3190) |
| B2：LRU の常駐量 | partial | 呼出し間の保持は F2 で解消しました。1回の `main()` 内の peak や旧版との RSS 比較は、この静的検査では確認できません。[check_docs.py:1384](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed/tools/check_docs.py:1384)、[同:6693](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed/tools/check_docs.py:6693) |
| B3：追加テストの所要 | partial | 裁定は焦点走全体の所要を報告していますが、個別所要は別途記録予定です。テスト群は[test_check_docs.py:12963](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed/orchestrator/tests/test_check_docs.py:12963)以降です。 |

## 新規所見

**なし。** 空 archive は抽出時に `None` となり呼出し側で処理を中断するため、`archive_entry_ids[0]` には到達しません。[check_docs.py:1443](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed/tools/check_docs.py:1443)、[同:3099](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed/tools/check_docs.py:3099)、[同:3190](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed/tools/check_docs.py:3190)。archive 境界には右 archive の先頭 ID、現行 worklog 境界には現行の先頭 ID が渡されており、取り違えも見当たりません。[check_docs.py:3240](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed/tools/check_docs.py:3240)、[同:3256](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed/tools/check_docs.py:3256)。

テスト差分では、テスト本文の変更はなく、hold 呼出しと guard の移動、および手動 runner への6ケースの登録だけを確認しました。この fix が rc・findings・warnings の列を変える新たな入力は、静的検査では見つかりませんでした。

## 総括

**GO（静的再レビュー）。** 新規 must-fix・should-fix・nit はありません。テストは指示どおり実行していません。