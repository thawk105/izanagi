1. **should-fix — `tools/check_docs.py:1384`（O1）**
   反例入力: 改行が非常に多い大きな文字列を異なる値で 4 個処理すると、LRU が元文字列と改行位置の `int` 列を `main()` 終了後も保持します。旧 `str.count` にはこの保持がなく、メモリ上限下では新実装だけが失敗しえます。同値の別 object や hash 衝突は値キーの照合で区別され、判定値は変わりません。**推奨修正:** キャッシュを `main()` の終了時に消し、巨大な文字列はキャッシュ対象から外す。

2. **should-fix — `orchestrator/tests/test_check_docs.py:13046`（T4）**
   反例入力または根拠: 負例は rc=1 と所見の断片だけを確認します。余分な所見・警告、所見の順序や全文が変わっても通ります。正例も警告の追加を見逃します。**推奨修正:** 旧実装との rc・stdout 全文比較を予定どおり実走し、その結果を判定根拠にする。

3. **nit — `orchestrator/tests/test_check_docs.py:13010`（実 corpus への到達性）**
   根拠: 追加テストは合成文字列と `_build_min_repo()` を使い、追加部分に実 docs corpus への明示的な参照はありません。T1〜T3 の入力数は固定です。一方、指定された閲覧範囲に `_build_min_repo()` の定義がないため、T4 の作成量が repo の成長と独立かは静的に確定できません。**推奨修正:** 親が helper の実体と実走時間を確認する。

**判定不変の確認:** O1 の通常入力での行番号は負 offset・範囲外を含め旧 `count` と一致します。O2 の `_top_level_ids` は所見を追加しない純粋な走査で、section が `None` の entry への先行実行も所見順を変えません。O3 は `\r`・`\n` を同じ位置で探します。O4' の比較式は旧 `_entry_point_is_before` と同じで、見出しは抽出時に full-match 検証済みのため、呼出し時点の変更による `ValueError` は到達しません。O5 の近道と事前 compile も同じ入力に同じ値を返します。これらについて、資源枯渇を除く rc・所見・警告の差を生む入力は構成できませんでした。所有外 consumer に公開関数の引数変更はなく、追加された dataclass フィールドには既定値があります。ただし、指定外ファイルは読んでいないため consumer の全呼出しは未確認です。

**変異の検出先:** M1・M2 → `test_speed_line_number_matches_count_boundaries`、M3 → `test_speed_transition_sink_uses_whole_entry_body` の本文 ID あり、M4 → 同テストの archive 境界かつ本文 ID なし、M5 → `test_speed_raw_slice_matches_reference_exhaustively`、M6 → `test_speed_visible_lines_matches_reference`、M7 → `test_speed_archive_order_uses_last_entry_of_left_archive`。指定の M1〜M7 に、静的に赤とならない変異は見つかりませんでした。

## 総括

**NO-GO。** 新たな判定ロジック上の must-fix は見つかりませんでした。既知の **hold 契約違反**（追加テストが `enforce_held_functions(...)` より後ろ）は修正が必要です。テスト・旧版比較はこのレビューでは実行していません。