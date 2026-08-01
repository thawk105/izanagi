N1〜N6 をすべて実装しました。docs、禁止ファイル、Git index、commit、branch には触れていません。pytest・mutation harness 本走は未実施で、緑は主張しません。

### N1〜N6 対応

| 項目 | 状態 | 対応 |
|---|---|---|
| N1 timeout 契約 | closed | 全 spec に `expect_timeout` を追加。false の timeout は abort。process group を TERM→KILL、dispatch log から request ID 捕捉、`qdel`、`qstat` 消滅照合後にだけ復元する。照合不能時は復元を保留して fail-closed |
| N2 mutation 意味論 | closed | M10 を production provider ごとの resolver 再実行へ再照準。M13 2件を `diagnostic-pin` とし、`DIAGNOSTIC-PINNED` で KILL 総数から分離 |
| N3 成功 consumer | closed | provider/run-level receipt を独立 deep copy。production `_run_workload` を通し、journal bytes と disk report cell を独立検査。M14-report-drop を追加 |
| N4 P1/P2 | closed | P1 を flag 省略 `run_trial` production E2E、I/O 0回、固定 clock・2走 byte比較へ変更。P2 を flag-on wrapper＋production provider＋実 subprocess E2Eへ変更 |
| N5 PBS grammar | closed | leaf 文法を qsub authority と逐語一致。consumer は leaf validator を参照。test が `qsub_binding` と `collector` を import して関係を固定 |
| N6 proxy preflight | closed | lowercase pair の存在・型を policy read 前へ移動。両 key の missing/non-string と壊れた reader の併存を reader 0回で固定 |

`partial`、`regressed` はありません。

### Root-cause 等価 mutant

- M10′: 検出可能。M10 自体を「各 production provider が別 resolver 結果を受け取る」変異へ変更し、production provider 4個を使う test に対応付けました。
- M14-report-drop: 検出可能。journal には receipt が残る一方、report の planner provenance だけから receipt を落とす変異を追加しました。
- P1′: 検出可能。flag-off E2E で admission、site resolver、policy reader を監視し、呼出し 0 回と決定的 journal/report bytes を確認する構造です。

いずれも静的検出予測であり、KILLED／POSITIVE-GREEN の実測主張ではありません。

### 変更ファイル

- [claude_transport.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/claude_transport.py:61): authority 同一 PBS pattern・共通 validator、lowercase pair pure preflight。
- [p3_autonomous_workload_trial.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:609): consumer 側の独自 PBS regex を廃止し leaf validator を参照。
- [test_claude_transport.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/tests/test_claude_transport.py:318): authority drift、N6、production M10、P1/P2、成功 journal/report consumer を強化。
- [mutate.py](/home/SFC/tanab/.claude/jobs/acef4d0f/tmp/t276-wave/mutate.py:115): timeout cleanup、scheduler cancel・消滅照合、diagnostic status、集計分離。
- [mutations.json](/home/SFC/tanab/.claude/jobs/acef4d0f/tmp/t276-wave/mutations.json): `kind`、`expect_timeout`、再照準 M10、M14-report-drop、本来の P1/P2。

所有外では qualification authority を test から読むだけで、production の qualification package 依存は増えていません。docs、`s8b_prediction_runner.py`、`s8b_selector_freeze.py`、`site_policy.py` に working-tree 差分はありません。段5の provider・policy・registry staged bytesにも今回の追加変更はありません。

### 更新後の M / P 対応

全24 non-positive entry の anchor は最終ソース上 `count=1`、全27 entry の nodeid は AST 上実在します。現 spec に timeout 期待の hang entry はないため、全 entry の `expect_timeout=false` です。

| Entry | 種別 | kill／維持 node |
|---|---|---|
| M1 | mutation | `test_rejects_non_compute_sites_and_wrapper_orders_io` |
| M2 | mutation | `test_rejects_each_tls_override_without_secret_disclosure` |
| M3 | mutation | `test_rejects_each_unadmitted_proxy_name_without_disclosure` |
| M4 | mutation | `test_rejects_missing_non_string_and_drifted_required_pair` |
| M5-leaf | mutation | `test_m5_leaf_preserves_distinct_http_and_https_values` |
| M5-provider | mutation | `test_m5_provider_real_subprocess_preserves_distinct_admitted_pair` |
| M6 | mutation | `test_reverse_endpoint_key_order_uses_literal_canonical_digest` |
| M7 | mutation | `test_rejects_pbs_job_witness_failures_without_disclosure` |
| M8 / M9 | mutation | `test_cli_flag_default_and_all_four_wiring_links_are_explicit` |
| M10 | mutation | `test_m10_real_providers_share_run_admission_without_resolving_per_role` |
| M11-invalid | mutation | `test_m11_invalid_attempt_keeps_same_receipt` |
| M11-init | mutation | `test_m11_provider_init_error_keeps_same_receipt` |
| M12-pre-open | mutation | `test_m12_pre_open_rejects_policy_symlink_before_open` |
| M12-post-open | mutation | `test_m12_post_open_rejects_controlled_regular_file_swap` |
| M13-leaf | diagnostic-pin | `test_m13_leaf_error_never_discloses_proxy_value` |
| M13-trial | diagnostic-pin | `test_m13_trial_error_redacts_endpoint_and_jobid` |
| M14-exact | mutation | `test_invoke_consumer_rejects_missing_extra_and_hash_receipts` |
| M14-success-reject | mutation | `test_success_consumer_keeps_valid_receipt_in_journal_and_report` |
| M14-success-drop | mutation | 同上 |
| M14-report-drop | mutation | 同上 |
| M14-opt-out | mutation | `test_opt_out_rejects_forged_provider_transport_receipt` |
| M15 | mutation | `test_committed_policy_matches_independent_literal_hash_and_registry` |
| M16 | mutation | `test_m16_rejects_each_metered_transport_key_by_presence` |
| P1 | positive | `test_p1_flag_omitted_run_trial_has_no_transport_io_or_fields` |
| P2 | positive | `test_p2_flag_on_run_trial_admits_compute_wrapper_with_real_providers` |
| P3 | positive | `test_p3_accepts_when_metered_transport_keys_are_absent` |

### 静的検査

- `py_compile`: production 2 file、test、harness 成功
- JSON parse: `mutations.json` 成功
- mutant 24件: メモリ上適用後の Python/JSON 構文検査成功
- spec: mutation 22、diagnostic-pin 2、positive 3
- anchor: non-positive 24件すべて一意
- nodeid: 全件実在、test 関数重複なし
- timeout log parser／qstat absence classifier: 静的 fixture 照合成功
- `git diff --check`／`--cached --check`: 成功
- `check_codex_agents.py`: rc=0
- `check_docs.py`: 違反なし
- pytest、plain runner、mutation harness: 未実施
- commit／stage／branch操作: 未実施

## 総括

N1〜N6 は実装面で closed です。KILL 対象22件、diagnostic pin 2件、正例3件へ整理し、M10′・M14-report-drop・P1′をそれぞれ production 経路で検出できる構造へ変更しました。次工程は親による計算ノード関連テスト、統合commit後の mutation harness、本受入全走です。