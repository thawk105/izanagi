## 現行挙動

変更前の `load_states` は、`story_version`・`figure_created` とも接尾辞なしの `YYYY-MM-DD` と有効な暦日を要求していました。`2026-09-19` は日付検査を通り、`2026-09-19c`・大文字／複数字接尾辞・不正暦日は拒否されます。

`story_path` は `docs/paper-story/{story_version}.md` との完全一致を要求し、その本文の存在・構造も検査します。変更前の `_caption` は版名によらず旧 `CAPTION.format(...)` を返していました。

## 変更内容

- [plot_arc_status.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/ps21c-arc-impl/tools/plotting/plot_arc_status.py:110)
  - 110〜115 行：`story_version` のみ英小文字 1 字の接尾辞を許容し、先頭 10 文字を暦日検査。`figure_created` と接尾辞込みの path 照合は維持。
  - 359〜362 行：`_caption` を旧版／その他の版で分岐。
  - 448〜449 行：裁定の逐語どおりの `GENERIC_CAPTION` を追加。旧 `CAPTION` は無変更。
- [test_plot_arc_status.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/ps21c-arc-impl/orchestrator/tests/test_plot_arc_status.py:273)
  - 273〜349 行：5 test 関数・計 7 ケースと、実 JSON・実本文を複製する補助関数を追加。
  - 既存 T1〜T8、`BAD_CASES`、自走 harness、subprocess env は無変更。

脚注・描画・layout 検査・provenance schema・既定 JSON・`DEFAULT_STATES` は変更していません。

## 追加した test

| 関数／ケース | 検査内容・期待理由 | 殺す想定の変異 |
|---|---|---|
| `test_t9_default_caption_matches_independent_literal` | 既定図番号 3b・旧 caption 全文の独立 literal 一致 | M8 |
| `test_t10_suffix_version_and_generic_caption` | 接尾辞版の読込み、実寸 Figure の layout、版名、汎用 caption 全文一致、旧 A-4 文の不在 | M1・M6・M7 |
| `test_t11_invalid_story_version[invalid-calendar-day]` | `2026-02-30c`：`day is out of range for month` | M4 |
| 同 `[uppercase-suffix]` | `2026-09-19C`：`ISO date required` | M3 |
| 同 `[multiple-suffix-letters]` | `2026-09-19cc`：`ISO date required` | M2 |
| `test_t12_figure_created_rejects_suffix` | 作成日の接尾辞：`ISO date required` | M5 |
| `test_t13_suffix_version_requires_matching_story_path` | 接尾辞を欠く path：`story_path mismatch` | M6 |

異常系はすべて `PLOT.FigureDataError` と期待理由を検査します。版名異常の 3 ケースには一致する path に実本文を複製するため、検査を除去した際のファイル不在による偽の検出を避けています。変異の KILLED は未確認です。

## meta-test と波及の静的判定

検索・ソース確認から、次のように判定しました。いずれも実走結果ではありません。

| 検査 | 本変更による影響 |
|---|---|
| `test_plain_runner_coverage.py` | 既存の末尾 `pytest.main` 委譲を維持。追加関数の手動登録は不要 |
| `test_check_subprocess_bytecode_guard.py` | subprocess 呼出しの追加なし。既存 `PYTHONDONTWRITEBYTECODE` を維持 |
| `test_pytest_collection_config.py` | file 名・収集設定・除外集合は不変 |
| `test_growth_test_holds_contract.py`・`test_hold_inventory.py` | 固定対象は登録済み hold 集合。本 test は登録対象になく、集合を変更しない |
| `test_campaign_import_invariant.py` | import・campaign namespace・起動形式を変更しない |
| `test_ccbench_spawn_sites.py` | 主対象の campaign／calibrator に変更なし。process・build 呼出しの追加なし |
| `test_site_policy.py` | 固定検査対象の module に変更なし |

`git grep` で確認した直接 consumer は対象 test の import・CLI 呼出しと、生成器内部の `main`／`build_provenance` です。他の Python consumer は見つかりませんでした。共有入力は既定 JSON と旧本文、共有 fixture は対象 test 内の `production` で、いずれも変更していません。

所有外の参照は plotting／figures README、旧 paper-story、旧 provenance、failures・archive・過去 insight の記録です。旧 provenance の生成器 hash は過去の記録として維持します。今回の生成器変更により新規生成時の hash は変わりますが、schema と旧版 caption の仕様は維持しています。

## 未実走の明記

**実装済み・未実走**です。テスト・変異・作図・自走 harness は起動していません。`py_compile` も未実施です。

`git diff --check` は成功し、最終 `git status` の変更は指定の 2 ファイルだけでした。git add・commit・branch 操作はしていません。

## 総括

段 4 plan v2 の最小修正と、独立 literal・実寸 fixture を使う追加 test を実装しました。親側でのテスト・変異実走による確認が残っています。
