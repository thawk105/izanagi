# Paper-story A-1 headline estimand 別 study 事前登録

この文書は、論文 §8 A-3 で採用した headline estimand を現行契約で測り直す**別 study**を、
結果を見る前に事前登録する。既存 A-1 (`paper-story-a1-20260826-sized-v1`) は据え置き、
その文書・policy・driver・test・成果物を変更しない (D1027)。

本 wave で凍結するのは解析契約、sizing certificate、将来 consumer 義務のカテゴリと失敗方向である。
投入器、driver、qsub job body、campaign lock、`BUILD_START`、block、report への runtime 束縛は
未実装であり、測定値も未取得である。この study は `formal=false`、
`promotion_prohibited=true` であり、単独で論文 §8 の A-1 を閉じない。

## 1. Headline estimand と floor

primary point estimand は workload ごとに
`median(variant TPS) / median(baseline TPS) - 1` とする。これは A-3 の表示値を作った式そのものである。
標本数が偶数なら標本中央値は中央 2 順序統計量の算術平均とする。全対比比率の中央値は一般に
この estimand と一致しないため、primary にも secondary にも用いない。

floor は相対効果 3% である。D938 の逐語である「adaptive arm の平均 tps」は旧 A-1 固有なので、
本 study では相対境界という原則を baseline population median 比へ移植し、ratio band
`[97/100, 103/100]` として凍結する。

## 2. 区間と 3 値判定

各 arm の母中央値へ二項順序統計量による有限標本区間を作る。各 arm 内は固定母集団からの IID を
仮定する。連続分布では nominal coverage が exact で、ties や非一意中央値がある場合は
at-least-nominal の保守的区間としてだけ解釈する。IID を満たせない場合は descriptive へ降格し、
95% family coverage を主張しない。3 workload × 2 arm の 6 区間へ
Bonferroni で family alpha `1/20` を配り、各 arm の failure probability を `1/120` とする。
baseline 区間 `[Lb, Ub]`、variant 区間 `[Lv, Uv]` から ratio 区間を
`[Lv / Ub, Uv / Lb]` とする。入力は exact n 件の finite positive TPS に限る。

- `resolved-beyond-floor`: `upper < 97/100` または `lower > 103/100`。前者は `regression`、後者は `improvement`
- `bounded-within-floor`: `lower >= 97/100` かつ `upper <= 103/100`
- `unresolved`: 上のどちらでもない

resolved 側は strict、bounded 側は inclusive である。丸めた表示値は判定に使わない。

## 3. Sizing

反復数は検出力式でなく、この 3 値判定自身の動作特性で決めた (D937)。generation v1 は最初の
search 通過候補だけを certification する規則だった。balanced n=562 の zero 条件が lower bound
0.80 を満たさず、規則どおり不発効にした。seed や threshold を変更せず failed certificate として残す。

generation v2 は結果を見る前に新 seed domain と certification alpha spending を固定した。
search 20,000 trial と source-separated certification replay 100,000 trial を使い、0、+6%、-6% の
3 条件を固定分母で評価する。search 通過 candidate の certification attempt を `j=1,2,...` とし、
各 condition の one-sided exact Clopper-Pearson alpha を `1/(60*j*(j+1))` とする。3 条件と
全 attempt の総 alpha は workload ごとに `1/20` 以下である。全 lower bound が0.80以上になる
最初の n を採る。結果は次のとおり。

| workload | n / arm | lower index | upper index |
|---|---:|---:|---:|
| write-heavy | 218 | 90 | 129 |
| balanced | 564 | 251 | 314 |
| read-heavy | 28 | 7 | 22 |

planning CV は 2026-08-24 の探索走で測った `adaptive` / `static10` の CV 最大値を
`2.372356` 倍して転移した値であり、target arm の CV 上限ではない。したがって動作特性は
この conditional planning model の下でのみ成立する。target arm の真の CV が大きくても、
結果を見た後に n を増やして事前登録を救済してはならない。

failed v1 certificate は `sizing-certificate.failed-v1.json`
(SHA-256 `da511809ba1ef855c39f78aacee3feba5524c222b80d77f2884b61223aa10efd`) である。
canonical v2 certificate は
`output/insights/2026-08-27_paper-story-a1-headline-estimand-preregistration/sizing-certificate.v2.json`
(SHA-256 `4f4735cf43f227f421b0bfcc2c9f17328736a105def15071838e0ba5d5a3e18a`) である。
generator と相互 import しない source-separated replay verifier が seed、pilot、全 candidate、
simulation count、exact bound、alpha spending、最初の通過 n、order index を再計算して一致した。
これは sampler と数学の独立 oracle ではなく、同一規則の別 source replay である。
tracked receipt は `sizing-replay-receipt.v2.json`
(SHA-256 `a147b10f5881eeb000239380cc48580e5217dbc4184fd896ce864f1226a38958`) で、certificate、pilot、
generator/verifier source、Python/NumPy runtime、CLI policy、rc=0を束縛する。

## 4. Canonical machine-readable spec

次の marker 間の JSON object が判定規則の唯一の authority である。mirror policy はこの raw spec と
文書 bytes を束縛する非 authority envelope であり、fallback として使ってはならない。

<!-- PAPER_STORY_A1_HEADLINE_SPEC_START -->
```json
{
  "analysis": {
    "classification": {
      "bounded": {
        "label": "bounded-within-floor",
        "lower_operator": ">=",
        "upper_operator": "<="
      },
      "otherwise": "unresolved",
      "resolved": {
        "direction_negative": "regression",
        "direction_positive": "improvement",
        "label": "resolved-beyond-floor",
        "lower_operator": ">",
        "upper_operator": "<"
      }
    },
    "estimand": {
      "effect": "median-ratio-minus-one",
      "even_sample_median": "arithmetic-mean-of-two-central-order-statistics",
      "point_formula": "median(variant_tps)/median(baseline_tps)-1",
      "population_parameter": "population-median(variant)/population-median(baseline)-1",
      "rounding_for_decision": "prohibited"
    },
    "floor": {
      "band_lower": {
        "denominator": 100,
        "numerator": 97
      },
      "band_upper": {
        "denominator": 100,
        "numerator": 103
      },
      "effect_absolute": {
        "denominator": 100,
        "numerator": 3
      },
      "scale": "ratio-minus-one"
    },
    "input": {
      "boolean_is_numeric": false,
      "exact_count_required": true,
      "finite_required": true,
      "numeric_coercion": "prohibited",
      "positive_required": true
    },
    "interval": {
      "arm_failure_probability": {
        "denominator": 120,
        "numerator": 1
      },
      "cross_arm_independence_required_for_union_bound": false,
      "family": "three-workloads-six-arms",
      "family_alpha": {
        "denominator": 20,
        "numerator": 1
      },
      "method": "exact-binomial-order-statistic-median-rectangle-ratio",
      "runtime_quantile_or_randomness": "prohibited",
      "ties_or_nonunique_median_coverage": "at-least-nominal-conservative",
      "within_arm_sampling": "iid-from-fixed-population-required"
    }
  },
  "applicability": {
    "encoding_grid": "not-applicable-no-generated-proposal-encoding",
    "mu_grid": "not-applicable-no-mu-grid",
    "shape_grid": "not-applicable-no-shape-grid"
  },
  "authority": {
    "canonical_document_path": "output/insights/2026-08-27_paper-story-a1-headline-estimand-preregistration/README.md",
    "canonicalization": "strict-utf8-json-object-indent-2-sorted-keys-lf-v1",
    "failed_sizing_certificate_path": "output/insights/2026-08-27_paper-story-a1-headline-estimand-preregistration/sizing-certificate.failed-v1.json",
    "failed_sizing_certificate_sha256": "da511809ba1ef855c39f78aacee3feba5524c222b80d77f2884b61223aa10efd",
    "mirror_policy_path": "orchestrator/campaign/paper_story_a1_headline.v1.json",
    "sizing_certificate_path": "output/insights/2026-08-27_paper-story-a1-headline-estimand-preregistration/sizing-certificate.v2.json",
    "sizing_certificate_sha256": "4f4735cf43f227f421b0bfcc2c9f17328736a105def15071838e0ba5d5a3e18a",
    "sizing_replay_receipt_path": "output/insights/2026-08-27_paper-story-a1-headline-estimand-preregistration/sizing-replay-receipt.v2.json",
    "sizing_replay_receipt_sha256": "a147b10f5881eeb000239380cc48580e5217dbc4184fd896ce864f1226a38958"
  },
  "execution": {
    "arm_order": "alternate-by-block-baseline-first-on-odd-block-variant-first-on-even-block",
    "block_count": "selected-n-per-workload",
    "build_type": "Release",
    "clocks_per_us": 1800,
    "env_tag": "linux-baremetal",
    "extime_seconds": 3,
    "instrumentation": {
      "ccbench_trace": 0,
      "performance_build_trace_disabled": true
    },
    "numa": "numactl-interleave-all",
    "phase_order": [
      "write-heavy",
      "balanced",
      "read-heavy"
    ],
    "runtime_binding_status": "deferred-unwired",
    "sampling_cohort": {
      "duplicate_rep_id": "future-collector-invalid",
      "first_tps_event_starts_primary_cohort": true,
      "missing_or_invalid_after_first_tps": "retain-as-failure-no-replacement",
      "outlier_exclusion": "future-collector-prohibited",
      "pre_benchmark_retry_reasons": [
        "allocation-lost-before-first-tps",
        "build-failed-before-benchmark",
        "scheduler-never-started"
      ]
    },
    "source_and_binary_binding": "future-campaign-lock-build-start-block-report-required",
    "warmup_repetitions": 0
  },
  "reporting": {
    "b7": {
      "all_workloads_required": true,
      "invalid_omission": "prohibited",
      "regression_omission": "prohibited",
      "status": "deferred-unwired-future-report-consumer-required"
    },
    "b8": {
      "distinct_seed_required": true,
      "long_duration_required": true,
      "primary_result_replacement": "prohibited",
      "status": "deferred-unwired-future-validation-consumer-required"
    },
    "exposure": {
      "attempt_history_required": true,
      "post_exposure_rule_change": "prohibited",
      "result_exposure_before_freeze": "prohibited"
    },
    "missing": {
      "partial_workload_report": "invalid",
      "rerun_to_replace_missing_after_first_tps": "prohibited"
    }
  },
  "schema_version": "paper-story-a1-headline-preregistration-spec/v2",
  "sizing": {
    "certificate_sha256": "4f4735cf43f227f421b0bfcc2c9f17328736a105def15071838e0ba5d5a3e18a",
    "certification_alpha_spending": {
      "all_attempts_total_alpha": {
        "denominator": 20,
        "numerator": 1
      },
      "condition_alpha_at_attempt_j": "1/(60*j*(j+1))"
    },
    "certification_trials": 100000,
    "conditions": [
      "zero",
      "positive-two-floor",
      "negative-two-floor"
    ],
    "invalid_trial": "failure-in-fixed-denominator",
    "n_max": 4096,
    "n_min": 28,
    "planning_cv_is_target_arm_upper_bound": false,
    "root_seed": "531e720c249e561c768471ffbab1d63885a25a08868128bb5c3212843992bc16",
    "root_seed_preimage": "paper-story-a1-headline-sizing-root-seed/v2|20260828|certification-alpha-spending",
    "search_trials": 20000,
    "selection": "ascending-every-n-first-search-and-alpha-spent-certification-pass",
    "source_separated_replay_receipt_sha256": "a147b10f5881eeb000239380cc48580e5217dbc4184fd896ce864f1226a38958",
    "success_probability_required": {
      "denominator": 5,
      "numerator": 4
    }
  },
  "status": {
    "formal": false,
    "promotion_prohibited": true,
    "result_observed": false,
    "runtime_wired": false
  },
  "study_id": "paper-story-a1-headline-estimand-20260828-v2",
  "workloads": [
    {
      "baseline": {
        "BACKOFF_FIXED": -1,
        "BACKOFF_NOINLINE": 0,
        "BACK_OFF": 0,
        "label": "no-backoff"
      },
      "lower_index_1based": 90,
      "name": "write-heavy",
      "records": 1000000,
      "repetitions_per_arm": 218,
      "rmw": 0,
      "rratio": 5,
      "skew": "0.9",
      "threads": 48,
      "upper_index_1based": 129,
      "variant": {
        "BACKOFF_FIXED": 10,
        "BACKOFF_NOINLINE": 0,
        "BACK_OFF": 1,
        "label": "fixed10"
      }
    },
    {
      "baseline": {
        "BACKOFF_FIXED": -1,
        "BACKOFF_NOINLINE": 0,
        "BACK_OFF": 0,
        "label": "no-backoff"
      },
      "lower_index_1based": 251,
      "name": "balanced",
      "records": 1000000,
      "repetitions_per_arm": 564,
      "rmw": 0,
      "rratio": 50,
      "skew": "0.9",
      "threads": 48,
      "upper_index_1based": 314,
      "variant": {
        "BACKOFF_FIXED": 5,
        "BACKOFF_NOINLINE": 0,
        "BACK_OFF": 1,
        "label": "fixed5"
      }
    },
    {
      "baseline": {
        "BACKOFF_FIXED": -1,
        "BACKOFF_NOINLINE": 0,
        "BACK_OFF": 0,
        "label": "no-backoff"
      },
      "lower_index_1based": 7,
      "name": "read-heavy",
      "records": 1000000,
      "repetitions_per_arm": 28,
      "rmw": 0,
      "rratio": 95,
      "skew": "0.9",
      "threads": 48,
      "upper_index_1based": 22,
      "variant": {
        "BACKOFF_FIXED": 2,
        "BACKOFF_NOINLINE": 0,
        "BACK_OFF": 1,
        "label": "fixed2"
      }
    }
  ]
}
```
<!-- PAPER_STORY_A1_HEADLINE_SPEC_END -->

## 5. Runtime consumer 義務と主張上限

今 wave の parser は、呼出し側から渡された canonical path 文字列、README bytes、mirror bytes の
pair consistency を検査し、deeply immutable spec を解析関数へ渡す純関数である。任意 path、mirror
fallback、nested duplicate key、非 canonical JSON、未知/欠落 key、nonfinite、bool-as-numberを拒否する。
`formal=false`、`promotion_prohibited=true`、`result_observed=false`、`runtime_wired=false` と deferred
status は schema v2 の exact literal であり、同じ schema のまま反転できない。

一方、bytes が実際に canonical path の regular non-symlink file から 1 回だけ読まれたこと、
freeze commit と ancestry、spec/code digest が campaign lock、各 `BUILD_START`、block、reportへ
束縛されたことは、将来の投入器・driver・collector・report consumer が閉じる。本 wave はその配線を
実装せず、配線済みとも呼ばない。duplicate rep ID、outlier exclusion、raw attempt cohort は future
collector の規則であり、TPS 配列だけを受ける解析関数が実効化したとは数えない。

## 6. B-7 / B-8 と失敗条件

B-7 により3 workloadを常に全件報告し、退行、invalid、unresolvedを落とさない。
B-8 により最終候補は別 seed の長時間 validation 相を必要とする。ただし validation は primaryを
置換せず、未実施なら未実施と報告する。具体的 seed、duration、collector配線は本 wave のscope外で、
未確定値を後付けで埋めたことにしてはならない。

primary cohort の warmup は 0 回で、最初の TPS event から cohort が始まる。その後の missing / invalid
attempt は保持して failure とし、置換再走しない。最初の TPS より前に限り、spec の閉集合にある
infrastructure 理由だけ再走できる。全 attempt history は残す。

target arm の実現 CV が planning proxy を超えた場合も primary 判定を上書きしない。動作特性の
条件付き説明が外れた事実を全 workload とともに報告し、結果後に n や規則を動かさない。
