## 総括

D1452 の照合は consumer 側だけで閉じる案を採る。道具側の変更は不要。
ただし、現行 validator のまま本番証明書を受理する policy は作れない。sigma の十進表現を保持する局所修正が必要。
(P1-3) の `formal=true` は採らず、現行 driver と一致する `formal=false / promotion_prohibited=true` を維持する。
成果物は現行配置規約に合わせ、`output/insights/2026-09-13/paper-story-a1-balanced5-sized-preregistration/` に同居させる。
証明書候補の hash・pilot の束縛・道具の source hash は静的に一致を確認した。replay・pytest・load_policy は実行していない。
本走は未投入・人間認可待ちと明記する。さらに、計測本体に残る pilot 専用制約は別途親へ返す。

## 変更面 (file:line 粒度)

以下、既存ファイルの行番号は現在のもの。新規ファイルの `:1` は先頭からの追加を指す。

### 1. driver：本番証明書を受理するための必須修正

対象：[orchestrator/campaign/paper_story_a1_paired.py:1477](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-a1-sizing-certificate/orchestrator/campaign/paper_story_a1_paired.py:1477)、1477–1485 行。

**現状の不整合**

- 1480–1483 行は `k`・`planned_sigma_tps` に `_finite_number` を要求する。
- `_finite_number`（4726–4732 行）は文字列を拒否する。
- 一方、1370–1387 行は `Decimal(str(value))` による exact な数値照合を行う。
- 証明書の数値文字列は生成側 127–130 行の `.17g` 表現である。

標準 JSON loader を経由した結果を静的に確認すると、次の差が生じる。

| workload | 証明書の sigma | JSON 数値として読み込んだ後の `str(float)` |
|---|---|---|
| write-heavy | `66403.452108019716` | `66403.45210801972` |
| balanced | `56697.435713574683` | `56697.43571357468` |
| read-heavy | `74668.489566274948` | `74668.48956627495` |

したがって、数字の桁をそのまま JSON 数値へ書くだけでは通らない。

**変更後**

sized 分岐を次の形へ置換する。

```python
        else:
            if reps < 30 or reps % 10 != 0:
                raise PaperStoryError(
                    f"v3 sized workload plan differs: {workload_name}"
                )
            for field in ("k", "planned_sigma_tps"):
                value = _positive_decimal(
                    workload.get(field),
                    f"v3 sized workload {field}: {workload_name}",
                )
                if not _finite_number(float(value)):
                    raise PaperStoryError(
                        f"v3 sized workload plan differs: {workload_name}"
                    )
```

既存 `_positive_decimal` を使い、正の有限十進文字列を保持する。bool・非数・非正値は拒否し、実計算用 float の有限性も維持する。1370–1387 行の exact 照合は変更しない。

統計計算側の 4713・4720–4721 行は既に明示的に `float(...)` へ変換しているので変更不要。全体の `_finite_number` や JSON loader を変更する必要もない。

### 2. driver：D1452 の consumer 側照合

対象：[paper_story_a1_paired.py:1338](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-a1-sizing-certificate/orchestrator/campaign/paper_story_a1_paired.py:1338)。

**1338 行の input binding 検査直後、1339 行の workload 検査より前**へ追加する。

```python
    certificate_policy = certificate.get("policy")
    if type(certificate_policy) is not dict:
        raise PaperStoryError("v3 sized certificate registered policy differs")

    # Frozen pilot preregistration §§5.4–5.5; D1452.
    for section_name, field, expected in (
        ("search", "trials", 20000),
        ("certification", "trials", 100000),
        ("candidate_grid", "registered_minimum", 28),
        ("candidate_grid", "maximum", 4096),
        (
            "root_seed",
            "digest",
            "e72bc005d156caea2c89085c563c72fa04bbeb4afd98160fca968da9a7f6b3b3",
        ),
    ):
        section = certificate_policy.get(section_name)
        if type(section) is not dict:
            raise PaperStoryError(
                f"v3 sized certificate registered policy differs: {section_name}"
            )
        observed = section.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise PaperStoryError(
                "v3 sized certificate registered policy differs: "
                f"{section_name}.{field}"
            )
```

出所は pilot README の 166–167 行と 184–196 行。厳密には候補上下限の数値本体は **§5.4**、試行回数・root seed は **§5.5** にある。

比較対象を sized policy の自由な値から取らず、凍結済み事前登録の literal にする。Markdown parser や道具側への import は追加しない。整数は `20000.0`・`"20000"`・bool も拒否する。

**consumer 側だけで閉じられる範囲**

D1452 が問題にする「別の試行回数・候補上下限で選んだ証明書の受理」は、この追加で閉じる。証明書全体の再計算は既存 verifier の役割であり、driver が replay receipt を検証したとは主張しない。

### 3. sized policy の全内容

新規：`orchestrator/campaign/paper_story_a1_paired.v3-sized.json:1`

下記は省略のない内容案。`<README_SHA256>` **だけ**は、後述の順序で親が README を凍結した後、その実 bytes の SHA-256 に置換する。未作成 README の hash をここで捏造しない。

```json
{
  "authority": {
    "formal": false,
    "promotion_prohibited": true,
    "result_authority": "sized-preregistered-descriptive-only"
  },
  "campaign_schema": "paper-story-a1-paired-campaign/v2",
  "ccbench_acceptance": {
    "boundaries": [
      "login-submit-before-intent-and-qsub",
      "compute-job-body-preflight",
      "driver-measurement-start",
      "before-each-trace-and-perf-build",
      "artifact-consumer-arm-validation-and-materializer-raw-recollection"
    ],
    "build_preflight_required": true,
    "canonical_pin": "511c9538e4e8efa54b45cda62e72389ed3b706ec",
    "parent_submodule_ignore_independent": true,
    "tracked_clean_required": true,
    "untracked_files_ignored": true
  },
  "execution": {
    "automatic_retry": false,
    "bench_lock_acquisitions_per_workload": 1,
    "bench_lock_scope": "all-balanced-five-rep-blocks-after-both-arms-build-and-verify",
    "bench_max_rounds": 1,
    "campaign_shape": "one fresh exact-two-arm balanced-five-rep campaign per workload",
    "competing_tenant_probe": "before-each-five-rep-arm-block-fail-closed-workload-abort",
    "durable_measurement_base": "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-a1-balanced5-sized-20260913/measurement",
    "materialization": "terminal raw bundle to exclusive-create destination",
    "materialization_relative_path": "output/insights/2026-09-13/paper-story-a1-balanced5-sized",
    "mode": "exploration",
    "schedule_round_definition": "one complete workload schedule",
    "settle": "once-at-workload-schedule-start",
    "site": "pegasus-compute-only"
  },
  "final_estimate_eligible": true,
  "invalid_rules": [
    "campaign workload arm set is not exactly its registered variant and baseline",
    "an arm has anything other than exactly one build attempt",
    "both arms are not built and verified before the first bench block",
    "a verify_done is not certified true or its workload tag differs",
    "a competing-tenant probe is missing, raises, or detects a tenant before any five-rep arm block",
    "settle is missing, fails, or occurs other than once at workload schedule start",
    "bench throughput has no point",
    "bench aggregate CV is undefined",
    "bench aggregate CV is not computed from every rep of its arm",
    "bench rounds is not exactly integer one",
    "bench unstable is not exactly false",
    "a block has anything other than five positive finite throughput points",
    "schedule receipt is missing or differs from the frozen seed derivation and physical order",
    "a workload is interrupted, one-sided committed, or lacks both arm completion records",
    "trace0 source-routed evidence is incomplete or inconsistent",
    "CCBench HEAD differs from canonical pin or CCBench tracked files are dirty at a required boundary"
  ],
  "pairing": {
    "arm_block_reps": 5,
    "contrast": "variant-minus-baseline",
    "design": "balanced-a5b5-b5a5-v1",
    "estimand": "arithmetic mean of paired differences under the balanced five-rep schedule",
    "group_pairs": 10,
    "physical_orders": {
      "bit_0": "A^5 B^5 B^5 A^5",
      "bit_1": "B^5 A^5 A^5 B^5"
    },
    "schedule_receipt_schema": "paper-story-a1-balanced-schedule-receipt/v1",
    "seed": {
      "all_identical_redraw": {
        "counter_initial": 0,
        "counter_limit_exclusive": 16,
        "effective_root_seed_preimage": "<64-lowercase-hex>|counter=<zero-based decimal>",
        "failure": "fail-closed when counter reaches 16 without a non-identical bit sequence",
        "predicate": "all workload group order bits are 0 or all workload group order bits are 1",
        "rule": "increment the fixed counter and redraw the entire workload bit sequence before observing or selecting any realized schedule"
      },
      "concatenation": "root seed ASCII bytes followed immediately by group preimage UTF-8 bytes",
      "digest": "SHA-256",
      "group_preimage": "a1-balanced5/v1|workload=<name>|group=<zero-based decimal>",
      "group_preimage_prohibits": ["study ID", "date"],
      "order_bit": "least-significant bit of the SHA-256 digest",
      "root_seed_encoding": "64 lowercase hexadecimal ASCII characters"
    }
  },
  "preregistration": {
    "path": "output/insights/2026-09-13/paper-story-a1-balanced5-sized-preregistration/README.md",
    "sha256": "<README_SHA256>"
  },
  "quality": {
    "aggregate_cv": "sample standard deviation of all arm rep TPS divided by arithmetic mean of all arm rep TPS",
    "block_cv": "diagnostic-only and never substituted or averaged for aggregate CV",
    "throughput_absent": "bench-no-throughput and abort whole workload",
    "unstable": "aggregate_cv > 0.05",
    "undefined_cv": "bench-cv-undefined and abort whole workload",
    "unsettled": "bench-unsettled and abort whole workload"
  },
  "rerun": {
    "allowed_reasons": [
      "build-failure-before-bench",
      "verify-failure-before-bench",
      "competing-tenant-detected-before-bench",
      "scheduler-or-infrastructure-failure-before-bench"
    ],
    "closed_enumeration": true,
    "performance_output_may_not_authorize_rerun": true
  },
  "scale": {
    "expected_verify_configs": ["legacy"],
    "extime_s": 3,
    "records": 1000000,
    "threads": 48,
    "ycsb_max_ope": "10",
    "ycsb_rmw": "0",
    "ycsb_zipf_skew": "0.9"
  },
  "schema_version": "paper-story-a1-paired-policy/v3",
  "sizing": {
    "alpha_c": {"denominator": 20, "numerator": 1},
    "arm_failure_probability": {"denominator": 120, "numerator": 1},
    "block_mean_count": 12,
    "conditions": [
      {
        "delta_from_baseline_mean": {"denominator": 1, "numerator": 0},
        "name": "zero"
      },
      {
        "delta_from_baseline_mean": {"denominator": 50, "numerator": 3},
        "name": "positive-six-percent"
      },
      {
        "delta_from_baseline_mean": {"denominator": 50, "numerator": -3},
        "name": "negative-six-percent"
      }
    ],
    "family_alpha": {"denominator": 20, "numerator": 1},
    "floor_fraction": {"denominator": 100, "numerator": 3},
    "n_grid": {
      "effective_minimum": 30,
      "maximum": 4096,
      "maximum_candidate": 4090,
      "nominal_minimum": 28,
      "rule": "evaluate operating characteristics only at the actual candidate n",
      "step": 10
    },
    "pilot_pair_blocks": {
      "baseline_first": 6,
      "pairs_per_block": 5,
      "total": 12,
      "variant_first": 6
    },
    "pilot_pairs_per_workload": 60,
    "planned_sigma": "max(sigma_pair, sigma_block)",
    "required_success_probability": {"denominator": 5, "numerator": 4},
    "sigma_block": "sqrt(5) * c(one-sided, alpha_c, df = 11) * sd(12 five-pair block means)",
    "sigma_pair": "c(one-sided, alpha_c, df = 59) * sd(60 paired differences)",
    "sqrt_block_size": "sqrt(5)",
    "upper_factor": "c(one-sided, alpha_c, df) = sqrt(df / chi-square-quantile(alpha_c, df))"
  },
  "sizing_inputs": {
    "pilot_result": {
      "path": "output/insights/2026-09-01_paper-story-a1-balanced5-pilot/sizing-pilot.json",
      "sha256": "b4201083cc02434b6b300eb24b6916304bfcadc17c7259257e5cf2ee5a7451ed"
    },
    "sizing_certificate": {
      "path": "output/insights/2026-09-13/paper-story-a1-balanced5-sized-preregistration/sizing-certificate.json",
      "sha256": "41d041963c8f3a175b5501810f52ab2619d9285f6f1eeb176790698131fc8299"
    }
  },
  "study_id": "paper-story-a1-20260901-balanced5-sized-v1",
  "workloads": [
    {
      "arms": [
        {
          "contrast": "minuend",
          "flags": {
            "BACKOFF_FIXED": 10,
            "BACK_OFF": 1,
            "NO_WAIT_LOCKING_IN_VALIDATION": 1,
            "NO_WAIT_OF_TICTOC": 0,
            "WAL": 0
          },
          "name": "fixed10",
          "protocol": "silo",
          "role": "variant"
        },
        {
          "contrast": "subtrahend",
          "flags": {
            "BACKOFF_FIXED": -1,
            "BACK_OFF": 0,
            "NO_WAIT_LOCKING_IN_VALIDATION": 1,
            "NO_WAIT_OF_TICTOC": 0,
            "WAL": 0
          },
          "name": "no-backoff",
          "protocol": "silo",
          "role": "baseline"
        }
      ],
      "df": 29,
      "k": "2.8315526875186725",
      "name": "write-heavy",
      "pair_indices": {"start_inclusive": 0, "stop_exclusive": 30},
      "planned_sigma_tps": "66403.452108019716",
      "reps": 30,
      "schedule_root_seed": "e82d0c269021faae457924b71e22b720ca881d4ff0ac6726cf4d8c9c774323d3",
      "ycsb_rratio": "5"
    },
    {
      "arms": [
        {
          "contrast": "minuend",
          "flags": {
            "BACKOFF_FIXED": 5,
            "BACK_OFF": 1,
            "NO_WAIT_LOCKING_IN_VALIDATION": 1,
            "NO_WAIT_OF_TICTOC": 0,
            "WAL": 0
          },
          "name": "fixed5",
          "protocol": "silo",
          "role": "variant"
        },
        {
          "contrast": "subtrahend",
          "flags": {
            "BACKOFF_FIXED": -1,
            "BACK_OFF": 0,
            "NO_WAIT_LOCKING_IN_VALIDATION": 1,
            "NO_WAIT_OF_TICTOC": 0,
            "WAL": 0
          },
          "name": "no-backoff",
          "protocol": "silo",
          "role": "baseline"
        }
      ],
      "df": 29,
      "k": "2.8315526875186725",
      "name": "balanced",
      "pair_indices": {"start_inclusive": 0, "stop_exclusive": 30},
      "planned_sigma_tps": "56697.435713574683",
      "reps": 30,
      "schedule_root_seed": "f322d1daa33e1dd5bf15d3566cc81bb817a15233be762ca64a22664bb3c0ff94",
      "ycsb_rratio": "50"
    },
    {
      "arms": [
        {
          "contrast": "minuend",
          "flags": {
            "BACKOFF_FIXED": 2,
            "BACK_OFF": 1,
            "NO_WAIT_LOCKING_IN_VALIDATION": 1,
            "NO_WAIT_OF_TICTOC": 0,
            "WAL": 0
          },
          "name": "fixed2",
          "protocol": "silo",
          "role": "variant"
        },
        {
          "contrast": "subtrahend",
          "flags": {
            "BACKOFF_FIXED": -1,
            "BACK_OFF": 0,
            "NO_WAIT_LOCKING_IN_VALIDATION": 1,
            "NO_WAIT_OF_TICTOC": 0,
            "WAL": 0
          },
          "name": "no-backoff",
          "protocol": "silo",
          "role": "baseline"
        }
      ],
      "df": 29,
      "k": "2.8315526875186725",
      "name": "read-heavy",
      "pair_indices": {"start_inclusive": 0, "stop_exclusive": 30},
      "planned_sigma_tps": "74668.489566274948",
      "reps": 30,
      "schedule_root_seed": "9ad57bf708b51345af6a65c2208493f99e1d3c308cc48b329b816240d9a701ce",
      "ycsb_rratio": "95"
    }
  ]
}
```

**pilot policy との差分と出所**

比較元：[paper_story_a1_paired.v3-pilot.json:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-a1-sizing-certificate/orchestrator/campaign/paper_story_a1_paired.v3-pilot.json:1)。

| key／比較元行 | 変更 | 出所 |
|---|---|---|
| `authority.result_authority`：5 | `sized-preregistered-descriptive-only` | 親が新たに凍結する本走の用途。driver の descriptive 出力と整合 |
| `execution.durable_measurement_base`：29 | 上記本走専用 path | P1-5、親の新規凍結値 |
| `execution.materialization_relative_path`：31 | 上記本走専用 path | P1-5、配置規約 |
| `final_estimate_eligible`：37 | `false → true` | driver 1401–1407 行の sized 契約。pilot の観測値を使える意味ではない |
| `preregistration.path`：88 | 新規 README | 親の新規凍結値 |
| `preregistration.sha256`：89 | 凍結 README の実 hash | 親が bytes 確定後に算出 |
| `study_id`：187 | `paper-story-a1-20260901-balanced5-sized-v1` | driver 100 行の既存 literal。日付を `20260913` に変えない |
| `workloads[*].reps`：224、263、302 | `60 → 30` | 証明書 `workloads[*].selected.n` |
| `workloads[*].df`：218、257、296 | `59 → 29` | 同 `selected.df` |
| `workloads[*].pair_indices.stop_exclusive`：222、261、300 | `60 → 30` | 同 `selected.n`、driver 1147 行 |
| `workloads[*].k`：各 workload に追加 | 上記十進文字列 | 同 `selected.t_critical` |
| `workloads[*].planned_sigma_tps`：各 workload に追加 | 上記十進文字列 | 同 `planned_sigma_tps` |
| `workloads[*].schedule_root_seed`：225、264、303 | 上記 3 値 | P1-4。後述の規則で親が新規凍結 |
| `sizing_inputs`：新規 | `pilot_result` と `sizing_certificate` のみ | driver 1665–1679 行の exact key 集合 |
| `sizing_inputs.pilot_result.{path,sha256}` | 証明書の入力束縛 | 証明書 `inputs.pilot.{path,sha256}` |
| `sizing_inputs.sizing_certificate.{path,sha256}` | 最終配置と候補 bytes の実 hash | 親の配置決定、候補証明書 |

**上記以外は pilot と同値。** 特に `authority.formal=false`、`promotion_prohibited=true`、`execution.mode=exploration` を維持する。

`sizing.pilot_pairs_per_workload=60`、`block_mean_count=12`、`pilot_pair_blocks` は **sigma の入力となった pilot の設計**なので、30 対へ変更しない。`sizing.conditions` も証明書側の別名へ置換しない。

`replay_receipt` を `sizing_inputs` に追加すると exact key 検査に違反するため、README から束縛する。

### 4. sized 事前登録 README の節構成

新規：`output/insights/2026-09-13/paper-story-a1-balanced5-sized-preregistration/README.md:1`

| 新 README の構成 | pilot README の対応行・節 | 内容 |
|---|---|---|
| 冒頭メタデータ | 1–10 行 | `authority: preregistration`、`default_effect: no-state-change`、本走 study ID、機械可読 policy の path、自己参照禁止 |
| §1 何を測るか | §1、14–32 行 | 同一 workload・arm・flags・scale。未投入・人間認可待ち、formal/promotion の意味を明記 |
| §2 配置と凍結 schedule seed | §2、34–88 行 | **30 対、6 対ブロック、12 arm ブロック、3 組、各先行3本**。seed 表・新規 root 導出規則。既存 group preimage と redraw は維持 |
| §3 推定対象と限定 | §3、90–104 行 | 5-rep 均衡配置下の対差平均。定常直接効果との同一視を禁止 |
| §4 pilot から得た計画 scale | §4、106–122 行 | 凍結済み sigma 式を継承。証明書の baseline 水準・planned sigma を workload 別に掲載。旧 sigma 非流用、pilot の最終推定混入禁止 |
| §5 反復数の探索・認証と選択値 | §§5.1–5.5、124–197 行 | 凍結規則を継承。`n=30 / df=29 / k` を掲載。数値実験は性能結果ではないと明記 |
| §5.6 証拠の束縛と consumer 照合 | 新設、pilot §5.5 の補足 | pilot・証明書・最終 receipt の path/hash、道具 source hash。D1452 の5値照合と verifier の役割を区別 |
| §6 走行・品質・無効・再走 | §§6.1–6.4、199–264 行 | 新規出力 path 以外を継承。16 invalid rules、追加の `rep_notes` 条件、規律2・性能依存再走禁止を保持 |
| §7 本走の出力でできること・できないこと | §7、266–283 行 | 認可後に取得される本走データのみが登録解析の対象。pilot 分類・混入・自動昇格は禁止。現時点では本走結果なし |
| §8 設計の限界 | §8、285–302 行 | 正規模型・scale 固定に条件付けた sizing、残留効果、source-routed 証拠、workload 横断結論の禁止を保持 |
| §9 還元判断 | §9、304–306 行 | CCBench 本体への還元候補なし |

§5.5 の凍結文書自体は編集しない。新 README 側で「道具の広い受理範囲に加え、sized consumer が登録値を照合する」と補足する。

§8 の note 感度式は継承可能だが、pilot の `n=60` の例を本走の説明へそのまま写さない。本走は `2n=60` と明示する。新たな性能評価は書かない。

**schedule root の前向きな導出規則**

新 README §2 に次を登録する。

> 各 workload の root seed は、ASCII 文字列  
> `paper-story-a1-balanced5-sized-schedule-root/v1|workload=<name>`  
> の SHA-256 小文字16進表現とする。`<name>` は `write-heavy`、`balanced`、`read-heavy` の exact literal。末尾改行を含めない。原像・導出値を本走のスケジュール生成前に凍結し、pilot の TPS、選択された n、実現順序を理由に別の原像を試さない。引き直しは既存の全 bit 同一時の counter 規則だけに限る。

上記 policy の3値は、この原像から算出した候補値。group preimage 自体には日付・study ID を追加しない。

### 5. 成果物と pin の凍結順序

対象：[paper_story_a1_paired.py:212](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-a1-sizing-certificate/orchestrator/campaign/paper_story_a1_paired.py:212)、212–213 行。

```python
V3_SIZED_PREREGISTRATION_RELATIVE_PATH: str | None = (
    "output/insights/2026-09-13/"
    "paper-story-a1-balanced5-sized-preregistration/README.md"
)
V3_SIZED_PREREGISTRATION_SHA256: str | None = (
    "<README_SHA256>"
)
```

親の実装順序は次とする。

1. **証明書を最終 path に byte 同一で配置して凍結する。**  
   `sizing-certificate.json:1` は候補の全 bytes。hash は  
   `41d041963c8f3a175b5501810f52ab2619d9285f6f1eeb176790698131fc8299`。
2. **最終証明書 path を渡して既存 verifier で replay receipt を生成・検証し、凍結する。**  
   `sizing-replay-receipt.json:1` に配置する。
3. **最終証明書・receipt の path/hash、schedule seed、用途・出力先を含め README を凍結する。**
4. README bytes の SHA-256 を算出し、driver の2 pin と policy の `preregistration` を確定する。
5. policy bytes を凍結する。policy hash を README に逆流させない。
6. 親が `load_policy` と関連テストを実行する。

候補 receipt は `certificate.path` が worktree 外の候補ファイルを指す。既存 verifier の [726–744 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-a1-sizing-certificate/tools/verify_paper_story_a1_balanced_sizing.py:726) と 758–771 行は path を含め比較するため、**候補 receipt をそのまま最終証明書用と扱わない**。手編集で path を差し替えず、最終 path で生成する。

### 6. job script

対象：[tools/pegasus/paper_story_a1_paired.sh:49](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-a1-sizing-certificate/tools/pegasus/paper_story_a1_paired.sh:49)、49–52 行。

sized study ID から `paper_story_a1_paired.v3-sized.json` を選ぶ分岐は **既にある**。`V3_STUDY=1` も設定済みなので、本 wave の凍結・loader 受入のための変更は不要。

ただし、以下は実在する未解決事項である。

- script 1362–1372 行の依存ソース staging は pilot policy に限定される。
- driver 7077–7079 行は v3 計測途中で無条件に source amendment の study/attempt を要求し、エラー文も `requires pilot attempt-0004`。
- よって、sized 分岐の存在だけから本走の実行可能性を結論できない。

本 wave ではこれらの限定を外さず、README 冒頭または親の完了報告に「policy 受理の完了は計測経路の受入完了を意味しない」と明記する。

### 7. 成果物の置き場

[output/README.md:82](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-a1-sizing-certificate/output/README.md:82)、82–85 行は、新規の複数ファイルを `YYYY-MM-DD/<topic>/` にまとめる規約である。

したがって置き場は次を推奨する。

```text
output/insights/2026-09-13/paper-story-a1-balanced5-sized-preregistration/
├── README.md
├── sizing-certificate.json
└── sizing-replay-receipt.json
```

headline の同居構成は先例として採れるが、旧い `YYYY-MM-DD_topic/` 命名まで新規資料へ継承する根拠にはならない。pilot 公開先・headline 凍結ディレクトリには追加しない。

本走結果の将来の materialization 先は別の  
`output/insights/2026-09-13/paper-story-a1-balanced5-sized`  
とし、本 wave では作成しない。

## (P1) への評価

| 項目 | 評価 | 根拠 |
|---|---|---|
| **P1-1** | **採る** | D1452 が明示的に求める穴を閉じる。consumer の一箇所で5値を型込み照合でき、道具の式・候補・停止規則を変更しない |
| **P1-2** | **条件付き** | README・証明書・receipt の同居は採る。ディレクトリ名は現行 `output/README.md:82–85` に従う |
| **P1-3** | **採らない** | 人間認可前の正式性宣言を避けるだけでなく、driver 7431–7432、7821–7826、8116 行の固定された非正式出力と整合させる必要がある |
| **P1-4** | **条件付きで採る** | 上記の原像を先に固定し、結果や実現順序で seed を選び直さない。sizing root seed は一切変更しない |
| **P1-5** | **採る** | pilot の create-only 公開先と本走を分離できる。新規 durable path と materialization path を README・policy へ同時に凍結する |

P1-3 の代案は、上記 policy の `formal=false / promotion_prohibited=true` と `final_estimate_eligible=true` の組合せである。後者は「本走観測値を登録解析の対象にする」という profile の意味であり、投入許可・正式昇格の意味ではない。

[T-1505] の逐語だけから `formal` という key の意味までは断定できない。しかし、現行実装には「将来認可後の正式性」を示すという別解釈の裏付けがない。認可時に policy の bool だけを反転すれば済むとも約束しない。

P1-4 で pilot seed を使い回すと、同じ group index の raw 順序 bit が共有され、本走の短い系列が pilot の先頭部分と重なり得る。ただし n によって全 bit 同一の redraw 判定が変わるため、常に完全一致するとは限らない。別 seed はこの共有を避ける設計であり、測定値の独立性や残留効果の消失を保証するものではない。

## テスト

対象はすべて  
`orchestrator/tests/test_paper_story_a1_paired.py`。以下の `::...` を連結したものが nodeid。

**改訂する既存テスト**

- `::test_v3_loader_accepts_future_sized_policy_shape`（1012–1093 行）  
  1035–1048 行の証明書 fixture に D1452 の5登録値を追加する。さらに 1019 行より前で、仮 README の bytes と hash を作り、2 sized pin をその仮 binding へ monkeypatch する。`_repo_root` を tmp repo に変えても README が存在するようにする。既存の n/k/sigma drift と証明書不在の負例は保持する。

**新規：1095 行直前へ追加**

| nodeid | 正例・負例 |
|---|---|
| `::test_v3_sized_frozen_policy_loads_with_registered_certificate` | 実際の凍結 policy を `load_policy(V3_SIZED_STUDY_ID)` で読む。3 workload の n/df/k/sigma、2入力 binding、authority、pilot との出力先分離を literal と照合 |
| `::test_v3_sized_certificate_requires_registered_parameters` | 5値の正例。負例 ids は `search-trials`、`certification-trials`、`registered-minimum`、`maximum`、`root-seed`。証明書を書き直して **binding hash も更新**し、hash mismatch ではなく登録値照合で落ちることを確認 |
| `::test_v3_sized_certificate_rejects_missing_or_mistyped_registered_parameters` | policy/各 section/各 field の欠落、section の非 object、整数の float・文字列・bool 化、seed の非文字列・大文字化を拒否 |
| `::test_v3_sized_certificate_preserves_decimal_statistics` | 本番 sigma 3文字列を受理。最短 float 表現への置換、および float にすると同値になる末尾改変も exact 照合で拒否 |
| `::test_v3_sized_statistics_reject_invalid_decimal_values` | `k`・sigma の bool、null、非数、NaN/Infinity 文字列、0・負数を拒否 |
| `::test_v3_sized_consumer_uses_registered_decimal_statistics` | 合成した30対を consumer に渡し、既知の差・SDから k、半幅、現在走 baseline 相対 floor、variance breach を確認。実 pilot 値を結果に使わない |
| `::test_v3_sized_preregistration_binding_has_no_policy_self_reference` | README bytes の hash が policy と module pin に一致し、算出した policy hash が README 本文にない。README 改変を loader が拒否 |
| `::test_v3_sized_schedule_roots_follow_frozen_derivation` | 独立に literal 原像から SHA-256 を計算し、3 root が登録値・pilot と異なることを確認。group preimage と redraw 規則は既存のまま |

D1452 の負例値は、例えば探索 `19999`、認証 `99999`、下限 `29`、上限 `4095`。後者2つは実現候補集合を変えない場合でも、登録した引数との exact 一致を要求することを検証できる。

**変更だけで赤になる既存テストの静的予測**

- `::test_v3_loader_accepts_future_sized_policy_shape`  
  **赤になる。** 新照合では fixture の `certificate.policy` 欠落で落ちる。そこを直しても、実 pin の導入後は tmp repo に README がないため、現状のままでは loader が失敗する。
- `::test_legacy_frozen_bytes_have_independent_literal_goldens`（903–938 行）  
  **本案では赤にならない見込み。変更不要。** literal 集合に今回変更する paired driver は含まれず、exact ファイル集合検査は headline ディレクトリ内だけ。そこへ新規ファイルを置けば赤になる。
- 提示されたテストファイルの他の既存 nodeid について、本案による必然的な失敗は静的読解では見つからない。pilot の pin・policy bytes・既存 golden は維持する。

テスト実走は親が行う。ここでは pytest の成功を報告しない。

## 未解決・親裁定へ返す項目

1. **scope の局所追加**：driver 1477–1485 行の十進文字列受理は、本番証明書を変更せず完了条件を満たすために必須。これを含めない場合、現行 validator を通る本番 policy は提示できない。
2. **実装案の凍結値**：配置規約に沿う path、`result_authority`、schedule root 原像・3値を上記案で確定する。README hash は本文確定後にのみ埋める。
3. **本走の実行面**：driver 7077–7079 行と job script 1362–1372 行の pilot 専用制約が残る。今回の完了を「本走起動可能」と書かず、証明書・policy の凍結完了として扱う。
4. **正式測定の認可**：[T-1505] に従い人間手番のまま。今回の成果物作成・受入を投入認可と解釈しない。

編集・新規作成・commit・branch 操作・計測投入は行っていない。