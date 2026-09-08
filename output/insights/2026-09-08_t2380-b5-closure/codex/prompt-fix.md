単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze

必読事項の射影:
- /home/SFC/tanab/.claude/jobs/9218ced6/tmp/t2380/artifacts/dev-wave-t2380-b5-successor-freeze/review_a_1.md (段 6 レビュー A。RA-08 が対象。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/9218ced6/tmp/t2380/artifacts/dev-wave-t2380-b5-successor-freeze/review_b_1.md (段 6 レビュー B。RB-01 と RB-05〜RB-12 の「直接 oracle」提案が対象。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/tests/test_axis_b5_search_catalog.py (編集対象、未 commit。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/axis_b5_search/catalog.py (**読むだけ。変更禁止**。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-closure-preregistration.md §3.2〜§3.4 (契約。読めなければ即停止)

## 役割と所有

あなたは dev-wave 段 6 の fix 子 (Codex `role=author`) である。段 5 の実装子契約 (所有 path 限定、テストを甘くしない、期待値を変えない、commit 禁止、docs 編集禁止) を全文継承する。
**編集してよい file は `orchestrator/tests/test_axis_b5_search_catalog.py` の 1 つだけ。** `catalog.py` と生成 JSON と他の file は 1 byte も変えない。

## 親の裁定 (レビュー所見の採否)

- **RA-04 / RA-05 (index 値の表記、year の型):** 親裁定 = `index` は凍結 ID の literal と同じ小文字 token `arxiv` / `openalex` / `dblp`、`year` は JSON number。**現行の実装と生成 JSON のとおりで、bytes は変えない。** test の literal はこの裁定値のままでよい。
- **RA-08 (自己参照の期待値、must-fix):** 次の 3 test の期待値を production の renderer から作らない形に直す。
  - `test_render_catalog_json_is_canonical_deterministic_and_one_newline`: 期待値を `build_catalog_document()` + `json.dumps` で作らず、**tracked JSON の bytes と、その SHA-256 の固定 literal `7eb8385e35bd24edac8a227a72ba5bc6b568ca8bc7cac2c8250af8b4ea4c346f`** を oracle にする (render bytes の sha256 == literal、末尾 newline ちょうど 1 個、2 回 render が一致、UTF-8 decode 可)。
  - `test_cli_output_writes_exact_rendered_bytes`: 出力 bytes の sha256 == 上の literal、かつ tracked JSON と一致。
  - `test_cli_verify_accepts_exact_and_rejects_one_byte_change`: 正例 fixture は **tracked JSON の bytes をコピー**して作る (renderer を呼ばない)。負例は末尾 1 byte 追加で rc=1。
- **RB-01 (独立 oracle の穴、must-fix):** node を増やさず、既存 test に次を足す。期待値は test 側の独立 literal (test 内に既にある 85 語・block 順・10 枝の literal) から導出し、production の `BLOCKS` / `BRANCHES` / helper を使わない。
  - `test_main_query_ids_order_and_cardinalities_are_exact`: 1622 本の `query_id` の**完全列** (arXiv Q1〜Q10、OpenAlex Q1〜Q10、DBLP は Q4〜Q10 の枝順で左語外側・右語内側) を test 側 literal から組み立てて完全一致させる。各 query の `term_groups` が test 側 literal の block/語 ID から導いた値と一致する (arXiv/OpenAlex は block ごとの語 ID 列、DBLP は `[[左],[右]]`)。
  - `test_openalex_q1_full_url_is_unquoted_and_keeps_comma_unencoded`: 全 OpenAlex query と control について `request_template` が literal `&cursor={CUR}` で終わり、`first_page_url` が `&cursor=*` で終わり、両者が `{CUR}` → `*` の置換関係にあることを検査する。全 arXiv / DBLP entry (control・venue 含む) についても `{POS}` と `0` の同じ関係を検査する。
  - `test_dblp_cartesian_branch_counts_bounds_and_request_bytes_are_exact`: 全 DBLP record について `query_id` / `term_groups` / `first_page_url` の三者対応 (URL の `q=` が test 側 literal の 2 語を空白で連結して `%20` 符号化したものと一致) を検査する。
  - `test_aux_venue_streams_have_frozen_range_order_ids_and_full_urls`: 全 272 entry について `stream_id` / `index` / `venue` / `year` / `request_template` / `first_page_url` を test 側 literal (8 venue × 1993〜2026 と template 文字列) から組み立てた完全列と一致させる。
- **RB-05〜RB-12 の「直接 oracle」提案:** 採用してよい。既存 test 関数の先頭に `_percent_encode("a b") == "a%20b"`、`_percent_encode("a,b", preserve_comma=True) == "a,b"`、`_term_id("T", 1) == "T01"` のような直接 assertion を足してよい (import は `orchestrator.axis_b5_search.catalog` から)。**新しい test 関数は作らない。**
- **RB-02 / RB-03 / RB-04、RA-01〜RA-03 / RA-06 / RA-07 / RA-09:** refuted、変更なし。

## 禁止

- **`git add` / `git commit` / `git stash` / `git checkout` など git の状態を変える操作を一切しない。commit は親が行う。**
- docs を編集しない (`docs/handoff/` への file 作成を含む)。`catalog.py`・生成 JSON・他 test・tools・schema を変えない。
- 既存 test の期待値を緩めない・反転しない・skip や削除をしない。赤になったら実装側の誤りとして報告し、期待値を実装に合わせない。
- test 関数の追加・改名・削除をしない (nodeid 17 本を保つ)。
- 外部 network を使わない。出力に結合文字 U+0300〜U+036F を使わない。

## 実走

`PYTHONPATH=. python3 orchestrator/tests/test_axis_b5_search_catalog.py` を実行し rc と passed 数を報告する。実走できないなら「未実走」と書き、module を import して各 test 関数を直接呼び出した結果を書く。走らせていない結果を書くな。

## 出力形式

見出しは全部 H2 (`## `) で書く。最後の節は必ず `## 総括` (`#` を 2 個) とする。`### 総括` と書いてはならない。

## 変更した test と対応する所見 (closed / partial / regressed の表)
## 実走した結果
## 総括
