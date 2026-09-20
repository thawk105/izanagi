## 所見ごとの対応表

変更ファイルは次の3本と、untrackedの `probe-k2fig12/` 内3成果物です。

- G: `tools/plotting/plot_k2_loop_flow.py`
- J: `tools/plotting/k2_loop_flow_2026-09-20.json`
- T: `orchestrator/tests/test_plot_k2_loop_flow.py`

以下、test nodeidの接頭辞は `orchestrator/tests/test_plot_k2_loop_flow.py::` です。

| 所見 | 状態 | 対応箇所 |
|---|---|---|
| A-M1 | closed | Jのrole cellをtyped object化。G:`load_flow`、`_display_items`、`make_figure`。T:`test_t7_discipline6_flip_changes_marker_and_items`、`test_t3_invalid_json_without_drawing[discipline6-form]` |
| B-M1 | closed | columnのlabel削除・number追加。G:`load_flow`、`_display_items`、`make_figure`。T:`test_t7_drawn_items_match_flow` |
| B-M2 | closed | G:`load_flow`。T:`test_t3_invalid_json_without_drawing[not-a-round-kind/round-critic-null/round-date-null/diagnosis-column]`。各拒否文言も照合 |
| B-M3 | closed | T:`_moved_text`、`collision`。登録済みTextの文字列を保ち座標移動。`test_t6_publish_runs_layout_check[overlap/escape/arrow-crossing]` |
| A-S1 | closed | G:`CAPTION`に固定文7。T:`test_t7_caption_verbatim_and_limits` |
| A-S2 | closed | Jのrole sublabelをtool access限定へ変更。G:`CAPTION`に固定文8。同上test |
| A-S3／P1(b) | closed | G:`_display_items`、Jのproposal sublabel。literal表示はproposalだけ。T:`test_t7_drawn_items_match_flow` |
| A-S4／B-S3 | closed | G:`_drawn_arrows`、`_arrow_count_words`、`_caption`、`build_provenance`、`_publish_outputs`。T:`test_t7_arrows_bind_artists_and_caption`。件数指定の差は下記 |
| B-S1 | closed | T5の空tmp検査を削除し、T6を3種へ拡張 |
| B-S2 | closed | G:`_display_items`の凡例にfield名とtyped bool由来の集約表示。T:`test_t7_drawn_items_match_flow`、`test_t7_discipline6_flip_changes_marker_and_items` |
| B表の負例不足 | closed | T:`test_t3_invalid_json_without_drawing`へschema、日付、reference、順序、path、flags、重複、null等の負例を追加 |
| A-nit1 | closed | G:`make_figure`、`check_figure_layout`からneutral分岐・tuple要素を削除 |
| A削除候補 | closed | Jのrole laneをid/source_anchorだけに。G:`load_flow`の重複一致検査削除、`_display_items`でrolesから導出 |
| 親目視：列見出し | closed | typed numberからRound／After roundを生成 |
| 親目視：括弧 | closed | G:`check_display_text`と使用ID検査で`()[].:`をstrip。Jを`(R0)`／`(T-2795)`へ |
| 親目視：a3 | closed | G:`make_figure`で幅0.02の水平stub＋×。T:`test_t7_arrows_bind_artists_and_caption` |
| 親目視：R6 marker | closed | 右上、markersize 7、false=p／true=赤X。T:`test_t7_discipline6_flip_changes_marker_and_items` |
| 親目視：副題 | closed | 指定templateへ変更。T:`test_t7_drawn_items_match_flow` |
| 親目視：round-1評価 | closed | Jのsublabelを`legacy verify condition`へ |
| 親目視：parent説明 | closed | Jを指定文言へ変更 |
| 親目視：lane高さ | closed | parent .115、proposal .068、evaluation .083、critic .079。layout検査通過、PNG目視済み |

**仕様差が1点あります。** 今回の検査欄はmeasurement-reflux **2本**ですが、段4・現JSON・既存T1は **3本**（m1、m2a、m2b）です。経路とT1の期待値を維持しました。captionはJSONから「還流元の評価で数えてtwice」「描画経路はthree times」を生成します。したがって、検査欄の「2本」への一致だけはpartialです。

## 実走した検査

最終self-run：**104 passed / 1 failed / 0 skipped、16.59秒**。失敗は未着地T9だけです。

| nodeid | passed | failed |
|---|---:|---:|
| `test_t1_real_flow_at_production_size` | 1 | 0 |
| `test_t2_tools_none_mismatch_is_rejected[0/1/2]` | 3 | 0 |
| `test_t2_role_frontmatter_binding` | 5 | 0 |
| `test_t3_invalid_enum_is_rejected` | 6 | 0 |
| `test_t3_unknown_key_is_rejected` | 15 | 0 |
| `test_t3_invalid_json_without_drawing` | 44 | 0 |
| `test_t3_json_parser_rejects_noncanonical_values` | 4 | 0 |
| `test_t3_non_unique_anchor_is_rejected` | 1 | 0 |
| `test_t4_free_text_rejects_quantities` | 11 | 0 |
| `test_t4_declared_identifiers_are_accepted` | 1 | 0 |
| `test_t5_overlap_is_a_layout_error` | 1 | 0 |
| `test_t5_escape_is_a_layout_error` | 1 | 0 |
| `test_t5_arrow_crossing_text_is_a_layout_error` | 1 | 0 |
| `test_t6_publish_runs_layout_check[overlap/escape/arrow-crossing]` | 3 | 0 |
| `test_t7_cli_outputs_and_independent_hashes` | 1 | 0 |
| `test_t7_caption_source_hash_is_independent` | 1 | 0 |
| `test_t7_drawn_items_match_flow` | 1 | 0 |
| `test_t7_caption_verbatim_and_limits` | 1 | 0 |
| `test_t7_arrows_bind_artists_and_caption` | 1 | 0 |
| `test_t7_discipline6_flip_changes_marker_and_items` | 1 | 0 |
| `test_t8_cli_rejects_invalid_prefix` | 1 | 0 |
| `test_landed_fig12_bundle_when_present` | 0 | 1（期待赤） |

途中のself-runは、1 failed／2.56秒、93 passed・1 failed／4.45秒でした。前者はlabel bankと凡例の重なりを実装側で修正、後者はarrow-crossing fixtureのmarker接触を座標変更で除去しました。その後の再走は104 passed・T9のみfailed／13.18秒、14.91秒です。期待値の緩和・skip・xfail化はしていません。

追加検査：

| 検査 | 結果 | 所要秒 |
|---|---|---:|
| `test_plain_runner_coverage.py::test_allowlist_has_no_stale_or_self_runnable_entries` | passed | |
| 同`::test_every_test_file_is_self_runnable_or_allowlisted` | passed | |
| 同`::test_this_metatest_is_itself_self_runnable` | passed。計3 passed／0 failed／0 skipped | 0.45 |
| `test_pytest_collection_config.py::test_permanent_exclusion_table_has_no_other_verifier_or_oracle_tests` | 実関数直接実行、1 passed／0 failed／0 skipped | 0.428 |
| `check_subprocess_bytecode_guard.py --repo …/k2fig12-unit` | rc=0、違反なし | 29.17 |
| 実データCLI | rc=0、PNG／PDF／provenance生成 | 5.31 |

実データ出力は `probe-k2fig12/fig12_k2_manual_loop_dataflow.{png,pdf,provenance.json}`。最終生成前に既存scratchの3ファイルを削除しました。

`caption_source.sha256` は独立hashlib照合で一致：

```text
1b0f6f568f17af4967362cb864a14c18ef9220f826e257c113da0065bb512758
```

arrowsは **measurement-reflux 3／diagnosis-reflux 1／absent 3**。measurementの異なるfromは2件です。生成器・PNG・PDFの記録hashも現物と一致しました。

drawn_items全50件：

```text
title | K2 manual loop: data flow over three recorded rounds (schematic; no performance values)
subtitle | Source: frozen results note 2026-09-20-k2-manual-loop-three-rounds.md (SHA-256 in provenance); figure created 2026-09-20
knowledge | K2 knowledge source (identical source bytes in all rounds) a measurement WAL from another machine; manifest receipt verified inside the job; declared as data, not instructions
lane-parent | Parent session: typed projection builds the planner and coder input JSON, sends the full JSON inline, runs preflight checks on the login node (per round records)
lane-planner | planner-v4 no tool access (structural blockade of tool use); outputs direction and magnitude, no value, no mechanism
lane-coder | coder-v4-autonomous-k2 no tool access (structural blockade of tool use); outputs a backoff literal and self-reports knowledge use and data boundary
lane-proposal | Proposal file a backoff hole literal; known-value re-proposals are recorded, not counted as new values
lane-evaluation | Evaluation: Pegasus compute-node job separate trace-enabled verify and trace-disabled bench builds and runs; campaign WAL terminal record
lane-critic | critic legacy role with Bash; reads digest and WAL; not B-4 material
round-1 | Round 1 proposal 2026-09-16 (per round records) · evaluation 2026-09-16 (job log)
round-1.parent | planner: current_perf, leading_indicators, whiteboard, knowledge_input coder: baseline, planner_direction, whiteboard, knowledge_input, leakproof_context current_perf from the knowledge source's last bench record; whiteboard empty
round-1.planner | planner-1 decrease / medium data boundary: none detected
round-1.coder | coder-1 synthesizes one backoff literal data boundary: none detected
round-1.proposal | proposal-1 backoff literal 20 known evaluated re-proposal of a known literal, evaluated under the round authorization
round-1.evaluation | job 1216 verdict serializable; certified; no anomaly; stop: continue legacy verify condition
round-1.critic | critic-1 not attributable to any design choice same-campaign stock control first (R0) data boundary: none detected
round-2 | Round 2 proposal 2026-09-16 (per round records) · evaluation 2026-09-18 (job log)
round-2.parent | planner: current_perf, leading_indicators, whiteboard, knowledge_input coder: baseline, planner_direction, whiteboard, knowledge_input, leakproof_context current_perf and whiteboard from the previous evaluation
round-2.planner | planner-2 decrease / small data boundary: none detected
round-2.coder | coder-2 synthesizes one backoff literal data boundary: none detected
round-2.proposal | proposal-2 backoff literal 25 not known evaluated submitted for evaluation
round-2.evaluation | job 4954 refused at preflight: job 4947 verdict serializable; certified; no anomaly; stop: continue the refused submission did not reach the campaign
round-2.critic | critic-2 not attributable; runs are not contemporaneous decrease, large; same-job stock control first (R0) data boundary: none detected
after-round-2 | After round 2 (not a round) proposal 2026-09-18 (per round records) · evaluation: none
after-round-2.parent | planner: current_perf, leading_indicators, whiteboard, knowledge_input coder: baseline, planner_direction, whiteboard, knowledge_input, leakproof_context same measurement as the next column; no diagnosis key (typed path not yet implemented)
after-round-2.planner | planner-3 decrease / medium data boundary: none detected
after-round-2.coder | coder-3 synthesizes one backoff literal data boundary: none detected
after-round-2.proposal | proposal-3 backoff literal 20 known not evaluated re-proposal of a known literal; not evaluated by ruling
after-round-2.evaluation | not evaluated
after-round-2.critic | no critic
round-3 | Round 3 proposal 2026-09-19 (per round records) · evaluation 2026-09-19 (job log)
round-3.parent | planner: current_perf, leading_indicators, whiteboard, knowledge_input + k2_critic_diagnosis coder: baseline, planner_direction, whiteboard, knowledge_input, leakproof_context + k2_critic_diagnosis same measurement as the previous column, plus diagnosis from the previous critic verbatim
round-3.planner | planner-4 decrease / large data boundary: none detected
round-3.coder | coder-4 synthesizes one backoff literal data boundary: none detected
round-3.proposal | proposal-4 backoff literal 10 not known evaluated matches diagnosis candidate (self-reported advice, not causation)
round-3.evaluation | job 10761 verdict serializable; certified; no anomaly; stop: continue same-job stock control not achieved
round-3.critic | critic-3 not attributable again same-job stock control first (R0) data boundary: none detected
arrow-m1 | m1: round-1.evaluation → round-2.parent measurement reflux: current_perf and whiteboard
arrow-m2a | m2a: round-2.evaluation → after-round-2.parent measurement reflux
arrow-m2b | m2b: round-2.evaluation → round-3.parent measurement reflux: current_perf and whiteboard
arrow-d1 | d1: round-2.critic → round-3.parent diagnosis reflux: typed path, identical for planner and coder k2_critic_diagnosis: attribution, recommend, avoid, uncertainty, data_boundary, source_sha256
arrow-a1 | a1: round-1.critic → round-2.parent no typed path: diagnosis not delivered
arrow-a2 | a2: round-2.critic → after-round-2.parent no diagnosis key
arrow-a3 | a3: round-3.critic → no destination no further proposal in the recorded scope
stock_control | same-job stock control not achieved; ruling pending (T-2795)
legend-arrows | Solid: measurement reflux; dashed: diagnosis reflux; dotted with cross: absent path; thin: within-column flow; dashed box: not a round.
legend-r6 | R6: self-reported; shield: none detected; red X: detected. data-boundary check: role self-report; planner in uncertainty prose, critic in a trust-boundary section; not a mechanical gate; coder: structured field data_boundary_report.instruction_like_content_detected; false in all recorded rounds
footnote-source | Read from the frozen results note 2026-09-20-k2-manual-loop-three-rounds.md; no performance values are drawn and the three runs are not compared.
footnote-certified | Certified means the trace-enabled verify run found the trace serializable with no anomaly; it is not a performance certification.
footnote-discipline | Discipline-six marks are role self-reports, not a mechanical gate; causal effects of knowledge or diagnosis are not claimed.
```

## 受理・拒否の含意

受理集合は、新しいtyped discipline6／numberと簡略化したrole laneのschemaへ移り、正しいformの検出trueや括弧付き宣言IDを表示へ反映して受理します。

旧schema、不正form／bool／number、kind別矢印件数が1〜3以外の入力、および描画矢印の欠落・不可視・入力との不一致は拒否します。

通る正例は更新済みの既定Jで、実データCLIがrc=0でした。

## 変異登録への対応

10群12変異＋M11群2変異＝**11群14変異**。以下は対応nodeidの存在・通常実装での通過確認であり、変異実走のKILLED報告ではありません。

| 変異 | 位置 | killするnodeid |
|---|---|---|
| M1 membership恒真 | G:`_enum` | `test_t3_invalid_enum_is_rejected[direction]` |
| M2 未知key許容 | G:`_keys` | `test_t3_unknown_key_is_rejected[top]` |
| M3 早期return | G:`check_display_text` | `test_t4_free_text_rejects_quantities[38%]` |
| M4a 常に0 | G:`_intersection` | `test_t5_overlap_is_a_layout_error` |
| M4b 常にTrue | G:`_contains` | `test_t5_escape_is_a_layout_error` |
| M4c 常にFalse | G:`_segment_intersects_box` | `test_t5_arrow_crossing_text_is_a_layout_error` |
| M5 別hash定数 | G:`build_provenance` | `test_t7_caption_source_hash_is_independent` |
| M6 tools比較恒真 | G:`load_flow` | `test_t2_tools_none_mismatch_is_rejected[0]` |
| M7 layout検査呼出し削除 | G:`_publish_outputs` | `test_t6_publish_runs_layout_check[overlap]` |
| M8 prefix述語恒真 | G:`_figure_number` | `test_t8_cli_rejects_invalid_prefix` |
| M9 anchor条件を>=1 | G:`_anchor` | `test_t3_non_unique_anchor_is_rejected` |
| M10 表示照合削除 | G:`_drawn_items` | `test_t7_drawn_items_match_flow` |
| M11a form不一致許容 | G:`load_flow` | `test_t3_invalid_json_without_drawing[discipline6-form]` |
| M11b markerを常にp | G:`make_figure` | `test_t7_discipline6_flip_changes_marker_and_items` |

M7 fixtureは文字列不変で、`_drawn_items`が通ることをfixture内で確認しています。登録対象について静的に残る複数拒否理由は見つかっていません。実際の変異による公開・kill確認は親へ引き継ぎます。

## 所有外への波及

無し。`git status --short`は指定3ファイルの変更と `?? probe-k2fig12/` だけでした。docs・既存共有test・role定義は編集していません。禁止されたgit操作、`tools/run_tests.py`、`python -m pytest`は実行していません。

## 総括

実装済み：段6採用項目、所有3ファイル、scratch3成果物、PNG目視。
検査：104 passed／T9のみ1 expected failed／0 skipped、16.59秒。追加検査も通過。
未実走：変異14件、親の着地・受入検査。
期待赤：`test_landed_fig12_bundle_when_present`（未着地）。
親への依頼：実測還流「2回／描画3本」の検査欄を整合させ、変異・docs着地・commitを実施してください。