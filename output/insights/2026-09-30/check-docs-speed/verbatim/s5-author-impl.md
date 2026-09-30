## 変更点

[check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed-impl/tools/check_docs.py:1385) に plan v2 の O1・O2・O3・O4'・O5 と正規表現の事前 compile を実装しました。変更箇所は `_line_number`（1394 行）、`_visible_markdown_lines`（1495 行）、`_top_level_item_raw_slice`（1976 行）、`_is_carry_candidate`（2001 行）、`_check_backlog_guard`（2882 行）と `_ArchiveWorklog`（1100 行）です。

## 等価性の根拠

- O1 は負の offset を `str.count` と同じ規則で正規化し、改行位置を値キーの上限 4 件 LRU で参照します。
- O2 は entry 本文の ID を位置ごとに保持し、同じ本文 ID を遷移先にも使います。O4' は各 archive の先頭・末尾の比較値を順序検査内で一度だけ求めます。
- O3 は CR、LF、CRLF の終端を維持します。O5 はコメント外かつ `<!--` のない行だけを素通しします。所見の追加順、早期 return、carry generator、読取 cache と `Path.open` の処理は変更していません。

変更前の受理・拒否条件を変える処理は入れていません。ただし全入力木での一致を示す pytest 全走は未実走です。

## 追加 test

[test_check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed-impl/orchestrator/tests/test_check_docs.py:12965) の末尾に T1〜T3、遷移境界の正負 6 ケース、archive 順序 1 ケースを追加しました。T2・T3 の参照処理には基準 commit の旧関数本体を使っています。既存の期待値・fixture は変更していません。

## 変異の確認

M1・M2 は `test_speed_line_number_matches_count_boundaries`、M3・M4 は `test_speed_transition_sink_uses_whole_entry_body`、M5 は `test_speed_raw_slice_matches_reference_exhaustively`、M6 は `test_speed_visible_lines_matches_reference`、M7 は `test_speed_archive_order_uses_last_entry_of_left_archive` の直接呼出しで、それぞれ赤になりました。各変異後に元のバイト列へ復元したことを確認しています。**pytest の赤い nodeid は取得できていません。**

## 実走結果

追加 10 ケース、関連する既存の遷移・carry 7 件、読取 cache 2 件、hold inventory 1 件は直接関数呼出しで通過しました。`python3 tools/check_docs.py` は **rc=0、末尾「check_docs: 違反なし」**。`py_compile` と `git diff --check` も通過しました。

指定の pytest 実走は未実走です。`run_tests.py` は `qstat -Q` の preflight 失敗（rc=16）で子を起動できず、直接の pytest 起動はログインノードの PreToolUse hook に拒否されました。

## 波及

所有外の呼出し元は `tools/spool_fold.py`、`tools/dev_wave_land.py`、`tools/scoped_acceptance.py` です。共有 helper `_build_min_repo`・`_write_backlog_docs`・`_run_check` は再利用のみで、編集していません。関連 consumer の pytest 全走も未実走です。

## 総括

実装と合成入力での確認は完了しました。完了判定に必要な pytest 全走と旧版との木全体比較は、実行基盤が使える状態で残っています。