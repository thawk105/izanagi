## 変更一覧

新規2本のみを作成しました。既存ファイル・docs・output は編集せず、git add・commit は行っていません。親所有の results 稿は開始時から untracked でした。

生成器: [tools/plotting/plot_a1_sized_paired.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2775-fig9-impl/tools/plotting/plot_a1_sized_paired.py)

- 検査補助: `_require`:79、`_sha256`:84、`_number`:88、`_integer`:93、`_string`:97、`_close`:102、`_lane`:107、`_flags`:112、`_genome`:118。
- 読み込み・再計算・分類検算: `load_leaf`:122、`_load_leaf`:132。
- caption・作図: `_figure_number`:258、`_caption`:264、`_artist_series`:289、`make_figure`:298。
- レイアウト検査: `_intersection`:334、`_contains`:338、`check_figure_layout`:342。
- provenance・着地照合・保存・CLI: `build_provenance`:374、`validate_repo_closure`:391、`_publish_outputs`:415、`main`:449。

test: [orchestrator/tests/test_plot_a1_sized_paired.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2775-fig9-impl/orchestrator/tests/test_plot_a1_sized_paired.py)

- 補助関数: `_load_module`:23、`_hash`:35、`_write`:39、`_seal`:44、`_statistics`:53、`_fixture`:80、`_data`:128、`_change`:133、`_reject`:141、`_reject_changed`:151、`_provenance`:157。
- 指定24 test は次節に列挙。自走 harness `_run`:434。
- fixture は3 workload × 30対 × 2 arm。非対称な差を使い、mean→median 変異を検出できる形です。

## 実走結果

最終コードで次を実走しました。

```text
PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/tmp/t2775-mpl-cache PYTHONPATH=. python3 orchestrator/tests/test_plot_a1_sized_paired.py
```

**rc=0、23 passed / 0 failed / 1 skipped / 0 errors。**

以下の nodeid 接頭辞はすべて `orchestrator/tests/test_plot_a1_sized_paired.py::` です。

| node | 行 | 結果 |
|---|---:|---|
| test_fixture_has_production_shape_and_recomputes_statistics | 164 | passed |
| test_artist_series_equal_provenance_cells_and_leaf_statistics | 180 | passed |
| test_real_figure_passes_layout_check | 212 | passed |
| test_bbox_overlap_is_a_failure | 221 | passed |
| test_layout_failure_publishes_nothing | 232 | passed |
| test_caption_contains_fixed_literals_and_lane | 245 | passed |
| test_caption_avoids_forbidden_claims | 262 | passed |
| test_caption_figure_number_comes_from_prefix | 273 | passed |
| test_formal_true_is_rejected | 280 | passed |
| test_promotion_prohibited_false_is_rejected | 284 | passed |
| test_statistics_mismatch_is_rejected | 288 | passed |
| test_classification_mismatch_is_rejected | 293 | passed |
| test_pair_difference_mismatch_is_rejected | 298 | passed |
| test_leaf_hash_drift_is_rejected | 310 | passed |
| test_policy_hash_mismatch_is_rejected | 317 | passed |
| test_uncertified_arm_is_rejected | 327 | passed |
| test_variance_plan_breach_true_is_rejected | 332 | passed |
| test_provenance_binds_caption_source | 350 | passed |
| test_pinned_hashes_are_used_when_no_override | 365 | passed |
| test_pinned_input_hashes_match_results_document | 370 | passed |
| test_cli_writes_three_outputs_and_provenance_closure | 378 | passed |
| test_cli_rejects_prefix_without_fig_number | 403 | passed |
| test_real_leaf_loads_and_matches_results_document | 410 | passed |
| test_landed_fig9_repo_closure_and_caption_when_present | 422 | skipped |

skip は親所有の着地3成果物がまだ無いためです。tracked leaf を読む test は実走しています。CLI の不正 prefix に対する `[error]` は負例の期待出力です。

実データ生成も最終コードで実走しました。

```text
python3 tools/plotting/plot_a1_sized_paired.py /tmp/t2775-fig9-author/fig9_a1_balanced5_sized_attempt1
```

**rc=0**。PNG（90,710 bytes）、PDF（18,859 bytes）、provenance JSON（29,538 bytes）の3本を確認しました。`validate_repo_closure` も実走して通過し、PNG を目視確認しました。成果物は `/tmp` のみです。

provenance の値は稿 §2.1 と一致しました。

| workload | mean tps | h tps | B tps | classification |
|---|---:|---:|---:|---|
| write-heavy | 1591948.5 | 23911.502943472762 | 68795.219 | resolved-above-floor |
| balanced | 448830.1666666667 | 28351.599461068836 | 115876.89600000001 | resolved-above-floor |
| read-heavy | -576749.7666666667 | 32963.69867738655 | 310204.40199999994 | resolved-above-floor |

`tools/run_tests.py` 経由の統合実走、既存 consumer test 全体、変異 matrix の実走は未実施です。

## caption 全文

Figure 9. A-1 balanced five-rep paired comparison, sized run attempt-0001 (study paper-story-a1-20260901-balanced5-sized-v1; formal: false; promotion_prohibited: true; result_authority: sized-preregistered-descriptive-only). Columns: write-heavy (rr5, fixed10 minus no-backoff), balanced (rr50, fixed5 minus no-backoff), read-heavy (rr95, fixed2 minus no-backoff), each an independent campaign in its own job (job IDs, respectively: 4939.nqsv, 4940.nqsv, 4941.nqsv; hosts bnode107, bnode108, bnode109). What is drawn: 30 paired differences (variant minus baseline, one per pair index under the balanced five-rep schedule, ten-pair groups in the order A^5 B^5 B^5 A^5 or B^5 A^5 A^5 B^5) as open markers; the arithmetic mean as a solid line with the registered interval mean ± h, h = k·s/√n, k = 2.8315526875186725 (t quantile at 1 − (1/120)/2 with df 29), s the sample standard deviation of the 30 differences; the zero line; and the registered floor boundary ±B, B = 3 % of the baseline-arm mean, as dashed lines. M tps means million transactions per second. Values: write-heavy mean +1.592 M tps (h 0.024 M, B 0.069 M, baseline mean 2.293 M); balanced mean +0.449 M tps (h 0.028 M, B 0.116 M, baseline mean 3.863 M); read-heavy mean -0.577 M tps (h 0.033 M, B 0.310 M, baseline mean 10.340 M). The registered classification is resolved-above-floor in all three workloads (sign positive, positive and negative, respectively); variance_plan_breach is false in all three. The interval and the classification are the descriptive outputs of the preregistered rule; they are not a hypothesis test and are not a performance certification. This figure reports a single attempt of a non-certified lane: it is not a headline value, no cross-workload conclusion is drawn (preregistration section 7.2), it is not a reproduction of C1, and one attempt does not speak to stability across repeated attempts. Conditions: Pegasus compute nodes, 48 threads, 1,000,000 records, Zipf 0.9, read-modify-write disabled, max operations 10, 3 s per repetition, 30 pairs per workload, silo, CCBench pin 511c953, measurement source commit d2ebef7a4, no perf, trace-disabled performance. Correctness comes from separate trace-enabled verify runs under the recorded legacy check configuration, not the performance configuration: all 6 arms are recorded as certified (result.json correctness_evidence, verify_done frames bound by SHA-256); certified means serializability of the observed YCSB point read/write traces under that check configuration and nothing beyond, and this is not a performance certification. Panel y scales are workload-local and must not be compared across panels. Pilot observations did not enter the estimate; the estimand is the difference under the balanced five-rep schedule, not a carryover-free steady-state effect.

## 波及の静的列挙

- **所有外 caller・共有 fixture:** 既存生成器を import せず、共有 fixture・conftest を変更していません。test は既存 `skiputil` を読み、実 policy を一時 repo に複製します。
- **`test_plain_runner_coverage.py`:** 新しい test file は走査対象になります。`__main__` → `_run()` を備え、既存検査の harness signal に適合することを確認しました。allowlist 追加は不要です。
- **`orchestrator/tests/README.md` の制約:** pytest 専用化・parametrize・疑似 pass による skip はありません。着地物不在は `Skip` として計数します。`test_skip_classification.py` の指定既存 node・consumer 集合は変更していません。
- **`test_official_perf_closure.py`:** 新生成器は `tools/` 走査対象です。同ファイルの `_python_has_perf_predicate` と依存定義を抽出して新ソースへ適用し、**False** を確認しました。`performance_trace0_evidence` は読みません。
- **`tools/check_docs.py`:** 今回 docs 自体の変更はありません。新生成器・test は親の results 稿が既に参照する path です。作図 README、figures README、最終成果物の追加は親の統合対象です。checker 全体は未実走です。
- **着地後の依存:** 稿または生成器を変更すると着地 closure が拒否するため、確定 bytes で図を再生成する必要があります。

## 受理集合の自己申告

**通常 CLI／hash override 無しの受理集合は裁定 §5 に収まります。**

4入力を固定 SHA-256 で限定し、study、lane、3 workload、30対、arm の成立条件、正しさ証拠、再計算統計、分類述語、variance plan を検査します。caption_source 不在も拒否します。

`expected_hashes` は指定された Python API の fixture 注入 seam にのみ存在し、CLI からは指定できません。既存 test の期待値・凍結入力は変更していません。

## 変異 matrix の anchor

以下の `G` は `tools/plotting/plot_a1_sized_paired.py`、test node の接頭辞は `orchestrator/tests/test_plot_a1_sized_paired.py::` です。**kill は予想であり、変異自体は未実走です。**

| ID | 対象 file:line | 逐語 anchor | 予想する test node |
|---|---|---|---|
| M0 | G:449 | `def main(argv=None, *, expected_hashes=None):` | 無変異。指定24件中23 passed・着地1件 skipped |
| M1 | G:108 | `_require(record["formal"] is False, "formal must be false")` | `test_formal_true_is_rejected` |
| M2 | G:109 | `_require(record["promotion_prohibited"] is True, "promotion_prohibited must be true")` | `test_promotion_prohibited_false_is_rejected` |
| M3 | G:225 | `for key, field in STAT_FIELDS.items():`<br>`    _close(stat[field], values[key])` | `test_statistics_mismatch_is_rejected` |
| M4 | G:234 | `_require(stat["classification"] == expected_class, "classification mismatch")` | `test_classification_mismatch_is_rejected` |
| M5 | G:213 | `_require(d == v - b, "pair difference mismatch")` | `test_pair_difference_mismatch_is_rejected` |
| M6 | G:138 | `_require(digest == hashes[path], f"SHA-256 mismatch: {path}")` | `test_leaf_hash_drift_is_rejected` |
| M7 | G:342 | `def check_figure_layout(fig, axes):` | 関数を no-op 化 → `test_bbox_overlap_is_a_failure` |
| M8 | G:276 | `f"Figure {_figure_number(prefix)}. A-1 balanced five-rep paired comparison, sized run attempt-0001 (study {data['study_id']}; {FIXED_LANE}).",` | `{FIXED_LANE}` を除去 → `test_caption_contains_fixed_literals_and_lane` |
| M9 | G:193 | `_require(type(evidence["certified"]) is list and len(evidence["certified"]) == 1`<br>`         and evidence["certified"][0] is True, "uncertified arm")` | `test_uncertified_arm_is_rejected` |
| M10 | G:157 | `_require(result["policy_sha256"] == _sha256(root / POLICY_PATH), "policy SHA-256 mismatch")` | `test_policy_hash_mismatch_is_rejected` |
| M11 | G:290 | `return [{"workload": c["workload"], "mean": c["mean"] / 1e6,` | mean 式を対差の median `/ 1e6` に変更 → `test_artist_series_equal_provenance_cells_and_leaf_statistics` |
| M12 | G:140 | `tracked.append({"kind": "caption_source", "path": CAPTION_SOURCE,`<br>`                "sha256": _sha256(root / CAPTION_SOURCE), "authority_scope": CAPTION_SCOPE})` | この append を除去 → `test_provenance_binds_caption_source` |

単一理由性のため、M3 は記録 mean だけを変更し、M5 は variant の raw と pair を同時変更して差だけを不整合にしています。M6 は completion の空白だけを変更し、M10 は result と receipt の policy hash を同じ偽値へ揃えています。

## 総括

author 所有の2本を実装し、自走 harness **23 passed / 1 skipped**、実データ生成 **rc=0・3成果物あり**、稿の数値照合と `/tmp` 成果物の closure 通過を確認しました。

親側のレビュー、統合 runner、変異 matrix、稿確定後の再生成・着地が残っています。