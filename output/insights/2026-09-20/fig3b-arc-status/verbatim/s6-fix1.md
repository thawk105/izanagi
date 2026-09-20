## 変更

- [生成器](/work/1/SFC/tanab/izanagi/.codex/worktrees/fig3b-unit-impl/tools/plotting/plot_arc_status.py:140)：140行でgroup labelを自由文検査へ追加。244・351行でAct行の表示から内部IDを除去。404行で公開前に0644へ変更。
- [test](/work/1/SFC/tanab/izanagi/.codex/worktrees/fig3b-unit-impl/orchestrator/tests/test_plot_arc_status.py:47)：47行でAct表示期待値を追随。148行でdefinition fixtureを文字列化。122・162行でgroup-percentを追加。239行で3成果物のmodeを検査。

既存期待値の変更は指定されたAct表示のみ。差分は2ファイル、11行追加・5行削除。`git diff --check` 通過。

## 実走

指定コマンドは **rc=0**。`probe-fig3b/out-fix1/fig3b_arc_status_2026-09-20` 配下ではなく、このprefixに続く `.png`・`.pdf`・`.provenance.json` の3成果物を生成。全て **0644**。

- `drawn_items`：27項目。Act全8行のlabelから内部IDが消え、余分な空白もないことを確認。
- 内部の`id`、Act見出し、証拠項目IDは維持。
- inputs SHA-256先頭8桁：states=`473aba56`、story=`0553280d`。

## test

pytestは`tools/run_tests.py`経由で試行しましたが、`qstat -Q`のpreflight失敗により **rc=16、test未開始**。指定の既存`probe-fig3b/run_tests_direct.py`で **30ケース通過、6.993秒**。全体描画はローカル実測4回＋CLIの3回＝7回。

実走nodeidは全て `orchestrator/tests/test_plot_arc_status.py::` を接頭辞とする以下です。

```text
test_t1_real_states_render_at_production_size
test_t2_independent_styles_and_changed_state
test_t3_invalid_json_without_drawing[bogus-state]
test_t3_invalid_json_without_drawing[null-evidence]
test_t3_invalid_json_without_drawing[duplicate-id]
test_t3_invalid_json_without_drawing[unknown-item-key]
test_t3_invalid_json_without_drawing[missing-item-key]
test_t3_invalid_json_without_drawing[unknown-top-key]
test_t3_invalid_json_without_drawing[unknown-act-key]
test_t3_invalid_json_without_drawing[unknown-group-key]
test_t3_invalid_json_without_drawing[unknown-definition-key]
test_t3_invalid_json_without_drawing[invalid-anchor]
test_t3_invalid_json_without_drawing[absent-anchor]
test_t3_invalid_json_without_drawing[nonunique-anchor]
test_t3_invalid_json_without_drawing[story-path]
test_t3_invalid_json_without_drawing[percent]
test_t3_invalid_json_without_drawing[group-percent]
test_t3_invalid_json_without_drawing[throughput]
test_t3_invalid_json_without_drawing[latency]
test_t3_invalid_json_without_drawing[assignment]
test_t3_invalid_json_without_drawing[duplicate-key]
test_t3_invalid_json_without_drawing[nan]
test_t3_invalid_json_without_drawing[infinity]
test_t3_invalid_json_without_drawing[negative-infinity]
test_t4_free_text_contract
test_t5_layout_rejects_overlap_and_escape[overlap]
test_t5_layout_rejects_overlap_and_escape[escape]
test_t6_publisher_rejects_collision_without_files
test_t7_cli_outputs_and_independent_hashes
test_t8_cli_rejects_invalid_prefix
```

直接runnerはpytest hooksを経由せず、親の受入全走を代替しません。

## 変異 anchor の一意性

`grep -F -c`で確認。M7は`-x`も指定しました。

| 変異 | anchor | 行 | 件数 |
|---|---|---:|---:|
| M1 | `state in STYLES` | 151 | 1 |
| M2 | `set(value) == set(expected.split())` | 53 | 1 |
| M3 | `def check_display_text(value, declared_ids):` | 73 | 1 |
| M4a | `def _intersection(left, right):` | 288 | 1 |
| M4b | `def _contains(outer, inner):` | 292 | 1 |
| M5 | `hashlib.sha256(raw).hexdigest()` | 368 | 1 |
| M6 | `return STYLES[state][:2]` | 185 | 1 |
| M7 | `    check_figure_layout(fig, layout)\n` | 389 | 1 |
| M8 | `_require(match is not None, "output prefix basename must start with fig<N><letters>_")` | 169 | 1 |

変異自体は未実走。静的にはM2の5ケースが受理集合変更を検出する構造となり、M3の対象にgroup-percentが加わります。

## 波及

所有外caller・consumer testの直接参照、今回に該当するplotting目録・横断schema検査は検索範囲で見つかりませんでした。共通autouse fixtureはsite判定入力を置換するもので、本生成器に直接依存しません。

JSON・docs・既存probe・共有fixtureは未変更。未追跡の追加は指定の`out-fix1/`。runnerは別途、ignoredなdispatch receiptを自動生成しました。

## 総括

指定4件の修正と生成器・全30ケースの直接実走を完了しました。9 anchorは全て一意です。commitは作成していません。