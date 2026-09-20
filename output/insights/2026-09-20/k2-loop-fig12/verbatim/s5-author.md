## 実装した物

- `tools/plotting/plot_k2_loop_flow.py`：閉じた schema、重複 key・非有限値・自由文数量の拒否、anchor 一意性、role frontmatter 束縛を実装。16×11 inch・200 dpi、4列×6 lane、3種の還流矢印、R6 marker、stock 未達枠を描画します。保存前に Text・領域・marker・矢印線分の交差を検査し、3成果物を上書き禁止で公開します。
- `tools/plotting/k2_loop_flow_2026-09-20.json`：稿から転記した既定入力。性能値は含めず、提案 literal・job ID・日付は型付き field に保持しています。
- `orchestrator/tests/test_plot_k2_loop_flow.py`：T1〜T9、実 JSON fixture、実 Figure の負例、独立 hash・全文字列照合、CLI 実走、self-run harness を実装。
- `probe-k2fig12/`：実データの scratch 成果物。untracked のままです。

provenance の key は `schema, generated_utc, figure_created, caption_source, inputs, generator, outputs, drawn_items, arrows, roles, caption, argv, versions`。caption は構造 field から決定的に組み立て、指定6文を逐語で含みます。

配置上、未評価列にも入力 key を収めるため4列を等幅にしました。長い矢印ラベルは格子下の専用領域に置き、ID・始点・終点を併記しています。

## 実走した検査

自走 harness：**76 passed / 1 failed / 0 skipped、8.66秒**。失敗は未着地の T9 のみです。

以下の nodeid はすべて `orchestrator/tests/test_plot_k2_loop_flow.py::` 配下です。括弧内は parameter 展開後の件数です。

| nodeid | 結果 |
|---|---:|
| `test_t1_real_flow_at_production_size` | 1 passed |
| `test_t2_tools_none_mismatch_is_rejected` | 3 passed |
| `test_t2_role_frontmatter_binding` | 5 passed |
| `test_t3_invalid_enum_is_rejected` | 6 passed |
| `test_t3_unknown_key_is_rejected` | 15 passed |
| `test_t3_invalid_json_without_drawing` | 20 passed |
| `test_t3_json_parser_rejects_noncanonical_values` | 4 passed |
| `test_t3_non_unique_anchor_is_rejected` | 1 passed |
| `test_t4_free_text_rejects_quantities` | 11 passed |
| `test_t4_declared_identifiers_are_accepted` | 1 passed |
| `test_t5_overlap_is_a_layout_error` | 1 passed |
| `test_t5_escape_is_a_layout_error` | 1 passed |
| `test_t5_arrow_crossing_text_is_a_layout_error` | 1 passed |
| `test_t6_publish_runs_layout_check` | 1 passed |
| `test_t7_cli_outputs_and_independent_hashes` | 1 passed |
| `test_t7_caption_source_hash_is_independent` | 1 passed |
| `test_t7_drawn_items_match_flow` | 1 passed |
| `test_t7_caption_verbatim_and_limits` | 1 passed |
| `test_t8_cli_rejects_invalid_prefix` | 1 passed |
| `test_landed_fig12_bundle_when_present` | 1 expected failed |

追加検査：

- `test_plain_runner_coverage.py` の `test_allowlist_has_no_stale_or_self_runnable_entries`、`test_every_test_file_is_self_runnable_or_allowlisted`、`test_this_metatest_is_itself_self_runnable`：**3 passed / 0 failed / 0 skipped、0.26秒**。
- 探索で見つけた `test_pytest_collection_config.py::test_permanent_exclusion_table_has_no_other_verifier_or_oracle_tests`：実関数を直接実行し、**1 passed / 0 failed / 0 skipped、0.142秒**。
- `check_subprocess_bytecode_guard.py --repo …/k2fig12-unit`：**rc=0、違反0、23.51秒**。
- `compile(..., "exec")` による新規 Python 2ファイルの構文確認：通過。

実データ CLI：**rc=0**。成果物：

- `probe-k2fig12/fig12_k2_manual_loop_dataflow.png`
- `probe-k2fig12/fig12_k2_manual_loop_dataflow.pdf`
- `probe-k2fig12/fig12_k2_manual_loop_dataflow.provenance.json`

`caption_source.sha256` は `sha256sum`・独立 hashlib の双方と一致：

```text
1b0f6f568f17af4967362cb864a14c18ef9220f826e257c113da0065bb512758
```

role の現物照合もすべて一致：

| role | tools_none | SHA-256 |
|---|---|---|
| planner-v4 | true | `8e2a0285419aea41e7cbba6f479a1d5b4d62f7488752975c98a396ba976d1027` |
| coder-v4-autonomous-k2 | true | `5d730eeaf09b639ef146157e6a7fe4786e79ace60af3de5c15bb23a16bf9e427` |
| critic | false | `fea81c65909aa9026b8fda1bf9b4768b38185dfd9327cff86a8bcef844504c1b` |

`drawn_items` 全文（折返しは空白に正規化）：

```text
title | K2 manual loop: data flow over three recorded rounds (schematic; no performance values)
subtitle | 2026-09-20-k2-manual-loop-three-rounds.md | 2026-09-20
knowledge | K2 knowledge source (identical source bytes in all rounds) a measurement WAL from another machine; manifest receipt verified inside the job; declared as data, not instructions
lane-parent | Parent session: typed projection builds input JSON; full inline sending and login preflight checks according to round records
lane-planner | planner-v4 tools: [] (structural blockade); outputs direction and magnitude, no value, no mechanism
lane-coder | coder-v4-autonomous-k2 tools: [] (structural blockade); outputs a backoff literal and self-reports knowledge use and data boundary
lane-proposal | Proposal file a backoff hole literal; known-value re-proposals are recorded, not counted as new values
lane-evaluation | Evaluation: Pegasus compute-node job separate trace-enabled verify and trace-disabled bench builds and runs; campaign WAL terminal record
lane-critic | critic legacy role with Bash; reads digest and WAL; not B-4 material
round-1 | Initial round proposal: 2026-09-16 evaluation: 2026-09-16
round-1.parent | planner: current_perf, leading_indicators, whiteboard, knowledge_input coder: baseline, planner_direction, whiteboard, knowledge_input, leakproof_context current_perf from the knowledge source's last bench record; whiteboard empty
round-1.planner | planner-1 decrease / medium
round-1.coder | coder-1 value 20
round-1.proposal | proposal-1 value 20 known value evaluated known value re-proposal, evaluated under the round authorization
round-1.evaluation | job 1216 verdict serializable; certified; no anomaly; stop: continue bnode host; legacy verify condition
round-1.critic | critic-1 not attributable to any design choice same-campaign stock control first ( R0 )
round-2 | Next round proposal: 2026-09-16 evaluation: 2026-09-18
round-2.parent | planner: current_perf, leading_indicators, whiteboard, knowledge_input coder: baseline, planner_direction, whiteboard, knowledge_input, leakproof_context current_perf and whiteboard from the previous evaluation
round-2.planner | planner-2 decrease / small
round-2.coder | coder-2 value 25
round-2.proposal | proposal-2 value 25 outside the known set evaluated outside the known set
round-2.evaluation | job 4954 refused at preflight: job 4947 verdict serializable; certified; no anomaly; stop: continue the refused submission did not reach the campaign
round-2.critic | critic-2 not attributable; runs are not contemporaneous decrease, large; same-job stock control first ( R0 )
after-round-2 | After evaluation (not a round) proposal: 2026-09-18 evaluation: none
after-round-2.parent | planner: current_perf, leading_indicators, whiteboard, knowledge_input coder: baseline, planner_direction, whiteboard, knowledge_input, leakproof_context same measurement as the next column; no diagnosis key (typed path not yet implemented)
after-round-2.planner | planner-3 decrease / medium
after-round-2.coder | coder-3 value 20
after-round-2.proposal | proposal-3 value 20 known value not evaluated known value re-proposal; not evaluated by ruling
after-round-2.evaluation | not evaluated
after-round-2.critic | no critic
round-3 | Final round proposal: 2026-09-19 evaluation: 2026-09-19
round-3.parent | planner: current_perf, leading_indicators, whiteboard, knowledge_input + k2_critic_diagnosis coder: baseline, planner_direction, whiteboard, knowledge_input, leakproof_context + k2_critic_diagnosis same measurement as the previous column, plus diagnosis from the previous critic verbatim
round-3.planner | planner-4 decrease / large
round-3.coder | coder-4 value 10
round-3.proposal | proposal-4 value 10 outside the known set evaluated outside the known set; matches diagnosis candidate (self-reported advice, not causation)
round-3.evaluation | job 10761 verdict serializable; certified; no anomaly; stop: continue same-job stock control not achieved
round-3.critic | critic-3 not attributable again same-job stock control first ( R0 )
arrow-m1 | m1: round-1.evaluation → round-2.parent measurement reflux: current_perf and whiteboard
arrow-m2a | m2a: round-2.evaluation → after-round-2.parent measurement reflux
arrow-m2b | m2b: round-2.evaluation → round-3.parent measurement reflux: current_perf and whiteboard
arrow-d1 | d1: round-2.critic → round-3.parent diagnosis reflux: typed path, identical for planner and coder k2_critic_diagnosis: attribution, recommend, avoid, uncertainty, data_boundary, source_sha256
arrow-a1 | a1: round-1.critic → round-2.parent no typed path: diagnosis not delivered
arrow-a2 | a2: round-2.critic → after-round-2.parent no diagnosis key
arrow-a3 | a3: round-3.critic → no destination no further proposal in the recorded scope
stock_control | same-job stock control not achieved; ruling pending ( T-2795 )
legend-arrows | Solid: measurement reflux; dashed: diagnosis reflux; dotted with cross: absent path; thin: within-column flow; dashed box: not a round.
legend-r6 | R6: no instruction-like content (self-reported). data-boundary check: role self-report that external input contained no instruction-like strings; coder as a structured field, planner in uncertainty prose, critic in a trust-boundary section; not a mechanical gate
footnote-source | Read from the frozen results note 2026-09-20-k2-manual-loop-three-rounds.md; no performance values are drawn and the three runs are not compared.
footnote-certified | Certified means the trace-enabled verify run found the trace serializable with no anomaly; it is not a performance certification.
footnote-discipline | Discipline-six marks are role self-reports, not a mechanical gate; causal effects of knowledge or diagnosis are not claimed.
```

## 稿との食い違い

- critic-1 の推奨は、下書きの `same-job` から稿の記述に合わせて `same-campaign` に修正。
- 知識源の `identical bytes` は source bytes に限定。role 入力 JSON 自体は key 順による bytes 差があるためです。
- 親の inline 送付・login preflight は稿の留保に合わせて `according to round records` を付記。
- `last record` は稿に合わせて `last bench record` に具体化。
- 自由文契約との整合のため、数詞を言い換え、列名を Initial／Next／After evaluation／Final としました。role 名と診断 key は型付き field／固定 template から描画し、`discipline-six check` は自由文で数詞に該当するため `data-boundary check` に変更しています。

## 未実走・期待赤

- `test_landed_fig12_bundle_when_present` は**未着地のため赤**。skip・xfail 化していません。
- 最終図の docs への生成、README 更新、変異実走、親の受入検査は未実施です。
- 指示どおり `tools/run_tests.py`・`python -m pytest`・git の変更操作は実行していません。
- PNG の目視確認は未実施です。

## 受理・拒否の含意

受理するのは、指定 schema・型・順序・相互整合を満たし、稿の anchor が一意で、role の宣言と現物が一致する転記 JSON です。

未知／不足／重複 key、不正 enum・数量表現・不整合・非一意 anchor・role 不一致を拒否し、描画後の交差や逸脱も公開前に拒否します。

通る正例は既定の `k2_loop_flow_2026-09-20.json` で、実データ CLI が3成果物を生成しました。

## 所有外への波及

既存 caller・共有 fixture・consumer の変更は無し。静的検索で生成器への参照は新規生成器と新規テストだけでした。

列挙型検査への追加対象は plain-runner、collection-config、subprocess bytecode guard で、該当検査を実走済みです。T9 は親が作成する図 bundle・figures README を参照します。

`git status --short` は所有する新規3ファイルと `probe-k2fig12/` のみでした。

## 変異事前登録への対応

nodeid の接頭辞はすべて `orchestrator/tests/test_plot_k2_loop_flow.py::` です。変異自体の実走は親へ引き継ぎます。

| ID | 変異位置 | kill 対応 test |
|---|---|---|
| M1 | `_enum` | `test_t3_invalid_enum_is_rejected` |
| M2 | `_keys` | `test_t3_unknown_key_is_rejected` |
| M3 | `check_display_text` | `test_t4_free_text_rejects_quantities` |
| M4a | `_intersection` | `test_t5_overlap_is_a_layout_error` |
| M4b | `_contains` | `test_t5_escape_is_a_layout_error` |
| M4c | `_segment_intersects_box` | `test_t5_arrow_crossing_text_is_a_layout_error` |
| M5 | `build_provenance` | `test_t7_caption_source_hash_is_independent` |
| M6 | `load_flow` の tools 比較 | `test_t2_tools_none_mismatch_is_rejected` |
| M7 | `_publish_outputs` | `test_t6_publish_runs_layout_check` |
| M8 | `_figure_number` | `test_t8_cli_rejects_invalid_prefix` |
| M9 | `_anchor` | `test_t3_non_unique_anchor_is_rejected` |
| M10 | `_drawn_items` | `test_t7_drawn_items_match_flow` |

単一理由性の注意：M1 の column-kind は enum 検査の後にも列位置との整合検査があります。membership だけを外しても後段が拒否します。direction／magnitude／arrow-kind／verdict／stop の負例は enum 検査を直接対象にできます。M4 の負例はそれぞれ期待する拒否理由まで照合しています。

## 総括

実装済み：新規3ファイル、scratch 3成果物、hash・role・表示文字列照合。
検査：76 passed、1 expected failed、0 skipped、8.66秒。meta 検査・bytecode guard・構文確認も通過。
期待赤：T9 は未着地のため赤。
未実走：目視、変異実走、最終着地・受入。
親への依頼：配置差分と PNG を確認し、scratch 退避、レビュー・変異、docs 着地をお願いします。