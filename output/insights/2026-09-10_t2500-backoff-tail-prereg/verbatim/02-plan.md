## プラン

変更対象は次の 2 ファイルだけとする。`orchestrator/`、`tools/`、`hooks/`、test、既存 spec、既存成果物 schema は変更しない。

- 新規 [docs/b10-backoff-static-tail-preregistration.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md)
- 地図への 1 項追加 [docs/README.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/README.md:28)

### 1. 新規事前登録の章立てと行配置

新規文書はおよそ 600 行とし、次の位置へ置く。

| 予定行 | 節 | 内容 |
|---:|---|---|
| L1〜L7 | 表題・位置づけ | B-10 の静的右 tail、本書が docs-only の前向き固定であること |
| L9〜L28 | §0 本書の効力 | v1、結果を見る前の commit で発効、結果後の変更は erratum のみ |
| L30〜L62 | §1 主張範囲 | 飽和位置または域内非飽和の限定主張、禁止する外挿と機序主張 |
| L64〜L110 | §2 探索結果の開示 | T-2418 の 3 点、3 workload の実測値、CV、格子と閾値を探索後に選んだ事実 |
| L112〜L166 | §3 本格格子 | 8 tail 点、1000 µs 境界参照、符号化値、探索 abscissa の再利用規則 |
| L168〜L210 | §4 反復数・動作点・時間枠 | workload、records、threads、extime、正しさ・性能各 5 rep、PBS 枠 |
| L212〜L310 | §5 飽和判定 | abort 率の log-log 傾き、同時区間、5%/倍増、連続 2 区間、非飽和結末 |
| L312〜L535 | §6 機械可読 spec | 下記 JSON をそのまま収録 |
| L537〜L552 | §7 検出力について主張しないこと | n=5 や CV gate を power guarantee と呼ばない |
| L554〜L604 | §8 失敗条件 | correctness、binary 完全性、欠測、CV、時間、非単調、途中終了 |
| L606〜L640 | §9 発効と後続 driver への束縛 | commit/spec の記録、新 identity、stem 非衝突、既存系列不変 |

### 2. 格子

同一 workload job 内の解析順を次で固定する。

```text
1000, 1414, 2000, 2828, 4000, 5657, 8000, 8944, 9999 µs
```

このうち 1000 µs は既存正式格子上端の境界参照で、本格 tail は次の 8 点である。

```text
1414, 2000, 2828, 4000, 5657, 8000, 8944, 9999 µs
```

規則は以下とする。

- 1000→8000 µs は半オクターブ、すなわち比 `sqrt(2)` の等比点を最も近い整数 µs へ丸める。
- 9999 µs は表現上限として必ず入れる。
- 8000→9999 の切れた最終区間には、その幾何平均を丸めた 8944 µs を 1 点だけ置く。これにより、上限直前にも「連続 2 区間」の飽和判定窓を持たせる。
- 解析は実際の `log(b_i / b_{i-1})` で正規化するため、最後の短い区間も半オクターブ区間と同じ「倍増あたり変化率」で比較できる。
- 追加点は設けない。通常域では半オクターブ、上限域では最終区間の二分で連続 2 区間を構成でき、それ以上は域内飽和の有無ではなく位置の細分化だけを行うためである。

物理値と raw 値は次で凍結する。

| 物理値 µs | `BACKOFF_FIXED` raw |
|---:|---:|
| 1000 | 3000 |
| 1414 | 3414 |
| 2000 | 4000 |
| 2828 | 4828 |
| 4000 | 6000 |
| 5657 | 7657 |
| 8000 | 10000 |
| 8944 | 10944 |
| 9999 | 11999 |

参照点は 1000 µs だけを含める。

- 1000 µs は tail の左境界を同一 job で測るため必須であり、過去の正式系列の数値は流用しない。
- backoff なしと adaptive は飽和述語へ入らないため除外する。特に既定 adaptive を単独基準線にする比較は定数差と機構差を分離しないという既知の問題がある。
- これにより 1 workload あたり 9 genome で閉じる。none/adaptive を足して 11 genome に増やさない。

探索の 2000 / 4000 / 9999 µs は abscissa として再利用する。ただし各点を本格 cohort で新しく 5 rep 測り、探索の測定値、分散、順位、途中成果物は正式推定へ一切混ぜない。D1813 が禁じるのは探索測定値の正式標本への混入であり、探索後に開示して格子位置を選ぶことではない。

### 3. 反復数と動作点

共有定数を参照せず、次の literal を本文と JSON の双方へ書く。

- workload:

  - `write-heavy`: zipf `0.9`、read ratio `5`、rmw `0`、max ope `10`
  - `balanced`: zipf `0.9`、read ratio `50`、rmw `0`、max ope `10`
  - `read-heavy`: zipf `0.9`、read ratio `95`、rmw `0`、max ope `10`

- `records = 1000000`
- `threads = 48`
- `extime_s = 3`
- 性能測定 `5 rep/cell`
- correctness `5 rep/cell`
- `correctness_mode = legacy+performance`
- 3 workload × 9 cell = 27 cell
- 性能、correctness とも期待反復総数は 135

共有定数を使わない理由は、生産コード、loader、test が同じ定数へ追随すると、裁定した値が変わっても全体が緑になり得るためである。文書の literal JSON を後続 driver の権威にする。

測定順も結果後に変えられないよう literal で固定する。

```text
write-heavy:
2828, 4000, 1414, 1000, 2000, 8944, 5657, 8000, 9999

balanced:
1414, 9999, 1000, 2828, 5657, 4000, 2000, 8000, 8944

read-heavy:
4000, 8000, 8944, 9999, 2828, 2000, 5657, 1414, 1000
```

これは既存 workload seed `0xB10005`、`0xB10050`、`0xB10095` を、昇順の上記 9 label に適用した順序である。spec では解決済み順序を権威とし、seed は provenance として併記する。

時間枠は次を固定する。

- workload ごとに 1 job、計 3 job。
- sweep の上限は `11700` 秒。
- PBS の予約は `18000` 秒。
- sweep timeout または PBS 途中終了は失敗条件。
- 実行時間を理由に rep や点を削らない。

実績上、8 genome × 5 rep の t2266 は build・verify・bench・commit を 11 分で完走し、5 genome の探索 3 job も投入から 18 分以内に全て完了している。予測所要を新たに捏造せず、この実績に対して十分大きい既存 cap を保持する。

### 4. 飽和判定

停止基準は測定を途中で止める規則ではなく、全 9 点の完走後に飽和位置を報告する規則と明記する。早期停止は禁止する。

主量は abort 率だけとする。throughput は過抑制の費用を示す必須併記量だが、飽和述語には入れない。

workload `w`、物理値 `b_i`、rep `r=1..5` の abort 率を `a_wir` とし、次を計算する。

```text
m_wi = (1/5) sum_r a_wir
s_wi = sample standard deviation of a_wir
cv_wi = s_wi / m_wi
v_wi = cv_wi^2 / 5

h_i = log(b_i / b_(i-1))
qhat_wi = log(m_wi / m_w(i-1)) / h_i
se_wi = sqrt(v_wi + v_w(i-1)) / h_i

nu_wi =
  (v_wi + v_w(i-1))^2
  / (v_wi^2/4 + v_w(i-1)^2/4)

qL_wi =
  qhat_wi
  - t_(1 - 0.05/24, nu_wi) * se_wi

U_wi = 1 - exp(qL_wi * log(2))
```

- `qhat <= 0` は backoff 増加に伴う abort 率の非増加を表す。
- `U` は、反復ばらつきを入れた「真の abort 率が backoff 倍増当たり最大で何割下がり得るか」の片側同時上限である。
- 3 workload × 各 8 隣接区間 = 24 比較へ Bonferroni を適用し、familywise alpha を `0.05` に固定する。
- 1 区間は `qhat <= 0` かつ `U <= 0.05` のときだけ飽和区間とする。
- 連続 2 区間がとも飽和区間なら、その中央の格子点を workload ごとの最初の飽和位置として報告し、外側 2 端点を位置 bracket として併記する。
- 全 3 workload に位置が得られた場合だけ「3 workload 全てで域内飽和」とする。
- 有効な全点を完走して該当する連続 2 区間が無ければ、「この事前登録述語では、表現可能域の 9999 µs までに飽和を観測しなかった」を正当な結末とする。

5% は「物理値を倍増しても abort 率の追加低下が最大 5%以下」を plateau と呼ぶ実用的等価幅である。探索後に選んだことを明記する。探索の最大 CV 0.65%に対して約 7.7 倍であり、探索で観測した大きな低下を無理に plateau と分類する閾値ではない。さらに同時区間と連続 2 区間を要求する。

CV は abort 率と throughput のそれぞれについて算出し、どちらかが `0.02` 以上なら cohort を formal claim に使わない。2% は探索最大 0.65%のおよそ 3 倍であり、5%幅より小さい。

ゼロ abort は次で閉じる。

- 隣接 2 cell がとも全 5 rep で abort 率 0: `qhat=qL=0`、`U=0`。
- 正値から全ゼロへ落ちる区間: 100%の改善なので飽和区間ではない。
- 全ゼロから正値へ上がる区間: 非単調。
- 一部 rep だけがゼロの場合は通常の平均と CV を計算する。CV gate を通らなければ失敗とする。

### 5. 失敗条件

次のいずれかが起きたら、登録した飽和または域内非飽和の主張には使わない。数値は失敗理由とともに全件を記述的に報告する。

1. 27 cell のどれかで trace-enabled correctness 5 rep が揃わない、`certified` でない、または anomaly が 1 件以上ある。
2. correctness 不合格 cell を bench へ到達させる。
3. 9 個の静的 amount に対応する trace-disabled `BuildResult` が完全に揃わない、canonical genome 束縛が違う、SHA-256 が完全長でない、または 2 amount が同じ binary SHA-256 になる。
4. workload、物理値、rep のいずれかが欠測、重複、非有限、範囲外、あるいは期待集合外である。
5. abort 率または throughput の cell CV が `0.02` 以上。
6. 同時下限 `qL > 0` となる隣接区間、すなわち統計的に支持された abort 率上昇が 1 区間でもある。この場合、単調 tail を前提とする飽和位置・域内非飽和の両主張を行わない。
7. `qhat > 0` だが `qL <= 0` の小さい揺れは失敗にせず、当該区間を飽和区間に数えず、そのまま開示する。
8. sweep が 11700 秒を超える、PBS 18000 秒内に `completion.json` まで到達しない、または job が途中終了する。
9. 途中終了後は、同一 campaign identity、同一 prereg commit/spec SHA、同一 source/toolchain 束縛の WAL resume だけを認める。別 campaign の cell を継ぎ合わせない。resume で全件完了しなければ失敗のままとする。
10. 探索測定値を formal rep、CV、区間、飽和判定へ混ぜる。
11. 文書 commit、文書 blob、spec SHA のいずれかを記録しない、または実行時 bytes と一致しない。

### 6. 機械可読 spec の完全な骨格

§6 に次を置く。実装前の placeholder や未定の identity 名は置かず、後続 wave が満たす関係を値として固定する。

<!-- IZANAGI-B10-STATIC-TAIL-SPEC-BEGIN -->
```json
{
  "schema_version": "izanagi-b10-backoff-static-tail-preregistration/v1",
  "preregistration": {
    "document_path": "docs/b10-backoff-static-tail-preregistration.md",
    "formal_run_must_record_containing_commit": true,
    "formal_run_must_record_document_blob_sha256": true,
    "formal_run_must_record_spec_sha256": true,
    "post_result_edits_count_as_preregistration": false
  },
  "study": {
    "formal": true,
    "claim_scope": "static-backoff-right-tail-abort-saturation-with-throughput-cost-context",
    "result_use_class": "formal-estimation",
    "performance_certification_claim": false,
    "physical_domain_us": {
      "lower": 1000,
      "lower_inclusive": false,
      "upper": 9999,
      "upper_inclusive": true
    },
    "exploration_measurements_in_formal_estimation": false,
    "measure_all_points_before_analysis": true,
    "early_measurement_stop_allowed": false
  },
  "disclosed_exploration": {
    "run_kind": "t2418-explore",
    "physical_values_us": [
      2000,
      4000,
      9999
    ],
    "median_throughput_tps": {
      "write-heavy": [
        746465,
        565390,
        402820
      ],
      "balanced": [
        542511,
        420293,
        317205
      ],
      "read-heavy": [
        1251217,
        921117,
        616015
      ]
    },
    "median_abort_rate": {
      "write-heavy": [
        0.0293,
        0.0198,
        0.0114
      ],
      "balanced": [
        0.0404,
        0.0268,
        0.0145
      ],
      "read-heavy": [
        0.017,
        0.0119,
        0.0074
      ]
    },
    "maximum_reported_cv": 0.0065,
    "observed_abort_direction": "strictly-decreasing-at-all-three-workloads",
    "observed_throughput_direction": "strictly-decreasing-at-all-three-workloads",
    "observed_saturation_status": "not-observed-through-9999us",
    "grid_selection_timing": "after-exploration-before-formal-run",
    "abscissa_reuse_allowed": true,
    "formal_remeasurement_required_at_reused_abscissae": true,
    "exploration_sample_reuse_allowed": false
  },
  "grid": {
    "authoritative_values": "analysis_values_us",
    "generation_rule": {
      "regular_rule": "nearest-integer-half-octaves-above-1000us-through-8000us",
      "regular_ratio": 1.4142135623730951,
      "representation_cap_us": 9999,
      "final_interval_rule": "append-nearest-integer-geometric-midpoint-of-8000-and-9999-then-append-9999"
    },
    "boundary_reference_values_us": [
      1000
    ],
    "formal_tail_values_us": [
      1414,
      2000,
      2828,
      4000,
      5657,
      8000,
      8944,
      9999
    ],
    "analysis_values_us": [
      1000,
      1414,
      2000,
      2828,
      4000,
      5657,
      8000,
      8944,
      9999
    ],
    "encoded_static_points": [
      {
        "physical_us": 1000,
        "backoff_fixed_raw": 3000
      },
      {
        "physical_us": 1414,
        "backoff_fixed_raw": 3414
      },
      {
        "physical_us": 2000,
        "backoff_fixed_raw": 4000
      },
      {
        "physical_us": 2828,
        "backoff_fixed_raw": 4828
      },
      {
        "physical_us": 4000,
        "backoff_fixed_raw": 6000
      },
      {
        "physical_us": 5657,
        "backoff_fixed_raw": 7657
      },
      {
        "physical_us": 8000,
        "backoff_fixed_raw": 10000
      },
      {
        "physical_us": 8944,
        "backoff_fixed_raw": 10944
      },
      {
        "physical_us": 9999,
        "backoff_fixed_raw": 11999
      }
    ],
    "encoding_rule": "physical-us-plus-2000-for-every-registered-point",
    "included_context_references": [
      {
        "name": "static-boundary-1000us",
        "back_off": 1,
        "backoff_fixed_raw": 3000
      }
    ],
    "excluded_context_references": [
      "none",
      "adaptive"
    ],
    "exploration_abscissae_reused_us": [
      2000,
      4000,
      9999
    ],
    "point_counts": {
      "boundary_references_per_workload": 1,
      "formal_tail_points_per_workload": 8,
      "total_points_per_workload": 9
    }
  },
  "workloads": [
    {
      "name": "write-heavy",
      "ycsb_zipf_skew": "0.9",
      "ycsb_rratio": "5",
      "ycsb_rmw": "0",
      "ycsb_max_ope": "10",
      "measurement_seed": 11599877,
      "measurement_order_us": [
        2828,
        4000,
        1414,
        1000,
        2000,
        8944,
        5657,
        8000,
        9999
      ]
    },
    {
      "name": "balanced",
      "ycsb_zipf_skew": "0.9",
      "ycsb_rratio": "50",
      "ycsb_rmw": "0",
      "ycsb_max_ope": "10",
      "measurement_seed": 11599952,
      "measurement_order_us": [
        1414,
        9999,
        1000,
        2828,
        5657,
        4000,
        2000,
        8000,
        8944
      ]
    },
    {
      "name": "read-heavy",
      "ycsb_zipf_skew": "0.9",
      "ycsb_rratio": "95",
      "ycsb_rmw": "0",
      "ycsb_max_ope": "10",
      "measurement_seed": 11600021,
      "measurement_order_us": [
        4000,
        8000,
        8944,
        9999,
        2828,
        2000,
        5657,
        1414,
        1000
      ]
    }
  ],
  "execution": {
    "records": 1000000,
    "threads": 48,
    "extime_s": 3,
    "performance_reps_per_cell": 5,
    "correctness_reps_per_cell": 5,
    "correctness_mode": "legacy+performance",
    "performance_trace_enabled": false,
    "correctness_trace_enabled": true,
    "jobs": 3,
    "one_workload_per_job": true,
    "cells_per_workload": 9,
    "total_cells": 27,
    "expected_performance_rep_observations": 135,
    "expected_correctness_rep_observations": 135,
    "shared_execution_constants_are_authoritative": false,
    "static_meaning_witness_status": "unestablished_for_positive_backoff_fixed_as_in_existing_sweep",
    "new_pointwise_meaning_witness_gate_required": false,
    "time_budget": {
      "sweep_cap_s": 11700,
      "pbs_walltime_s": 18000,
      "reduce_grid_or_reps_on_timeout": false
    }
  },
  "correctness": {
    "separate_trace_enabled_build_required": true,
    "required_verdict": "certified",
    "maximum_anomalies_per_rep": 0,
    "all_reps_for_all_cells_required": true,
    "failed_cell_may_reach_performance_measurement": false,
    "failure_action": "invalidate-entire-formal-cohort"
  },
  "binary_identity": {
    "physical_amounts_us": [
      1000,
      1414,
      2000,
      2828,
      4000,
      5657,
      8000,
      8944,
      9999
    ],
    "expected_trace_disabled_build_results_per_workload": 9,
    "require_exact_build_result_type": true,
    "require_canonical_genome_binding": true,
    "require_full_lowercase_sha256": true,
    "require_complete_amount_set_equality": true,
    "require_all_binary_sha256_values_distinct": true,
    "failure_action": "invalidate-entire-formal-cohort"
  },
  "variability": {
    "metrics": [
      "abort_rate",
      "throughput_tps"
    ],
    "rep_count": 5,
    "sample_standard_deviation_ddof": 1,
    "cv_formula": "sample-standard-deviation-divided-by-arithmetic-mean",
    "maximum_cv_exclusive": 0.02,
    "all-zero-abort-cell_cv": 0.0,
    "failure_action": "invalidate-entire-formal-cohort"
  },
  "analysis": {
    "primary_metric": "abort_rate",
    "throughput_role": "mandatory-cost-context-not-part-of-saturation-predicate",
    "abort_rate_point_estimator": "arithmetic-mean-of-five-reps",
    "also_report_median": true,
    "interval_axis": "adjacent-analysis-values-us",
    "slope_scale": "log-abort-rate-per-log-backoff-us",
    "canonical_effect_span": "one-backoff-doubling",
    "familywise_alpha": 0.05,
    "adjacent_intervals_per_workload": 8,
    "workload_count": 3,
    "simultaneous_comparison_count": 24,
    "multiplicity_correction": "bonferroni",
    "per_comparison_one_sided_alpha": 0.0020833333333333333,
    "confidence_method": "delta-log-ratio-with-welch-satterthwaite-t",
    "formulas": {
      "abort_mean": "m_i=sum(a_i_r)/5",
      "abort_cv": "cv_i=sample_sd(a_i_r)/m_i",
      "log_slope": "qhat_i=log(m_i/m_prev)/log(b_i/b_prev)",
      "log_slope_se": "se_i=sqrt(cv_i^2/5+cv_prev^2/5)/log(b_i/b_prev)",
      "welch_df": "nu_i=(v_i+v_prev)^2/(v_i^2/4+v_prev^2/4),where-v_i=cv_i^2/5",
      "simultaneous_lower_slope": "qL_i=qhat_i-t_quantile(1-0.05/24,nu_i)*se_i",
      "maximum_abort_reduction_per_doubling": "U_i=1-exp(qL_i*log(2))"
    },
    "zero_abort_rules": {
      "both_adjacent_cells_all_zero": "set-qhat-qL-and-U-to-zero",
      "positive_to_all_zero": "not-saturated-because-reduction-is-complete",
      "all_zero_to_positive": "nonmonotonic"
    },
    "saturated_interval": {
      "require_nonincreasing_point_estimate": true,
      "maximum_simultaneous_upper_abort_reduction_per_doubling": 0.05
    },
    "consecutive_saturated_intervals_required": 2,
    "per_workload_location_rule": "earliest-middle-grid-point-of-two-consecutive-saturated-intervals",
    "per_workload_location_bracket_rule": "outer-endpoints-of-the-two-consecutive-intervals",
    "aggregate_saturation_rule": "saturated-in-all-workloads-only-if-every-workload-has-a-valid-location",
    "valid_no_saturation_rule": "complete-valid-workload-with-no-two-consecutive-saturated-intervals",
    "valid_no_saturation_wording": "no-preregistered-saturation-observed-within-the-representable-domain-through-9999us",
    "allowed_aggregate_verdicts": [
      "saturated-in-all-workloads",
      "not-observed-in-any-workload",
      "not-observed-in-at-least-one-workload",
      "invalid"
    ],
    "stopping_rule_kind": "reporting-rule-after-full-grid-not-measurement-early-stop"
  },
  "failure_conditions": {
    "scope": "any-failure-invalidates-the-entire-formal-cohort-for-the-preregistered-claim",
    "missingness": {
      "expected_workload_jobs": 3,
      "expected_cells": 27,
      "expected_performance_reps": 135,
      "expected_correctness_reps": 135,
      "reject_missing_duplicate_nonfinite-out-of-range-or-unexpected-observation": true,
      "cross_campaign_cell_pooling_allowed": false
    },
    "confirmed_nonmonotonicity": {
      "definition": "qL_i-greater-than-zero-for-any-adjacent-interval",
      "action": "invalidate-saturation-and-no-saturation-claims"
    },
    "unconfirmed_upward_wiggle": {
      "definition": "qhat_i-greater-than-zero-and-qL_i-less-than-or-equal-to-zero",
      "action": "report-and-do-not-count-that-interval-as-saturated"
    },
    "sweep_timeout_s": 11700,
    "pbs_walltime_s": 18000,
    "job_interruption_without_bound_resume": "failure",
    "resume_only_with_same_campaign_identity_prereg-spec-source-and-toolchain": true,
    "exploration_sample_contamination": "failure",
    "preregistration_binding_mismatch": "failure",
    "failure_reporting": "report-all-observed-values-and-the-failure-reason-as-descriptive-only"
  },
  "future_driver_binding": {
    "spec_markers": {
      "begin": "IZANAGI-B10-STATIC-TAIL-SPEC-BEGIN",
      "end": "IZANAGI-B10-STATIC-TAIL-SPEC-END"
    },
    "must_parse_entire_spec": true,
    "code_constants_may_override_spec": false,
    "campaign_identity_must_include": [
      "run_kind",
      "workload",
      "preregistration_commit",
      "spec_sha256",
      "analysis_values_us",
      "execution"
    ],
    "run_kind_must_be_new_and_distinct": true,
    "forbidden_existing_run_kinds": [
      "extended",
      "t2266-tail",
      "t2418-explore"
    ],
    "campaign_identity_must_be_disjoint_from_existing_series": true,
    "report_schema_must_be_new_and_disjoint_from_existing_series": true,
    "artifact_stem_must_not_collide_with_any_existing-extended-t2266-tail-or-t2418-explore-stem": true,
    "existing_series_acceptance_sets_may_change": false,
    "existing_series_artifacts_may_change": false,
    "existing_series_report_schemas_may_change": false,
    "exploration_artifacts_may_be_consumed_as_formal_samples": false
  }
}
```
<!-- IZANAGI-B10-STATIC-TAIL-SPEC-END -->

### 7. 後続 driver への束縛

§9 は後続 wave に対し、次を前向きに要求する。

- 上記 HTML marker 間の JSON 全体を parse し、格子、動作点、順序、判定値をコード定数で置換しない。
- 初回 formal 投入時に本書を含む commit hash、文書 blob SHA-256、spec SHA-256 を campaign lock、report、completion artifact へ記録する。
- `extended`、`t2266-tail`、`t2418-explore` のいずれでもない新しい RUN_KIND と campaign identity を使う。
- report schema と成果物 stem も既存 3 系列から分離する。正確な新名称の決定と実装は後続 wave の scope とし、本書は非衝突関係だけを凍結する。
- 探索成果物を formal loader の入力にしない。
- 既存正式系列の受理集合、成果物、schema、`EXTENDED_SWEEP_US`、既存 test を変更しない。

### 8. `docs/README.md` の挿入

現行 L28 の直後、`dynamic-backoff-preregistration.md` の前へ 4 行追加する。

```markdown
- `b10-backoff-static-tail-preregistration.md` — B-10 の静的 backoff 右 tail
  `(1000, 9999]` の本格格子、literal の動作点と反復数、abort 率の飽和報告述語、
  域内非飽和を含む結末、失敗条件、探索開示、後続 driver 束縛の正本
```

挿入位置は [docs/README.md L25〜L29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/README.md:25)。既存 shape preregistration の隣に置く。

## 根拠

- 2 段構成、探索 3 点、探索値を正式標本へ混ぜないこと、探索後かつ本走前に格子と停止基準を凍結することは [d1813.md L3〜L13](/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/verbatim/d1813.md:3) の逐語裁定である。
- 本 wave が docs-only で、探索 abscissa の再利用、literal `5 / 3 / 1000000 / 48`、3 workload、域内非飽和を認めることは [brief.md L30〜L41](/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/brief.md:30) に明記されている。
- docs-only は Codex author 実装面の対象外であることは [d95.md L10〜L19](/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/verbatim/d95.md:10) に一致する。
- `EXTENDED_SWEEP_US` の上端 1000、表現上限 9999、1000 以上の `+2000` 符号化は [backoff-constants.txt L1〜L25](/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/verbatim/backoff-constants.txt:1) および [backoff_extended_sweep.py L55〜L79](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/orchestrator/campaign/backoff_extended_sweep.py:55) が現行の現物である。
- 1000 µs が高域符号化枝を既に通ることは [t2418-explore-README.md L24〜L37](/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/verbatim/t2418-explore-README.md:24) で実測済みである。
- 探索値、median throughput、abort 率、単調低下、最大 CV 0.0065 は [t2418-explore-README.md L193〜L225](/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/verbatim/t2418-explore-README.md:193) にある。
- 探索 campaign が formal 系列と identity、schema、stem を分離していることは [d1848.md L3〜L26](/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/verbatim/d1848.md:3) と [backoff_extended_sweep.py L81〜L100](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/orchestrator/campaign/backoff_extended_sweep.py:81) が根拠である。
- literal workload と既存 measurement seed は [backoff_extended_sweep.py L103〜L116](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/orchestrator/campaign/backoff_extended_sweep.py:103)。共有定数追随を避ける理由は [d1848.md L20〜L22](/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/verbatim/d1848.md:20) と [t2418-explore-README.md L66〜L71](/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/verbatim/t2418-explore-README.md:66) に明記されている。
- t2418 の完全性 gate は全 5 genome の trace-disabled `BuildResult`、genome 束縛、完全 SHA、全相異を要求する [backoff_extended_sweep.py L291〜L321](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/orchestrator/campaign/backoff_extended_sweep.py:291)。その強さを落とせない理由は [t2418-explore-README.md L54〜L64](/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/verbatim/t2418-explore-README.md:54) にある。
- correctness が全点で必要であり、未完走時に report を作らない現行境界は [backoff_extended_sweep.py L1023〜L1111](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/orchestrator/campaign/backoff_extended_sweep.py:1023) と [同 L1468〜L1478](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/orchestrator/campaign/backoff_extended_sweep.py:1468) にある。
- 事前登録 JSON を判定規則の正本として全件 parse させる形式は [b10-backoff-shape-preregistration.md L302〜L325](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-shape-preregistration.md:302)、marker の終端は [同 L646〜L648](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-shape-preregistration.md:646) が先例である。
- commit hash を成果物へ記録し、結果後の変更を事前登録に数えない規則は [b10-backoff-shape-preregistration.md L81〜L86](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-shape-preregistration.md:81) に倣う。
- trace 有無を分け、anomaly があれば即 reject し、時間を理由に correctness rep を減らさない強度は [b10-backoff-shape-preregistration.md L671〜L683](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-shape-preregistration.md:671) が先例である。
- 現行時間枠は `SWEEP_CAP_S=11700`、PBS 5 時間=`18000` 秒である [b10_backoff_grid.sh L1〜L21](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/tools/pegasus/b10_backoff_grid.sh:1)。sweep timeout の実体は [同 L576〜L595](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/tools/pegasus/b10_backoff_grid.sh:576)。
- 実走時間は、8 genome が 11 分で完走した事実が [t2418-explore-README.md L39〜L52](/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/verbatim/t2418-explore-README.md:39)、探索 3 job が 04:36〜04:54 に完了した事実が [同 L193〜L198](/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/verbatim/t2418-explore-README.md:193) にある。
- B-10 の残件が過抑制域を含み、性能地形だけでは spin 分離を伴う機序説明にならないことは [paper-story/2026-08-26.md L848〜L851](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/paper-story/2026-08-26.md:848)。したがって本書は飽和の記述を機序確定へ広げない。
- 既定 adaptive を単独基準線にしない主張軸は [paper-story-backoff/2026-09-05.md L27〜L42](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/paper-story-backoff/2026-09-05.md:27) と [同 L88〜L91](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/paper-story-backoff/2026-09-05.md:88) が根拠である。
- 現行 README の挿入先は shape preregistration 項の末尾 [docs/README.md L25〜L28](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/README.md:25)。

## 未確定・リスク

- 5%/倍増は外部標準から得た閾値ではなく、探索後に選ぶ実用的等価幅である。前向き性は開示と本走前 commit で守れるが、査読では 3%など別幅を問われ得る。案としては 5%を採用し、感度分析で閾値を動かさない。
- 8944 µs は最終区間にも連続 2 区間を作るための 1 点である。これを落とせば 8 genome の先例と同数になるが、8000 µs より右で初めて平坦化した場合を登録述語が検出できない。残す案を推奨する。
- none/adaptive を除外するため、formal job 単独から「無 backoff や adaptive に対して何倍」という主張はできない。飽和判定には不要であり最小規模を優先した結果である。
- `paper-story-backoff/2026-09-05.md` L168〜L172、L287〜L288 は古い符号化世代を前提に「1000 µs は測定不能」と書く。一方、現行 codec と T-2418 一次資料は 1000→3000 の発火と正式上端を明示する。本計画は現行実装と 2026-09-09 の一次資料を数値権威にし、凍結スナップショットは主張軸だけに用いる。
- 新 RUN_KIND、campaign identity、report schema、artifact stem の具体名は親 brief が後続 wave の scope としているため、本書では非衝突条件だけを固定する。これは spec の未確定値ではなく、後続実装に課す関係制約である。

## 総括

静的右 tail は、1000 µs 境界参照と 8 本格点、計 9 点/workload の格子で固定する。  
探索の 2000 / 4000 / 9999 µs は位置だけ再利用し、測定値は正式推定へ混ぜない。  
飽和は abort 率の倍増当たり改善上限 5%、24 区間同時補正、連続 2 区間で判定する。  
全点を必ず測り、停止基準は早期打切りではなく報告規則とする。  
correctness、binary 完全性、欠測、CV 2%、時間超過、非単調、途中終了を fail-closed にする。  
具体的な後続 RUN_KIND 名だけは scope 外で、非衝突と commit/spec 束縛を事前登録する。  
read-only 条件のためファイル変更や pytest は行わず、射影資料の静的照合だけを行った。