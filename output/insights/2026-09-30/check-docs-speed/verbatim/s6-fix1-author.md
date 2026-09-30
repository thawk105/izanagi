## 所見ごとの対応

- **F1（hold 契約違反）: partial** — 追加テスト群を hold 呼出しの前へ移し、手動 runner でも parameterized test の 6 ケースを実行できました。hold 契約の直接呼出しは通過しましたが、pytest は未実走です。
- **F2（A1/B2、cache の寿命）: partial** — `main()` の `finally` で改行位置 cache を消すよう変更し、正常終了時と例外時の両方で解放を確認しました。pytest は未実走です。
- **F3（B1、archive の ID 保持量）: partial** — archive 間の境界に必要な先頭 entry の本文 ID だけを保持するよう変更しました。M4 変異が T4 で赤になり、元のコードへ復元済みです。pytest は未実走です。

## 変更点

[check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed-impl/tools/check_docs.py) と [test_check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed-impl/orchestrator/tests/test_check_docs.py) のみ変更しました。既存テストの期待値と追加テストの中身は変更していません。commit は作成していません。

## 実走結果

直接関数呼出しで追加テスト **10 ケース**、hold 契約 **1 ケース**が通過しました。手動 runner の新規 **6 ケース**、cache 解放の **2 経路**も通過しました。`git diff --check` は成功しました。

pytest は **実装済み・未実走**です。`tools/run_tests.py` は `qstat -Q` の事前確認で失敗し、テスト子プロセスは起動していません。

## 波及

archive 境界の sink は従来と同じ先頭 entry の本文 ID を使います。直接実行した正例・負例では挙動を維持しています。rc・findings・warnings の全入力での一致確認は、親の再走結果待ちです。

## 総括

F1〜F3 の修正は実装済みです。pytest による最終確認が残っています。