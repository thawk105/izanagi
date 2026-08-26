# B-10 待ち方 / 待ち量の直交切り分け — 事前登録

論文 `docs/paper-story/2026-08-26.md` §8 の **B-10「機序説明の帯域外への拡張」**のうち、
**「待ち方と待ち量の直交切り分け」** 1 項目の事前登録である。
B-10 の他の 3 項目 (過抑制域の機序、ピーク位置の再現、balanced workload の profile) は
本書の対象外であり、**未取得のまま残る**。

## 0. 本書の状態と発効条件

- **状態**: §5 の実測欄 (`physical_residual.values`) に `FILL_FROM_PROBE_RESULT…` の
  placeholder が残っている版は**発効しない**。driver の parser がこの placeholder を拒否する。
- **発効の手順**:
  1. placeholder 版を commit する。
  2. その commit を指して `--phase probe` を計算ノードで走らせ、
     待機ループの実経過サイクルを実測する。
  3. 実測値を §5 へ転記した版を commit する。**これが発効版である。**
  4. 本走 (`build` / `verify` / `perf` の各相) は発効版の commit を指して起動する。
- **本走成果物は発効版の commit hash を記録する。記録が無い実走は事前登録された実験として扱わない。**
- 発効後の変更は旧版を Git 履歴に残したまま新しい commit で行い、変更理由と変更時点を本書へ明記する。
  **結果 commit より後に書かれた変更は事前登録として数えない。**

## 1. 事前登録の効力とその限界

- ancestry が証明するのは「その bytes の文書がその時点に存在したこと」だけである。
  したがって driver は、文書の blob SHA・その commit・patch SHA・式 SHA・
  spec SHA・解析コード SHA を campaign lock と各 `BUILD_START` とブロック記録へ束縛し、
  束縛の無い / 食い違う既存 WAL への resume を拒否する。
- **「登録前に一度も性能を見ていない」と機械的に言えるのは formal driver 経路についてだけである。**
  driver を経由しない手動実行を repo 内の preflight で封じることはできない。
  一回限りの capability token による封鎖は本 wave の範囲外とし、裁定へ送った。

## 2. 何を分離する実験か

CCBench (silo) の backoff は、abort のたびに `_mm_pause()` の busy spin を
`clocks_per_us × now_backoff` サイクル回すだけの機構である。すなわち
**`now_backoff` が「待ち量」、spin の回し方が「待ち方」**である。

既存の静的 backoff sweep は `now_backoff` を定数に固定して量だけを振っており、
待ち方は「毎回きっかり同じ長さ待つ」1 種類に固定されていた。
したがって「backoff が効く」とは言えても、効いているのが**待つ総量**なのか
**待ち方 (retry の時間的なばらけ方)** なのかを分離できない。

本実験は、**指示する待ち量の平均を μ に固定したまま、待ち方 (ばらつき) だけを 3 段階に変える**。

| 形 | 指示値 | 構成上の平均 | ばらつき |
|---|---|---|---|
| `constant` | 常に μ | μ | 0 |
| `symmetric-modulo` | μ/2 〜 3μ/2 | μ | 中 |
| `binary` | μ/2 または 3μ/2 を確率 1/2 ずつ | μ | 大 |

平均が厳密に μ になる論拠は次のとおりである。撹拌器は奇数なので
`y = start × mixer (mod 2^64)` は全単射であり、`y` の最上位ビットと下位 63 ビットは独立で
最上位ビットはちょうど半々になる。`symmetric-modulo` は最上位ビットで
剰余 `r` と `2μ−r` を折り返して選ぶので、剰余の分布に偏りがあっても**対の平均は厳密に μ** である。
`binary` も同じ理由で厳密に半々である。

**どの形も待ち量 0 を指示しない** (最小は μ/2)。これは待機ループが 0 を指示されても
最低 1 回は `_mm_pause()` と `rdtscp()` を通るため、0 を含む形だと名目平均と物理平均が
形ごとに違ってずれるからである。半幅にすることでこのずれを構造的に小さくし、
残る差は §5 の実測で上界を押さえる。

## 3. 何を主張し、何を主張しないか

**書ける主張:**

- 48 スレッドの Silo / YCSB 3 workload、μ = 2〜100 µs の登録 grid において、
  **指示待ち量の構成上の平均を μ に揃えたとき、待ち方 (ばらつき) が throughput を動かすか**を
  事前登録した手続きで検定した。
- 有意な族については、方向・効果量・信頼区間を限定付きで述べる。
- 非有意なら「**この設計では検出しなかった**」とだけ述べる。

**書けない主張:**

- 物理的な実待機時間の平均を完全に同一化した (§5 の実測上界までしか言えない)。
- 差の機序が脱同期だけである (総待ち量 = 呼び出し回数 × μ も同時に動く)。
- 過抑制域の機序、ピーク位置の再現、balanced の profile を閉じた。
- 非有意だから待ち量だけで全部説明できる。
- 事前に定めた検出力の範囲内である (**検出力の保証はしない**。§6)。

## 4. 既知材料の開示 (登録追試であることの明示)

本実験は**既知の μ grid 上での前向きな形の拡張であり、登録追試である**。
着手前に次を閲覧していた。数値は本実験の材料に流用しない。

| 材料 | SHA-256 | 登録前に既知だった内容 |
|---|---|---|
| `output/campaigns/backoff-sweep-silo-write-heavy-sweep-493813a7/runs/wal.jsonl` | `9c179331a7171969ac6f4ed2b1d09e4afbf52378cfbac7bd133696a6589fe926` | 一定 10 µs が backoff 無しの +38.3288% |
| `output/campaigns/backoff-sweep-silo-balanced-sweep-484c663e/runs/wal.jsonl` | `8ac3f47e55274fada20e6518eea9cbb0e822170eeda1b424df99e76e11fd789c` | 一定 5 µs が backoff 無しの +11.2682% |
| `output/campaigns/backoff-sweep-silo-read-heavy-sweep-610004b9/runs/wal.jsonl` | `c74d5837a4facd071704a515f905d1d638463878850661cf217b96cd694774dc` | 最良でも backoff 無しの -6.6430% |
| `output/campaigns/backoff-repro-silo-balanced-repro-87dbbf50/runs/wal.jsonl` | `7afeac668c8ba678f651ef9cab33f95fb87879f0034c138065b243913bb1dc92` | 量の再測材料 |
| `output/campaigns/backoff-repro-silo-write-heavy-repro-181607af/runs/wal.jsonl` | `ea6f9e250960f1bccac3c6c8d5b5029bebebf01eee607e50493e8d6b2aa6f103` | 量の再測材料 |
| `output/env/pegasus/calibration/registered/calibration-94a4b79fa31bba3c.json` | `94a4b79fa31bba3c725bd9c18990ae60bea86dbcdb6eff19822a58a75fe5c5a9` | D15 の下限基準で選択、records 1,000,000、作業集合 / L3 = 4.9275、**miss 率は飽和していない** |
| `output/env/pegasus/calibration/between_run_noise_t48_skew0p9_rr95_rmw0.json` | `23c024e467559b238b58ef9c32c144f78d23cb48ad7aafd6bbc02cd108842ce7` | read-heavy の参考 floor 0.22% |
| `output/env/linux-baremetal/calibration/between_run_noise_t48_skew0p9_rr5_rmw0.json` | `200ab13614344769bbceaa4f7efe8c4411c4f6d764b3a5c036b77036498b9a11` | write-heavy の参考 floor 0.67% |
| `output/env/linux-baremetal/calibration/between_run_noise_t48_skew0p9_rr50_rmw0.json` | `4040eda140572ea0f79d1b16854fc1db84ed18b2de13d7eacdde25ce45971dc8` | balanced の参考 floor 1.07% |
| `output/env/linux-baremetal/calibration/between_run_noise_t48_skew0p9_rr95_rmw0.json` | `a6d1657885b2c855a797b71b8565e6c21d282bfb62c94395884b4ba1eac555c5` | read-heavy の参考 floor 0.11% (別環境) |

**レコード数は 1,000,000 とする。** 根拠は上記 calibration 成果物であり、
「cache miss 率が飽和した点」**ではない** (miss 率は単調上昇で飽和しない)。
D15 の下限基準に従い、作業集合が L3 の 4.93 倍になる最小点を採っている。

**曝露の最小値 10,000 回の根拠**も既存の実測である。2026-08-25 の Pegasus 計測で
`BACKOFF_FIXED=10` / write-heavy は 3 秒間に 984,942 回 abort している。
10,000 はその 2 桁下であり、backoff 経路がほとんど使われていないセルだけを弾く。

## 5. 機械可読 spec

以下の JSON が判定規則の**正本**である。driver はこれを全件 parse し、
コードの定数ではなくこの spec を引数として解析を行う。
`FILL_FROM_PROBE_RESULT…` は意図的な非数値 placeholder であり、
**そのままでは parser が拒否して本走に入れない**。
`maximum_absolute_deviation_pct_exclusive` の 1.0 は**実測を見る前に固定した値**であり、
probe の結果を見て変更しない。

<!-- IZANAGI-B10-SPEC-BEGIN -->
```json
{
  "schema_version": "izanagi-b10-backoff-shape-preregistration/v3",
  "artifacts": {
    "patch_sha256": "36cd974c56c6f103d894a53048ac734d9859def266c05898d3794d2c48470832",
    "formula_sha256": "5b3d8deefed35d05597891592d7af442c96b2fa094cdebc8376b2e9bc9cd7662"
  },
  "grid": {
    "means_us": [
      2,
      5,
      10,
      25,
      50,
      100
    ],
    "shapes": [
      {
        "name": "constant",
        "code": 0,
        "support": "mu"
      },
      {
        "name": "symmetric-modulo",
        "code": 1,
        "support": "closed-half-width-mu/2-through-3mu/2"
      },
      {
        "name": "binary",
        "code": 2,
        "support": "two-point-mu/2-or-3mu/2"
      }
    ],
    "encoding": "BACKOFF_FIXED=shape_code*1000+mu",
    "references": [
      {
        "name": "none",
        "back_off": 0,
        "backoff_fixed": -1
      },
      {
        "name": "adaptive",
        "back_off": 1,
        "backoff_fixed": -1
      },
      {
        "name": "zero-loop",
        "back_off": 1,
        "backoff_fixed": 0
      }
    ]
  },
  "blocks": {
    "count": 3,
    "ids": [
      "block-1",
      "block-2",
      "block-3"
    ],
    "run_order": {
      "block-1": [
        "none",
        "adaptive",
        "zero-loop",
        "constant-mu2",
        "symmetric-modulo-mu2",
        "binary-mu2",
        "symmetric-modulo-mu5",
        "binary-mu5",
        "constant-mu5",
        "binary-mu10",
        "constant-mu10",
        "symmetric-modulo-mu10",
        "constant-mu25",
        "symmetric-modulo-mu25",
        "binary-mu25",
        "symmetric-modulo-mu50",
        "binary-mu50",
        "constant-mu50",
        "binary-mu100",
        "constant-mu100",
        "symmetric-modulo-mu100"
      ],
      "block-2": [
        "adaptive",
        "zero-loop",
        "none",
        "symmetric-modulo-mu2",
        "binary-mu2",
        "constant-mu2",
        "binary-mu5",
        "constant-mu5",
        "symmetric-modulo-mu5",
        "constant-mu10",
        "symmetric-modulo-mu10",
        "binary-mu10",
        "symmetric-modulo-mu25",
        "binary-mu25",
        "constant-mu25",
        "binary-mu50",
        "constant-mu50",
        "symmetric-modulo-mu50",
        "constant-mu100",
        "symmetric-modulo-mu100",
        "binary-mu100"
      ],
      "block-3": [
        "zero-loop",
        "none",
        "adaptive",
        "binary-mu2",
        "constant-mu2",
        "symmetric-modulo-mu2",
        "constant-mu5",
        "symmetric-modulo-mu5",
        "binary-mu5",
        "symmetric-modulo-mu10",
        "binary-mu10",
        "constant-mu10",
        "binary-mu25",
        "constant-mu25",
        "symmetric-modulo-mu25",
        "constant-mu50",
        "symmetric-modulo-mu50",
        "binary-mu50",
        "symmetric-modulo-mu100",
        "binary-mu100",
        "constant-mu100"
      ]
    }
  },
  "workloads": [
    {
      "name": "write-heavy",
      "ycsb_zipf_skew": "0.9",
      "ycsb_rratio": "5",
      "ycsb_rmw": "0",
      "ycsb_max_ope": "10"
    },
    {
      "name": "balanced",
      "ycsb_zipf_skew": "0.9",
      "ycsb_rratio": "50",
      "ycsb_rmw": "0",
      "ycsb_max_ope": "10"
    },
    {
      "name": "read-heavy",
      "ycsb_zipf_skew": "0.9",
      "ycsb_rratio": "95",
      "ycsb_rmw": "0",
      "ycsb_max_ope": "10"
    }
  ],
  "execution": {
    "threads": 48,
    "extime_s": 3,
    "performance_reps": 5,
    "correctness_reps": 5,
    "correctness_mode": "legacy+performance",
    "screening": false
  },
  "analysis": {
    "alpha": 0.05,
    "holm_families": [
      {
        "workload": "write-heavy",
        "shape": "symmetric-modulo"
      },
      {
        "workload": "write-heavy",
        "shape": "binary"
      },
      {
        "workload": "balanced",
        "shape": "symmetric-modulo"
      },
      {
        "workload": "balanced",
        "shape": "binary"
      },
      {
        "workload": "read-heavy",
        "shape": "symmetric-modulo"
      },
      {
        "workload": "read-heavy",
        "shape": "binary"
      }
    ],
    "permutation": {
      "method": "exact-sign-flip",
      "sided": "two-sided",
      "statistic": "absolute-sum-paired-relative-effect",
      "enumeration": "all-2^18",
      "pairs_per_family": 18
    },
    "confidence_interval": {
      "method": "student-t-paired-block-mean",
      "confidence_level": 0.95,
      "degrees_of_freedom": 2,
      "critical_value": 4.302652729911275
    },
    "missingness": {
      "conditions": [
        "missing",
        "performance-error",
        "correctness-not-certified",
        "unstable",
        "underexposed"
      ],
      "pair_action": "invalidate-entire-family",
      "family_action": "indeterminate",
      "indeterminate_pvalue": 1.0
    },
    "exposure": {
      "metric": "sum-performance-rep-abort-counts",
      "minimum_calls_per_cell": 10000,
      "below_minimum_action": "indeterminate"
    },
    "equivalence_margin_pct": 3.0,
    "decision_procedure": [
      "construct-all-18-within-block-paired-relative-effects",
      "mark-family-indeterminate-on-any-unusable-pair",
      "enumerate-two-sided-sign-flip-pvalue-for-each-testable-family",
      "set-indeterminate-family-pvalue-to-1",
      "holm-adjust-all-six-families",
      "different-iff-testable-and-holm-p-less-than-or-equal-alpha",
      "otherwise-not-detected",
      "report-all-cell-effects-confidence-intervals-and-equivalence-relations"
    ]
  },
  "physical_residual": {
    "measurement": "realized-backoff-loop-cycles",
    "maximum_absolute_deviation_pct_exclusive": 1.0,
    "values": [
      {
        "shape": "constant",
        "mean_us": 2,
        "realized_mean_cycles": "FILL_FROM_PROBE_RESULT.cells[shape=constant,mean_us=2].realized_mean_cycles",
        "commanded_mean_cycles": "FILL_FROM_PROBE_RESULT.cells[shape=constant,mean_us=2].commanded_mean_cycles",
        "deviation_pct": "FILL_FROM_PROBE_RESULT.cells[shape=constant,mean_us=2].deviation_pct"
      },
      {
        "shape": "symmetric-modulo",
        "mean_us": 2,
        "realized_mean_cycles": "FILL_FROM_PROBE_RESULT.cells[shape=symmetric-modulo,mean_us=2].realized_mean_cycles",
        "commanded_mean_cycles": "FILL_FROM_PROBE_RESULT.cells[shape=symmetric-modulo,mean_us=2].commanded_mean_cycles",
        "deviation_pct": "FILL_FROM_PROBE_RESULT.cells[shape=symmetric-modulo,mean_us=2].deviation_pct"
      },
      {
        "shape": "binary",
        "mean_us": 2,
        "realized_mean_cycles": "FILL_FROM_PROBE_RESULT.cells[shape=binary,mean_us=2].realized_mean_cycles",
        "commanded_mean_cycles": "FILL_FROM_PROBE_RESULT.cells[shape=binary,mean_us=2].commanded_mean_cycles",
        "deviation_pct": "FILL_FROM_PROBE_RESULT.cells[shape=binary,mean_us=2].deviation_pct"
      },
      {
        "shape": "constant",
        "mean_us": 5,
        "realized_mean_cycles": "FILL_FROM_PROBE_RESULT.cells[shape=constant,mean_us=5].realized_mean_cycles",
        "commanded_mean_cycles": "FILL_FROM_PROBE_RESULT.cells[shape=constant,mean_us=5].commanded_mean_cycles",
        "deviation_pct": "FILL_FROM_PROBE_RESULT.cells[shape=constant,mean_us=5].deviation_pct"
      },
      {
        "shape": "symmetric-modulo",
        "mean_us": 5,
        "realized_mean_cycles": "FILL_FROM_PROBE_RESULT.cells[shape=symmetric-modulo,mean_us=5].realized_mean_cycles",
        "commanded_mean_cycles": "FILL_FROM_PROBE_RESULT.cells[shape=symmetric-modulo,mean_us=5].commanded_mean_cycles",
        "deviation_pct": "FILL_FROM_PROBE_RESULT.cells[shape=symmetric-modulo,mean_us=5].deviation_pct"
      },
      {
        "shape": "binary",
        "mean_us": 5,
        "realized_mean_cycles": "FILL_FROM_PROBE_RESULT.cells[shape=binary,mean_us=5].realized_mean_cycles",
        "commanded_mean_cycles": "FILL_FROM_PROBE_RESULT.cells[shape=binary,mean_us=5].commanded_mean_cycles",
        "deviation_pct": "FILL_FROM_PROBE_RESULT.cells[shape=binary,mean_us=5].deviation_pct"
      },
      {
        "shape": "constant",
        "mean_us": 10,
        "realized_mean_cycles": "FILL_FROM_PROBE_RESULT.cells[shape=constant,mean_us=10].realized_mean_cycles",
        "commanded_mean_cycles": "FILL_FROM_PROBE_RESULT.cells[shape=constant,mean_us=10].commanded_mean_cycles",
        "deviation_pct": "FILL_FROM_PROBE_RESULT.cells[shape=constant,mean_us=10].deviation_pct"
      },
      {
        "shape": "symmetric-modulo",
        "mean_us": 10,
        "realized_mean_cycles": "FILL_FROM_PROBE_RESULT.cells[shape=symmetric-modulo,mean_us=10].realized_mean_cycles",
        "commanded_mean_cycles": "FILL_FROM_PROBE_RESULT.cells[shape=symmetric-modulo,mean_us=10].commanded_mean_cycles",
        "deviation_pct": "FILL_FROM_PROBE_RESULT.cells[shape=symmetric-modulo,mean_us=10].deviation_pct"
      },
      {
        "shape": "binary",
        "mean_us": 10,
        "realized_mean_cycles": "FILL_FROM_PROBE_RESULT.cells[shape=binary,mean_us=10].realized_mean_cycles",
        "commanded_mean_cycles": "FILL_FROM_PROBE_RESULT.cells[shape=binary,mean_us=10].commanded_mean_cycles",
        "deviation_pct": "FILL_FROM_PROBE_RESULT.cells[shape=binary,mean_us=10].deviation_pct"
      },
      {
        "shape": "constant",
        "mean_us": 25,
        "realized_mean_cycles": "FILL_FROM_PROBE_RESULT.cells[shape=constant,mean_us=25].realized_mean_cycles",
        "commanded_mean_cycles": "FILL_FROM_PROBE_RESULT.cells[shape=constant,mean_us=25].commanded_mean_cycles",
        "deviation_pct": "FILL_FROM_PROBE_RESULT.cells[shape=constant,mean_us=25].deviation_pct"
      },
      {
        "shape": "symmetric-modulo",
        "mean_us": 25,
        "realized_mean_cycles": "FILL_FROM_PROBE_RESULT.cells[shape=symmetric-modulo,mean_us=25].realized_mean_cycles",
        "commanded_mean_cycles": "FILL_FROM_PROBE_RESULT.cells[shape=symmetric-modulo,mean_us=25].commanded_mean_cycles",
        "deviation_pct": "FILL_FROM_PROBE_RESULT.cells[shape=symmetric-modulo,mean_us=25].deviation_pct"
      },
      {
        "shape": "binary",
        "mean_us": 25,
        "realized_mean_cycles": "FILL_FROM_PROBE_RESULT.cells[shape=binary,mean_us=25].realized_mean_cycles",
        "commanded_mean_cycles": "FILL_FROM_PROBE_RESULT.cells[shape=binary,mean_us=25].commanded_mean_cycles",
        "deviation_pct": "FILL_FROM_PROBE_RESULT.cells[shape=binary,mean_us=25].deviation_pct"
      },
      {
        "shape": "constant",
        "mean_us": 50,
        "realized_mean_cycles": "FILL_FROM_PROBE_RESULT.cells[shape=constant,mean_us=50].realized_mean_cycles",
        "commanded_mean_cycles": "FILL_FROM_PROBE_RESULT.cells[shape=constant,mean_us=50].commanded_mean_cycles",
        "deviation_pct": "FILL_FROM_PROBE_RESULT.cells[shape=constant,mean_us=50].deviation_pct"
      },
      {
        "shape": "symmetric-modulo",
        "mean_us": 50,
        "realized_mean_cycles": "FILL_FROM_PROBE_RESULT.cells[shape=symmetric-modulo,mean_us=50].realized_mean_cycles",
        "commanded_mean_cycles": "FILL_FROM_PROBE_RESULT.cells[shape=symmetric-modulo,mean_us=50].commanded_mean_cycles",
        "deviation_pct": "FILL_FROM_PROBE_RESULT.cells[shape=symmetric-modulo,mean_us=50].deviation_pct"
      },
      {
        "shape": "binary",
        "mean_us": 50,
        "realized_mean_cycles": "FILL_FROM_PROBE_RESULT.cells[shape=binary,mean_us=50].realized_mean_cycles",
        "commanded_mean_cycles": "FILL_FROM_PROBE_RESULT.cells[shape=binary,mean_us=50].commanded_mean_cycles",
        "deviation_pct": "FILL_FROM_PROBE_RESULT.cells[shape=binary,mean_us=50].deviation_pct"
      },
      {
        "shape": "constant",
        "mean_us": 100,
        "realized_mean_cycles": "FILL_FROM_PROBE_RESULT.cells[shape=constant,mean_us=100].realized_mean_cycles",
        "commanded_mean_cycles": "FILL_FROM_PROBE_RESULT.cells[shape=constant,mean_us=100].commanded_mean_cycles",
        "deviation_pct": "FILL_FROM_PROBE_RESULT.cells[shape=constant,mean_us=100].deviation_pct"
      },
      {
        "shape": "symmetric-modulo",
        "mean_us": 100,
        "realized_mean_cycles": "FILL_FROM_PROBE_RESULT.cells[shape=symmetric-modulo,mean_us=100].realized_mean_cycles",
        "commanded_mean_cycles": "FILL_FROM_PROBE_RESULT.cells[shape=symmetric-modulo,mean_us=100].commanded_mean_cycles",
        "deviation_pct": "FILL_FROM_PROBE_RESULT.cells[shape=symmetric-modulo,mean_us=100].deviation_pct"
      },
      {
        "shape": "binary",
        "mean_us": 100,
        "realized_mean_cycles": "FILL_FROM_PROBE_RESULT.cells[shape=binary,mean_us=100].realized_mean_cycles",
        "commanded_mean_cycles": "FILL_FROM_PROBE_RESULT.cells[shape=binary,mean_us=100].commanded_mean_cycles",
        "deviation_pct": "FILL_FROM_PROBE_RESULT.cells[shape=binary,mean_us=100].deviation_pct"
      }
    ]
  },
  "external_floor_reference_widths": {
    "terminology": "external-floor-derived-reference-width",
    "power_guarantee": false,
    "values": [
      {
        "workload": "write-heavy",
        "between_run_cv_pct": 0.67,
        "reference_width_pct": 1.9,
        "source_environment": "linux-baremetal"
      },
      {
        "workload": "balanced",
        "between_run_cv_pct": 1.07,
        "reference_width_pct": 3.0,
        "source_environment": "linux-baremetal"
      },
      {
        "workload": "read-heavy",
        "between_run_cv_pct": 0.22,
        "reference_width_pct": 0.62,
        "source_environment": "pegasus"
      }
    ]
  }
}
```
<!-- IZANAGI-B10-SPEC-END -->

## 6. 検出力について主張しないこと

上の `external_floor_reference_widths` は**外部 floor 由来の参考幅**であり、
本実験が実装した検定 (18 対を束ねた両側 exact 符号反転検定 + 6 族 Holm) の検出力ではない。
検出力は効果の μ 間の向き、対の差の分散と相関、Holm の順位に依存するので、
片側の stock の変動係数だけからは単一の最小検出効果量にならない。
`power_guarantee` は `false` に固定している。

**したがって非有意のときに書けるのは「この設計では検出しなかった」までである。**
「事前に定めた検出力の範囲内で検出しなかった」とは書かない。
代わりに全セルの効果量と 95% 信頼区間を報告し、
等価範囲 ±3.0% に対して信頼区間が内側か、外側か、境界を跨ぐかを必ず明記する。

read-heavy の参考幅は Pegasus の実測 (0.22%) を使う。
linux-baremetal の 0.11% は別環境の値なので参考として併記するに留める。

## 7. 実行と正しさ

- 相は `probe` → `build` → `verify` → `perf` の順に分ける。
  `verify` と `perf` は workload ごとに分ける。事前登録束縛が一致する WAL は再開できる。
- **性能計測は trace 無効ビルド、正しさ検証は trace 有効ビルドの別 run** で行う (絶対規律 1)。
  既存 pipeline が同じ genome / source から trace 有無の 2 つを別々に build し、
  verify は trace binary、bench は trace 無効 binary で走る。
  `IZANAGI_TRACE_DIR` は perf 側にも対称に設定され、環境変数の有無自体が判別子にならない。
- **verifier が anomaly を返した variant は即 reject する** (絶対規律 2)。
  bench へ到達させず fitness も付けない。正しさ検証の反復回数は 5 回で、
  実行時間を理由に減らさない。
- 性能測定に使う binary は、正しさを認証した attempt の binary の SHA-256 と完全一致させる。
  一致しないセルは bench へ送らず判定不能とする。
- perf に依存する診断は本実験の範囲外とする (この計算ノードに perf は無い)。

## 8. 報告に必ず含めるもの

- 全セルの中央値 throughput、反復のばらつき、abort 率、
  **backoff 呼び出し回数 (= abort 回数)**、毎秒呼び出し回数、
  **名目総待ち量 (= 呼び出し回数 × μ)**、正しさの認証状態。
- 全 workload の結果を退行込みで報告する。対象 workload で勝っても、
  他 workload で退行があれば退行込みで全件報告する。
- 判定不能セル・判定不能族は、分母から消さずに判定不能として明示する。
- 本走で使った発効版 commit hash、patch SHA、式 SHA、spec SHA、解析コード SHA。

## 9. 本書が閉じない B-10 の残り

- 過抑制域の機序
- ピーク位置の再現
- balanced workload の profile
- 実走での要求待ち量そのものの分布 (分位点・自己相関・スレッド間同時値率) の診断

これらは未取得のまま残る。本書の結果をもってこれらが閉じたと書いてはならない。
