## 実装

指定の 3 ファイルを新規作成しました。

- `tools/plotting/plot_arc_status.py`：入力・anchor・自由文検査、描画、保存前 layout 検査、provenance、上書き禁止 CLI。
- `tools/plotting/arc_status_story_2026-09-19.json`：裁定 §12 を転記。実使用の `reference_ids` は `T-1998` のみ。
- `orchestrator/tests/test_plot_arc_status.py`：T1〜T8。

S4 の仕様変更なし。docs・既存ファイルは未変更、commit は作成していません。

## 実走

指定コマンドは **rc=0**。以下の 3 成果物を生成しました。

`probe-fig3b/out/fig3b_arc_status_2026-09-20.{png,pdf,provenance.json}`

- `drawn_items`：27 件（Act 見出し 3、Act 行 8、証拠項目 16）
- 入力 SHA-256 先頭：states `473aba56`、story `0553280d`
- 入力・生成器・出力の全 hash が現物と一致。PNG 目視確認済み。

## test

**代替 runner で 29 ケース通過、T1〜T8 合計 7.925 秒。** 実走 nodeid 全件は [実行記録](/work/1/SFC/tanab/izanagi/.codex/worktrees/fig3b-unit-impl/probe-fig3b/test-results.txt) にあります。

実寸 Figure は 6 個。全体描画は 7 回（ローカル実測 4 回＋正常 CLI の layout・PNG・PDF 各 1 回）。T2 は実 artist を Agg renderer で測り、追加の全体描画を省いています。

pytest 本体は未実行です。`run_tests.py` は `qstat -Q` 失敗で rc=16、指定の直接 pytest は Pegasus 用フックで拒否されたため、許可された `probe-fig3b/run_tests_direct.py` を使用しました。

追加の制約テストも直接呼出しで **4 件通過、107.120 秒**。[nodeid・所要記録](/work/1/SFC/tanab/izanagi/.codex/worktrees/fig3b-unit-impl/probe-fig3b/meta-test-results.txt)

## 変異との整合

位置はすべて `plot_arc_status.py` 内です。

| 変異 | 関数・行 | 対応 test |
|---|---|---|
| M1 | `load_states`:151 | T3 bogus-state |
| M2 | `_keys`:53 | T3 unknown-item-key |
| M3 | `check_display_text`:73 | T4 |
| M4a | `_intersection`:288 | T5 overlap |
| M4b | `_contains`:292 | T5 escape |
| M5 | `build_provenance`:368 | T7 |
| M6 | `make_figure.style`:185 | T2 |
| M7 | `_publish_outputs`:389 | T6 |
| M8 | `_figure_number`:169 | T8 |

変異実行自体は未実施です。

## 波及

- 既存 caller・consumer の変更不要。既存 test との名前衝突なし。
- plotting の総数や provenance schema を横断固定するテストは検索で見つかりませんでした。
- 収集除外・予算定数・qdel caller・receipt 発行箇所の制約テストを確認済み。
- conftest の autouse は site／task-run／exploration／official 環境の隔離。直接 runner では適用されない点が検証上の限界です。

## 総括

**3 ファイルの実装、実 JSON からの生成、代替 runner による単体確認まで完了しました。** 親の pytest 全走・変異試験・PDF 目視・終端 commit に渡せる状態です。