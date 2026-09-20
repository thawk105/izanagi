## 所見ごとの対応表

略号：G＝`tools/plotting/plot_k2_loop_flow.py`、J＝`tools/plotting/k2_loop_flow_2026-09-20.json`、T＝`orchestrator/tests/test_plot_k2_loop_flow.py`。test nodeid の接頭辞は `T::`。

| 所見 | 状態 | 対応箇所・検証 |
|---|---|---|
| F-M1 | closed | G:`EXPECTED_ARROWS`／`load_flow`／`_caption`／`CAPTION`。回数語生成を廃止し指定文へ。T:`test_t3_frozen_arrow_paths_are_required[destination]`、`test_t7_arrows_bind_artists_and_caption` |
| F-M2 | closed | G:`_reported_detection`／`_display_items`／`_caption`。coder 集約と全 role 集約を分離。T:`test_t7_discipline6_flip_changes_marker_and_items[coder/planner/critic]` |
| F-S1 | closed | G:`_display_items` の role cell を指定 template へ。T:`test_t7_drawn_items_match_flow`、反転検査 |
| F-S2 | closed | G:`_display_items` の proposal、J:lane-proposal.sublabel。T:`test_t7_drawn_items_match_flow` |
| F-S3 | closed | T:`RECORDED_PATHS` に独立した7組を手書き。`test_t1_real_flow_at_production_size`／`test_t7_cli_outputs_and_independent_hashes`／`test_t7_arrows_bind_artists_and_caption` で JSON・provenance と照合 |
| F-S4 | closed | G:`load_flow` で7組の完全一致を要求。T:`test_t3_frozen_arrow_paths_are_required[destination/missing/reordered]` |

caption の固定文1〜8の逐語検査を維持し、規律6の文だけ今回の裁定に合わせて更新しました。長くなった role cell の文字と marker の重なりは、折返し幅に marker 用余白を確保して解消しました。

## 実走した検査

指定 self-run：**109 passed／1 failed／0 skipped、18.10秒**。失敗は未着地の T9 だけです。全行 skipped は0件です。

| nodeid（T:: 以下） | passed | failed |
|---|---:|---:|
| `test_t1_real_flow_at_production_size` | 1 | 0 |
| `test_t2_tools_none_mismatch_is_rejected` | 3 | 0 |
| `test_t2_role_frontmatter_binding` | 5 | 0 |
| `test_t3_invalid_enum_is_rejected` | 6 | 0 |
| `test_t3_unknown_key_is_rejected` | 15 | 0 |
| `test_t3_invalid_json_without_drawing` | 44 | 0 |
| `test_t3_json_parser_rejects_noncanonical_values` | 4 | 0 |
| `test_t3_frozen_arrow_paths_are_required` | 3 | 0 |
| `test_t3_non_unique_anchor_is_rejected` | 1 | 0 |
| `test_t4_free_text_rejects_quantities` | 11 | 0 |
| `test_t4_declared_identifiers_are_accepted` | 1 | 0 |
| `test_t5_overlap_is_a_layout_error` | 1 | 0 |
| `test_t5_escape_is_a_layout_error` | 1 | 0 |
| `test_t5_arrow_crossing_text_is_a_layout_error` | 1 | 0 |
| `test_t6_publish_runs_layout_check` | 3 | 0 |
| `test_t7_cli_outputs_and_independent_hashes` | 1 | 0 |
| `test_t7_caption_source_hash_is_independent` | 1 | 0 |
| `test_t7_drawn_items_match_flow` | 1 | 0 |
| `test_t7_caption_verbatim_and_limits` | 1 | 0 |
| `test_t7_arrows_bind_artists_and_caption` | 1 | 0 |
| `test_t7_discipline6_flip_changes_marker_and_items` | 3 | 0 |
| `test_t8_cli_rejects_invalid_prefix` | 1 | 0 |
| `test_landed_fig12_bundle_when_present` | 0 | 1（期待赤） |

途中の初回実走は marker/text overlap により **0 passed／1 failed／0 skipped、2.96秒**。生成器の折返し幅を修正して上記結果になりました。

追加検査：

| 検査 | 結果 | 秒 |
|---|---|---:|
| `test_plain_runner_coverage.py::test_allowlist_has_no_stale_or_self_runnable_entries` | passed | |
| 同 `::test_every_test_file_is_self_runnable_or_allowlisted` | passed | |
| 同 `::test_this_metatest_is_itself_self_runnable` | passed。合計3 passed／0 failed／0 skipped | 0.84 |
| `check_subprocess_bytecode_guard.py --repo …/k2fig12-unit` | rc=0、違反なし | 22.85 |
| 実データ CLI | rc=0、PNG／PDF／provenance 生成 | 4.86 |
| `git diff --check` | rc=0 | — |

生成前に指定 scratch 3 path を `unlink(missing_ok=True)` で削除処理しました。出力は `probe-k2fig12/fig12_k2_manual_loop_dataflow.{png,pdf,provenance.json}`。PNG 目視済みです。

provenance の **caption 全文**：

```text
Figure 12. Data flow of the K2 manual synthesis loop over three recorded rounds, read from the frozen results note 2026-09-20-k2-manual-loop-three-rounds.md. In each round the parent session projects typed JSON inputs (planner: current_perf, leading_indicators, whiteboard, knowledge_input; coder: baseline, planner_direction, whiteboard, knowledge_input, leakproof_context) to planner-v4 and coder-v4-autonomous-k2; the proposal is one backoff literal evaluated by one Pegasus compute-node job with separate trace-enabled verify and trace-disabled bench builds and a campaign WAL terminal record; critic reads the digest and the WAL. Measurement reflux occurred twice between the recorded rounds (the first evaluation into the second proposal inputs; the second evaluation into the inputs of an unevaluated proposal and of the third round), and diagnosis reflux occurred once (the second critic into the third-round inputs as the typed key k2_critic_diagnosis with fields attribution, recommend, avoid, uncertainty, data_boundary, source_sha256, identical for planner and coder). Three measurement arrows are drawn because the second evaluation feeds both the unevaluated proposal and the third-round proposal; three dotted arrows mark absent paths. The unevaluated proposal, generated without a diagnosis key, re-proposed a known value. The planner and coder role definitions declare no tools (structural blockade); critic is a legacy role with Bash access, so these rounds are not material for the B-4 leak-control ablation. Certified means only that the trace-enabled verify run found the observed trace serializable with no anomaly; it is not a performance certification and not a choice among candidates. Discipline-six marks are role self-reports that external inputs contained no instruction-like strings; none is reported in the recorded rounds. Their form differs by role and they are not a mechanical gate. No causal effect of the knowledge source or of the diagnosis on the proposed values is claimed: each condition was launched once, without a control. The same-job stock control was not achieved and awaits a ruling; proposal values are backoff literals, not results. This is a schematic of recorded data flow; no performance values are drawn and the three runs are not compared. Role launch times, inline delivery, proposal dates, and the fine ordering of steps rest on each round's records; saved prompts and inputs are not proof of delivery. This figure does not judge whether B-6 is met; the tool-less declaration concerns tool access only, and leak control is not complete.
```

fix1 報告から変わった **drawn_items 17行**：

```text
lane-proposal | Proposal file a backoff hole literal; run-card known-value re-proposals are recorded, not counted as new values
round-1.planner | planner-1 decrease / medium instruction-like content: none detected (self-report)
round-1.coder | coder-1 synthesizes one backoff literal instruction-like content: none detected (self-report)
round-1.proposal | proposal-1 backoff literal 20 in the run-card known set evaluated re-proposal of a known literal, evaluated under the round authorization
round-1.critic | critic-1 not attributable to any design choice same-campaign stock control first (R0) instruction-like content: none detected (self-report)
round-2.planner | planner-2 decrease / small instruction-like content: none detected (self-report)
round-2.coder | coder-2 synthesizes one backoff literal instruction-like content: none detected (self-report)
round-2.proposal | proposal-2 backoff literal 25 outside the run-card known set evaluated submitted for evaluation
round-2.critic | critic-2 not attributable; runs are not contemporaneous decrease, large; same-job stock control first (R0) instruction-like content: none detected (self-report)
after-round-2.planner | planner-3 decrease / medium instruction-like content: none detected (self-report)
after-round-2.coder | coder-3 synthesizes one backoff literal instruction-like content: none detected (self-report)
after-round-2.proposal | proposal-3 backoff literal 20 in the run-card known set not evaluated re-proposal of a known literal; not evaluated by ruling
round-3.planner | planner-4 decrease / large instruction-like content: none detected (self-report)
round-3.coder | coder-4 synthesizes one backoff literal instruction-like content: none detected (self-report)
round-3.proposal | proposal-4 backoff literal 10 outside the run-card known set evaluated matches diagnosis candidate (self-reported advice, not causation)
round-3.critic | critic-3 not attributable again same-job stock control first (R0) instruction-like content: none detected (self-report)
legend-r6 | R6: self-reported; shield: none detected; red X: detected. data-boundary check: role self-report; planner in uncertainty prose, critic in a trust-boundary section; not a mechanical gate; coder: structured field data_boundary_report.instruction_like_content_detected: false in all four coder outputs; no role reported detection
```

## 変異 anchor の維持

列挙された anchor は**すべて現物に維持**しています。旧→新の変更はありません。

- `_enum`／`_keys`／`check_display_text`／`_intersection`／`_contains`／`_segment_intersects_box` は関数本文が HEAD と同一。
- `caption_source=dict(path=SOURCE,sha256=by_path[SOURCE])`、`tools_none mismatch` の行は存続。
- `_publish_outputs` の `check_figure_layout(fig, layout)` は存続。
- `_figure_number` の `_require(match is not None, ...)`、`_anchor` の `== 1`、`_drawn_items` の照合は関数本文ごと不変。
- `discipline6 form mismatch` の行、marker の `'X' if ... else 'p'` 式は存続。

反転 test は parametrize したため、親の M11b は従来の関数 nodeid、または `[coder]` を指定できます。変異実走は行っていません。

## 所有外への波及

無し。開始時の `git status --short` は空、終了時は指定3ファイルの変更と scratch の3成果物だけでした。禁止された git 操作、docs 編集、`tools/run_tests.py`、`python -m pytest` は実行していません。

## 総括

実装済み：採用6項目すべて closed、指定3ファイルと scratch 3成果物。
検査：109 passed／1 failed／0 skipped、18.10秒。追加検査・実データ生成も成功。
期待赤：`test_landed_fig12_bundle_when_present`（未着地）。
未実走：登録変異14件、親の着地・受入検査。
親への依頼：変異・受入確認、docs着地、commitをお願いします。