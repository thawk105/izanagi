採用案は **P2・P3・P5 の値を維持し、P1 の spec 名に campaign 成分を追加する**形です。P4 の seed 式は維持しますが、無作為化の射程と非保証を訂正します。3 本を同じ commit で凍結し、集約対象も測定前に固定します。

これは静的な起草結果です。ファイル変更、commit、binder 実走、pytest は行っていません。読み取り時の worktree HEAD と local main は、ともに `d2ebef7a407dc6be61622ed596cf08b8b518f606` でした。

以下の参照略号は、この worktree 内のファイルを指します。

- **F** = [orchestrator/campaign/floor_pair_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-a5-freeze/orchestrator/campaign/floor_pair_driver.py)
- **I** = [orchestrator/campaign/p3_b4_floor_artifact_issuer.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-a5-freeze/orchestrator/campaign/p3_b4_floor_artifact_issuer.py)
- **T** = [orchestrator/tests/test_floor_pair_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-a5-freeze/orchestrator/tests/test_floor_pair_driver.py)
- **S** = `orchestrator/campaign/s8b_holdout_freeze.py`
- **V** = `/home/SFC/tanab/.claude/jobs/05e7e471/tmp/dev-wave-t2288-a5-freeze/verbatim/`

## 1. 採用する完全な JSON

以下は現在の HEAD を凍結 commit の親とする場合の完全な内容です。**main 取り込みで親が変わった場合は、3 本すべての `source_commit` と seed を再計算します。** 日付や campaign を結果に応じて変更する手順にはしません。

保存 bytes は、各 JSON を読み込んで次の形式で再直列化したものに統一します。以下の表示上の改行・空白から直接 hash を取らないでください。

```python
raw = (
    json.dumps(
        document, sort_keys=True, indent=2,
        ensure_ascii=False, allow_nan=False
    ) + "\n"
).encode("utf-8")
```

### rr95

配置先:

```text
output/env/pegasus/floor-pair/t2288-f1/spec__env-pegasus__protocol-silo__threads-48__workload-rr95-s0.9-rmw0__campaign-t2288-f1-rr95-c1c2.json
```

```json
{
  "schema": "floor-pair-spec/v3",
  "provenance": {
    "source_commit": "d2ebef7a407dc6be61622ed596cf08b8b518f606",
    "calibration": {
      "attestation_mode": "required",
      "path": "output/env/pegasus/calibration/registered/calibration-5c836a22eff9ab40.json",
      "sha256": "5c836a22eff9ab40cabb23cb597cd0b3c232979696c5784b6b3d358b92c789cc"
    }
  },
  "environment": {
    "site": "PEGASUS_COMPUTE",
    "env_tag": "pegasus",
    "clocks_per_us": 2100,
    "numactl_argv": [],
    "use_perf": false,
    "timeout_s": 120,
    "extra_env": {},
    "probe_timeout_s": 30
  },
  "artifacts": [
    {
      "artifact_id": "b4-candidate",
      "binary_relpath": "output/env/pegasus/binaries/7cdf0dc345f7eccdb50604e77521ce625c1792cc0eb8966b544f65a15ef274a4",
      "binary_sha256": "7cdf0dc345f7eccdb50604e77521ce625c1792cc0eb8966b544f65a15ef274a4",
      "build_receipt": {
        "path": "output/insights/2026-09-16/t2636-b4-binary-record/records/rr20--stock_common.json",
        "sha256": "760287f629ee96c5c0e31c43be7b6dc30bfbf48dd5ebbe4c0da8b5b0b3e389b0"
      },
      "trace": false
    },
    {
      "artifact_id": "b4-reference",
      "binary_relpath": "output/env/pegasus/binaries/7cdf0dc345f7eccdb50604e77521ce625c1792cc0eb8966b544f65a15ef274a4",
      "binary_sha256": "7cdf0dc345f7eccdb50604e77521ce625c1792cc0eb8966b544f65a15ef274a4",
      "build_receipt": {
        "path": "output/insights/2026-09-16/t2636-b4-binary-record/records/rr20--stock_common.json",
        "sha256": "760287f629ee96c5c0e31c43be7b6dc30bfbf48dd5ebbe4c0da8b5b0b3e389b0"
      },
      "trace": false
    }
  ],
  "cells": [
    {
      "cell_id": "rr95-t48-s0.9-rmw0",
      "perf_config": {
        "records": 1000000,
        "threads": 48,
        "extime": 3,
        "reps": 5,
        "ycsb_max_ope": 10,
        "workload": {
          "ycsb_rmw": "0",
          "ycsb_rratio": "95",
          "ycsb_zipf_skew": "0.9"
        }
      }
    }
  ],
  "pairs": [
    {
      "pair_id": "pair-rr95",
      "cell_id": "rr95-t48-s0.9-rmw0",
      "reference_artifact_id": "b4-reference",
      "sides": [
        {
          "side_id": "candidate_1",
          "candidate_artifact_id": "b4-candidate"
        },
        {
          "side_id": "candidate_2",
          "candidate_artifact_id": "b4-candidate"
        }
      ]
    }
  ],
  "windows": [
    {
      "window_id": "rr95-w1",
      "campaign_id": "t2288-f1-rr95-c1",
      "not_before": "2026-09-19T00:00:00Z",
      "not_after": "2026-09-27T00:00:00Z",
      "sample_count": 62,
      "pair_ids": ["pair-rr95"],
      "artifact_relpath": "output/env/pegasus/floor-pair/t2288-f1/window__env-pegasus__protocol-silo__threads-48__workload-rr95-s0.9-rmw0__campaign-t2288-f1-rr95-c1.jsonl"
    },
    {
      "window_id": "rr95-w2",
      "campaign_id": "t2288-f1-rr95-c2",
      "not_before": "2026-09-28T00:00:00Z",
      "not_after": "2026-10-06T00:00:00Z",
      "sample_count": 62,
      "pair_ids": ["pair-rr95"],
      "artifact_relpath": "output/env/pegasus/floor-pair/t2288-f1/window__env-pegasus__protocol-silo__threads-48__workload-rr95-s0.9-rmw0__campaign-t2288-f1-rr95-c2.jsonl"
    }
  ],
  "randomization": {
    "algorithm": "hmac-sha256-rank/v1",
    "seed_hex": "7fa738507efad5105c6545e85bacde4f21c36a95e3c7b654b2e145077a9bf99e"
  },
  "statistics": {
    "session_reducer": "median/v1",
    "stratum_upper": "sample_max/v1",
    "closed_strata": [
      {"window_id": "rr95-w1", "pair_id": "pair-rr95"},
      {"window_id": "rr95-w2", "pair_id": "pair-rr95"}
    ],
    "final_combiner": "max_over_closed_strata/v1",
    "reference_measurements_per_pair_sample": 2,
    "difference_formula": "D=abs((median(candidate_1)/median(reference_1)-1)-(median(candidate_2)/median(reference_2)-1))"
  },
  "failure_policy": {
    "policy": "d1641-drop-and-count-max-5pct/v1",
    "retry_count": 0,
    "require_all_reps": true,
    "max_dropped_fraction": "1/20"
  },
  "outputs": {
    "window_format": "floor-pair-jsonl/v1",
    "summary_format": "floor-pair-summary-json/v1",
    "summary_relpath": "output/env/pegasus/floor-pair/t2288-f1/summary__env-pegasus__protocol-silo__threads-48__workload-rr95-s0.9-rmw0__campaign-t2288-f1-rr95-c1c2.json"
  }
}
```

### rr50

配置先:

```text
output/env/pegasus/floor-pair/t2288-f1/spec__env-pegasus__protocol-silo__threads-48__workload-rr50-s0.9-rmw0__campaign-t2288-f1-rr50-c1c2.json
```

```json
{
  "schema": "floor-pair-spec/v3",
  "provenance": {
    "source_commit": "d2ebef7a407dc6be61622ed596cf08b8b518f606",
    "calibration": {
      "attestation_mode": "required",
      "path": "output/env/pegasus/calibration/registered/calibration-94a4b79fa31bba3c.json",
      "sha256": "94a4b79fa31bba3c725bd9c18990ae60bea86dbcdb6eff19822a58a75fe5c5a9"
    }
  },
  "environment": {
    "site": "PEGASUS_COMPUTE",
    "env_tag": "pegasus",
    "clocks_per_us": 2100,
    "numactl_argv": [],
    "use_perf": false,
    "timeout_s": 120,
    "extra_env": {},
    "probe_timeout_s": 30
  },
  "artifacts": [
    {
      "artifact_id": "b4-candidate",
      "binary_relpath": "output/env/pegasus/binaries/7cdf0dc345f7eccdb50604e77521ce625c1792cc0eb8966b544f65a15ef274a4",
      "binary_sha256": "7cdf0dc345f7eccdb50604e77521ce625c1792cc0eb8966b544f65a15ef274a4",
      "build_receipt": {
        "path": "output/insights/2026-09-16/t2636-b4-binary-record/records/rr20--stock_common.json",
        "sha256": "760287f629ee96c5c0e31c43be7b6dc30bfbf48dd5ebbe4c0da8b5b0b3e389b0"
      },
      "trace": false
    },
    {
      "artifact_id": "b4-reference",
      "binary_relpath": "output/env/pegasus/binaries/7cdf0dc345f7eccdb50604e77521ce625c1792cc0eb8966b544f65a15ef274a4",
      "binary_sha256": "7cdf0dc345f7eccdb50604e77521ce625c1792cc0eb8966b544f65a15ef274a4",
      "build_receipt": {
        "path": "output/insights/2026-09-16/t2636-b4-binary-record/records/rr20--stock_common.json",
        "sha256": "760287f629ee96c5c0e31c43be7b6dc30bfbf48dd5ebbe4c0da8b5b0b3e389b0"
      },
      "trace": false
    }
  ],
  "cells": [
    {
      "cell_id": "rr50-t48-s0.9-rmw0",
      "perf_config": {
        "records": 1000000,
        "threads": 48,
        "extime": 3,
        "reps": 5,
        "ycsb_max_ope": 10,
        "workload": {
          "ycsb_rmw": "0",
          "ycsb_rratio": "50",
          "ycsb_zipf_skew": "0.9"
        }
      }
    }
  ],
  "pairs": [
    {
      "pair_id": "pair-rr50",
      "cell_id": "rr50-t48-s0.9-rmw0",
      "reference_artifact_id": "b4-reference",
      "sides": [
        {
          "side_id": "candidate_1",
          "candidate_artifact_id": "b4-candidate"
        },
        {
          "side_id": "candidate_2",
          "candidate_artifact_id": "b4-candidate"
        }
      ]
    }
  ],
  "windows": [
    {
      "window_id": "rr50-w1",
      "campaign_id": "t2288-f1-rr50-c1",
      "not_before": "2026-09-19T00:00:00Z",
      "not_after": "2026-09-27T00:00:00Z",
      "sample_count": 62,
      "pair_ids": ["pair-rr50"],
      "artifact_relpath": "output/env/pegasus/floor-pair/t2288-f1/window__env-pegasus__protocol-silo__threads-48__workload-rr50-s0.9-rmw0__campaign-t2288-f1-rr50-c1.jsonl"
    },
    {
      "window_id": "rr50-w2",
      "campaign_id": "t2288-f1-rr50-c2",
      "not_before": "2026-09-28T00:00:00Z",
      "not_after": "2026-10-06T00:00:00Z",
      "sample_count": 62,
      "pair_ids": ["pair-rr50"],
      "artifact_relpath": "output/env/pegasus/floor-pair/t2288-f1/window__env-pegasus__protocol-silo__threads-48__workload-rr50-s0.9-rmw0__campaign-t2288-f1-rr50-c2.jsonl"
    }
  ],
  "randomization": {
    "algorithm": "hmac-sha256-rank/v1",
    "seed_hex": "d956c31f4b17552463838626f80768873aa2c9f15757804c2e3989a228e3eb73"
  },
  "statistics": {
    "session_reducer": "median/v1",
    "stratum_upper": "sample_max/v1",
    "closed_strata": [
      {"window_id": "rr50-w1", "pair_id": "pair-rr50"},
      {"window_id": "rr50-w2", "pair_id": "pair-rr50"}
    ],
    "final_combiner": "max_over_closed_strata/v1",
    "reference_measurements_per_pair_sample": 2,
    "difference_formula": "D=abs((median(candidate_1)/median(reference_1)-1)-(median(candidate_2)/median(reference_2)-1))"
  },
  "failure_policy": {
    "policy": "d1641-drop-and-count-max-5pct/v1",
    "retry_count": 0,
    "require_all_reps": true,
    "max_dropped_fraction": "1/20"
  },
  "outputs": {
    "window_format": "floor-pair-jsonl/v1",
    "summary_format": "floor-pair-summary-json/v1",
    "summary_relpath": "output/env/pegasus/floor-pair/t2288-f1/summary__env-pegasus__protocol-silo__threads-48__workload-rr50-s0.9-rmw0__campaign-t2288-f1-rr50-c1c2.json"
  }
}
```

### rr5

配置先:

```text
output/env/pegasus/floor-pair/t2288-f1/spec__env-pegasus__protocol-silo__threads-48__workload-rr5-s0.9-rmw0__campaign-t2288-f1-rr5-c1c2.json
```

```json
{
  "schema": "floor-pair-spec/v3",
  "provenance": {
    "source_commit": "d2ebef7a407dc6be61622ed596cf08b8b518f606",
    "calibration": {
      "attestation_mode": "required",
      "path": "output/env/pegasus/calibration/registered/calibration-2b7ba072b88023ae.json",
      "sha256": "2b7ba072b88023aecb4361781229bb5343dbfa489f4c7cc3dd8369c33bd3a067"
    }
  },
  "environment": {
    "site": "PEGASUS_COMPUTE",
    "env_tag": "pegasus",
    "clocks_per_us": 2100,
    "numactl_argv": [],
    "use_perf": false,
    "timeout_s": 120,
    "extra_env": {},
    "probe_timeout_s": 30
  },
  "artifacts": [
    {
      "artifact_id": "b4-candidate",
      "binary_relpath": "output/env/pegasus/binaries/7cdf0dc345f7eccdb50604e77521ce625c1792cc0eb8966b544f65a15ef274a4",
      "binary_sha256": "7cdf0dc345f7eccdb50604e77521ce625c1792cc0eb8966b544f65a15ef274a4",
      "build_receipt": {
        "path": "output/insights/2026-09-16/t2636-b4-binary-record/records/rr20--stock_common.json",
        "sha256": "760287f629ee96c5c0e31c43be7b6dc30bfbf48dd5ebbe4c0da8b5b0b3e389b0"
      },
      "trace": false
    },
    {
      "artifact_id": "b4-reference",
      "binary_relpath": "output/env/pegasus/binaries/7cdf0dc345f7eccdb50604e77521ce625c1792cc0eb8966b544f65a15ef274a4",
      "binary_sha256": "7cdf0dc345f7eccdb50604e77521ce625c1792cc0eb8966b544f65a15ef274a4",
      "build_receipt": {
        "path": "output/insights/2026-09-16/t2636-b4-binary-record/records/rr20--stock_common.json",
        "sha256": "760287f629ee96c5c0e31c43be7b6dc30bfbf48dd5ebbe4c0da8b5b0b3e389b0"
      },
      "trace": false
    }
  ],
  "cells": [
    {
      "cell_id": "rr5-t48-s0.9-rmw0",
      "perf_config": {
        "records": 2000000,
        "threads": 48,
        "extime": 3,
        "reps": 5,
        "ycsb_max_ope": 10,
        "workload": {
          "ycsb_rmw": "0",
          "ycsb_rratio": "5",
          "ycsb_zipf_skew": "0.9"
        }
      }
    }
  ],
  "pairs": [
    {
      "pair_id": "pair-rr5",
      "cell_id": "rr5-t48-s0.9-rmw0",
      "reference_artifact_id": "b4-reference",
      "sides": [
        {
          "side_id": "candidate_1",
          "candidate_artifact_id": "b4-candidate"
        },
        {
          "side_id": "candidate_2",
          "candidate_artifact_id": "b4-candidate"
        }
      ]
    }
  ],
  "windows": [
    {
      "window_id": "rr5-w1",
      "campaign_id": "t2288-f1-rr5-c1",
      "not_before": "2026-09-19T00:00:00Z",
      "not_after": "2026-09-27T00:00:00Z",
      "sample_count": 62,
      "pair_ids": ["pair-rr5"],
      "artifact_relpath": "output/env/pegasus/floor-pair/t2288-f1/window__env-pegasus__protocol-silo__threads-48__workload-rr5-s0.9-rmw0__campaign-t2288-f1-rr5-c1.jsonl"
    },
    {
      "window_id": "rr5-w2",
      "campaign_id": "t2288-f1-rr5-c2",
      "not_before": "2026-09-28T00:00:00Z",
      "not_after": "2026-10-06T00:00:00Z",
      "sample_count": 62,
      "pair_ids": ["pair-rr5"],
      "artifact_relpath": "output/env/pegasus/floor-pair/t2288-f1/window__env-pegasus__protocol-silo__threads-48__workload-rr5-s0.9-rmw0__campaign-t2288-f1-rr5-c2.jsonl"
    }
  ],
  "randomization": {
    "algorithm": "hmac-sha256-rank/v1",
    "seed_hex": "b011f2af789c63afbf206f69fee0c2bd1e202dc36dcd06cf5c943d4a3074094f"
  },
  "statistics": {
    "session_reducer": "median/v1",
    "stratum_upper": "sample_max/v1",
    "closed_strata": [
      {"window_id": "rr5-w1", "pair_id": "pair-rr5"},
      {"window_id": "rr5-w2", "pair_id": "pair-rr5"}
    ],
    "final_combiner": "max_over_closed_strata/v1",
    "reference_measurements_per_pair_sample": 2,
    "difference_formula": "D=abs((median(candidate_1)/median(reference_1)-1)-(median(candidate_2)/median(reference_2)-1))"
  },
  "failure_policy": {
    "policy": "d1641-drop-and-count-max-5pct/v1",
    "retry_count": 0,
    "require_all_reps": true,
    "max_dropped_fraction": "1/20"
  },
  "outputs": {
    "window_format": "floor-pair-jsonl/v1",
    "summary_format": "floor-pair-summary-json/v1",
    "summary_relpath": "output/env/pegasus/floor-pair/t2288-f1/summary__env-pegasus__protocol-silo__threads-48__workload-rr5-s0.9-rmw0__campaign-t2288-f1-rr5-c1c2.json"
  }
}
```

上記の内容を指定の直列化で生成した場合の計算値は次のとおりです。これは **binder 成功の証拠ではなく、予定 bytes の照合値**です。

| spec | bytes | SHA-256 |
|---|---:|---|
| rr95 | 4306 | `4cea0b521e5f0cbee1d120d68a0800bbe179384d5ada8361c1d9ff8a16d6115c` |
| rr50 | 4306 | `f13b08339c21aec4d9d0c82e7e54133dc81c6f3d14f12d4d51f4e84492a8c16a` |
| rr5 | 4286 | `bc6817b3bb5b5fce4fad5c68cc6039844ad304fdf2967b07675f6f3a3a35ff5b` |

## 2. loader との照合と既決値の継承

各 object の exact key 集合を次のとおり照合しました。表の集合以外に、説明用 field を足してはいけません。

| 対象 | 必須 exact key 集合 | 型・値・参照条件と照合結果 |
|---|---|---|
| root | `schema, provenance, environment, artifacts, cells, pairs, windows, randomization, statistics, failure_policy, outputs` | 11 key。schema は v3。`protocol` 等を追加しない。F:1239、T:798、T:816 |
| provenance | `calibration, source_commit` | source は lowercase 40 hex。現在値は一致。commit 後の真の祖先であることは実走で確認。F:660、F:1290 |
| calibration | `path, sha256, attestation_mode` | canonical relpath、lowercase 64 hex、`required`。`none` は parse できても較正なしで binder が拒否。F:647、F:1158 |
| environment | `site, env_tag, clocks_per_us, numactl_argv, use_perf, timeout_s, extra_env, probe_timeout_s` | site は列挙値、env_tag は ID、数値は正の exact int、argv は string list、env は string map。`false` と `{}` は適合。F:692 |
| artifact | `artifact_id, binary_relpath, binary_sha256, build_receipt, trace` | ID 重複なし、trace は exact false。receipt は `path, sha256`。F:639、F:739 |
| cell | `cell_id, perf_config` | 1 cell。ID 重複なし。F:798 |
| perf_config | `records, threads, workload, extime, reps, ycsb_max_ope` | 数値は正の exact int。workload は `ycsb_rmw, ycsb_rratio, ycsb_zipf_skew` の非空 string 3 key。F:775 |
| pair | `pair_id, cell_id, reference_artifact_id, sides` | side は exact 2 件。各 side は `side_id, candidate_artifact_id`。両 side は同じ candidate ID、reference は別 ID。F:818 |
| window | `window_id, campaign_id, not_before, not_after, sample_count, pair_ids, artifact_relpath` | 窓・campaign ID は spec 内一意、pair 列は非空・重複なし、sample_count は正の exact int。F:869 |
| randomization | `algorithm, seed_hex` | 定数 ID と lowercase 64 hex。F:928 |
| statistics | `session_reducer, stratum_upper, closed_strata, final_combiner, reference_measurements_per_pair_sample, difference_formula` | 定数文字列、参照数 exact int 2。stratum は `window_id, pair_id`、重複なし。F:937 |
| failure_policy | `policy, retry_count, require_all_reps, max_dropped_fraction` | 定数 ID、exact int 0、exact true、文字列 `"1/20"`。F:996 |
| outputs | `window_format, summary_format, summary_relpath` | format ID は **v1 のまま**。schema v3 に合わせて改名しない。F:1033 |

補足条件も以下を満たす構成です。

- **識別子:** 現在の `_ID_RE` は F:**92** の `[A-Za-z0-9][A-Za-z0-9._-]{0,127}`。指定資料の「87 行」は古い行番号です。今回の ID はすべて適合します。ファイル名全体を ID として検査する規則ではありません。
- **日時:** 末尾 `Z`、非空の半開区間、各 8 日、非重複です。日時 parser 自体は `datetime.fromisoformat` を使うため、一般的な RFC3339 全体の厳密 validator と説明しません。F:470、F:892。
- **相対 path:** 絶対 path、`./`、`..`、連続 slash、末尾 slash を使わず、`Path(text).as_posix() == text` を満たします。F:460。
- **出力親:** `output/env/pegasus/floor-pair/t2288-f1/` が実在する非 symlink directory である必要があります。tracked spec を同居させる案で checkout 後も確保できます。F:489、F:517。
- **出力 leaf:** loader は既存の通常 leaf を一律には拒否しません。create-only で失敗するのは発行時です。したがって凍結時にも予定出力が未使用であることを人手確認し、既存物の削除・改名で空けません。F:527、F:1685。
- **閉包:** 各 pair の cell・artifact 参照、各 window の pair 参照、`closed_strata` と全予定 `(window_id, pair_id)` の exact 一致を満たします。F:1060。
- **束縛:** spec・較正・receipt の tracked blob 一致、期待 hash、binary 現物 hash、較正 accepted と設定一致は静的 JSON だけでは証明できません。親の実走が必要です。F:1122、F:1197。

既決値の継承については次の結論です。

| 項目 | 継承結果 |
|---|---|
| artifacts 2 entry | 指定された旧 JSON の path・hash・receipt を維持。別 artifact ID で同じ bytes を共有する形は D2069 に適合。V/D2069.md:5、F:851 |
| perf_config | `extime=3, reps=5, ycsb_max_ope=10` を維持。`reps=5` は較正出力の転記ではなく AI の承認値。V/D2088.md:8、:17 |
| cells | workload 3 key の文字列を逐語維持。rr95/rr50 の records は 1000000、rr5 は 2000000。V/D2089.md:11 |
| calibration | 指定 3 件の path/hash と `required` を維持。選択規則をやり直さない。V/D2090.md:33 |
| statistics | 差の式・参照 2 件・各統計 ID は F:60–73 の値と一致。窓 ID だけ本案に置換 |
| failure_policy | F:64–66 と一致。campaign 合算の 5% を維持し、pair 別閾値を追加しない |
| outputs format | F:67–68 と逐語一致。summary 本体 schema と format ID の版を混同しない |

**D2088 の「spec の非保証欄」には schema 上の受け皿がありません。** 未知 key は拒否されるので `non_guarantees` を JSON に追加せず、AI が選んだ reps の説明を decisions と insight に残します。これは実装を変えずに処理すべき文書上の不整合です。V/D2088.md:22、F:1239、T:798。

## 3. A-5 の根拠・代案・brief の訂正

**P1：命名**

窓と summary の元案は D1641 の 5 成分を持っています。spec 名には campaign 成分がなかったため、本案では `__campaign-t2288-f1-<wl>-c1c2` を加えました。

ただし、**元の spec 名が D1641 違反だったとは断定しません。** precheck insight は D1641 の対象を成果物の命名とし、spec path は今回の選択と区別しています。本変更は対応を読み取りやすくするためです。`output/insights/2026-09-17/t2288-binder-precheck/README.md:96`。

issuer は `b4-floor__...` と `b4-floor-aggregate__...` を生成します。本案の `spec__`・`window__`・`summary__` と衝突しません。ただし issuer の workload/campaign 部分は独自に導出されるため、**「同じ識別子生成規則」ではなく、区切り様式を揃えた**と記録します。I:749、I:948、I:1226。

**P2：日時と 24 h 分離**

共通の 8 日窓を採用します。これは後続実装・queue 待ちに幅を持たせる運用上の選択であり、必要時間を実測から保証した値ではありません。

開始時刻を \(s_1,s_2\) とすると、

```text
s1 < 2026-09-27T00:00:00Z
s2 >= 2026-09-28T00:00:00Z
したがって s2 - s1 > 24 h
```

です。しかし F:2091 が検査するのは **session 開始**です。終了が `not_after` を越えない保証はありません。したがって brief の「任意の session が >24 h 離れる」「人手確認は式で閉じる」は強すぎます。

採用案では、決定記録に次を明記します。

> 許容開始時刻帯に 24 h の隙間を設ける。実際の campaign 分離は後続の証拠確認で確認する。終了から次の開始までの 24 h 分離を loader が証明したとは扱わない。

代案は w2 をさらに 1 日遅らせる形ですが、それでも終了時刻の機械保証にはなりません。現時点では日程を増やす根拠が薄いため採りません。D1974 の人手責任を維持します。V/D1974.md:3、F:2091。

また、凍結が遅れてこの予定を使えなくなった場合は、未実施の計画として扱い、結果を見ながら窓を延長する運用にしません。

**P3：ID**

元案を採用します。campaign は全 6 件で相異、window は workload ごとに区別し、pair/cell は対応が読み取れます。集約器は workload 間で同じ window ID を要求しません。各 spec にちょうど 2 窓を要求し、各 summary を当該 spec の閉包と照合します。I:1063、I:1077。

**P4：seed**

次の公開式を採用します。入力末尾に改行は加えません。

```text
SHA256(
  UTF8(
    "izanagi floor-pair-spec/v3 seed|"
    + spec_relpath
    + "|"
    + source_commit
  )
)
```

上記 3 seed はこの式で計算済みです。値を変えるために親 commit や path を試行選別しません。

brief の「side 順序だけ」は誤りです。HMAC は以下すべてを決めます。

1. window 内の pair/sample 順序。
2. 各 sample の side session 順序。
3. 各 side session 内の candidate/reference 測定順序。

根拠は F:1352、F:1366、F:1378。「同じ binary なので有利な選択が存在しない」も削除します。同じ bytes でも時刻・実行順序・失敗との関係は残ります。公開式は再現性を与えますが、独立した乱数抽選や事前性の機械証明ではありません。

代案として source commit に依存しない固定文字列からの seed も可能ですが、今回の式を変更する必要はありません。

**P5：実行設定**

`timeout_s=120`、`probe_timeout_s=30`、`numactl_argv=[]`、`extra_env={}`、`use_perf=false` を採用します。ただし、既裁定の数値と区別して **今回の運用設定の選択**として記録します。

- parser は timeout に正の exact int を要求するだけです。120 と 600 のどちらを統計的に正当とする機構もありません。F:731。
- `timeout_s` と空 argv は runner へ渡されます。`numactl_argv=[]` は spec の exact 値であり、較正時の `None` という表現と同一だと説明しません。F:1597。
- brief の rep wall・NUMA・`BENCH_TIMEOUT_S` の取得元は、本段では独立に実測確認していません。**brief の報告値**として扱います。
- NUMA 1 node の較正記録があっても、将来の割当て・CPU affinity・環境全体の同一性は保証しません。
- 120 秒を 4.5 秒で割った約 26.7 倍という算術は、timeout 成功率の根拠にはなりません。

代案の 600 秒は受理されますが、旧仮置き値を先例として戻す根拠はありません。120 秒を後続実測の結果に応じて途中変更しないことを記録します。

**費用と P8**

1 spec・1 窓は 124 session × 2 測定 × 5 rep = **1240 rep**。brief の 3.5–4.5 秒を仮に適用すれば、bench 部分は **約 1.21–1.55 時間**です。probe・起動・I/O 等を含めた「1 窓 1.6 時間」の上限にはできません。

名目 extime だけなら 1 窓 3720 秒、3 spec・2 窓で **22320 秒＝6.2 時間**です。これも総 wall time や §5 の承認済み予算を表しません。V/prereg-11.2.md:62。

共通窓は逐次実行にも使えます。「3 cell を別 node で並走できる」は資源確保・admission に依存する**推測**であり、凍結による保証から外します。

## 4. 集約への対応

凍結時に、次を decisions fragment の通常の表として記録し、insight に再現手順を置きます。新しい JSON manifest や台帳は作りません。

| 記録対象 | 確定内容 |
|---|---|
| `expected_specs` | §1 の 3 spec の **完全な relpath と実 bytes の SHA-256**。表示順は rr95、rr50、rr5 とする |
| `summary_paths` | 各 spec の `outputs.summary_relpath` に示した 3 path |
| `output_dir` | `output/env/pegasus/floor-pair/t2288-f1/` |
| 対象集合 | D2089 の 3 cell × 各 2 窓、各窓 1 pair × 62 sample |
| identity | env=pegasus、protocol=silo、threads=48。protocol は後続 issuer が receipt から導出する |
| 発行結果 | 全入力の保守側最大を 1 件。非生成・不一致・欠落時に正常入力だけへ間引かない |

§1 の親・bytes が維持される場合、期待 pin は同節の hash 3 件です。**summary から期待 spec 列を作らない**ことを、後続への申し送りに明記します。

I:1036 は path 重複と hash 不一致を拒否し、driver を通して各 spec を束縛します。I:1069 は窓・campaign・層・cell・標本の閉包を照合し、retained/dropped による予定標本の分割まで要求します。I:1159 は各 spec に対応する summary がちょうど 1 件ずつあることを要求します。I:1185 は env/protocol/threads 一致を要求します。

集約名は以下です。今回、issuer と同じ直列化式を用いて標準ライブラリだけで計算しました。

```text
b4-floor-aggregate__env-pegasus__protocol-silo__threads-48__workload-set-7095cfaaa30f9b4f5228__campaign-set-3553fb844072ea43111a.json
```

計算法は I:189、I:749、I:1189、I:1226 のとおりです。

```python
def canonical(value):
    return (
        json.dumps(
            value, sort_keys=True, separators=(",", ":"),
            ensure_ascii=False, allow_nan=False
        ) + "\n"
    ).encode("utf-8")

workloads = sorted(
    [
        {"ycsb_rmw": "0", "ycsb_rratio": ratio, "ycsb_zipf_skew": "0.9"}
        for ratio in ("95", "50", "5")
    ],
    key=canonical,
)
campaigns = sorted(
    f"t2288-f1-{wl}-c{i}"
    for wl in ("rr95", "rr50", "rr5")
    for i in (1, 2)
)
workload_id = "set-" + hashlib.sha256(canonical(workloads)).hexdigest()[:20]
campaign_id = "set-" + hashlib.sha256(canonical(campaigns)).hexdigest()[:20]
```

**末尾 newline を含めること、workload は canonical bytes 順、campaign は文字列順であること**が重要です。rr 数値の大小順を独自に使いません。集約名は予測値であり、成果物の存在・採用可能性・その内容 hash は今回確定しません。

## 5. 凍結 commit と親が実走する検査

順序は次のとおりです。作業場所は指定 worktree 内に限定します。

1. **local main 取り込み確認。** `git rev-parse HEAD main` と差分を確認する。現在は一致しています。main が進んでいれば、親の既存 wave 手順で取り込みを完了し、その後の HEAD を親 OID `P` と確定する。spec を生成してから別の準備 commit を挟まない。
2. **`place` 済みの確認。** 親 brief の配置済み証拠を使用する。main 取り込みで policy が変わった場合には既存 `place` 経路で確認する。ignored binary は別 checkout へ merge されない。V/D2069.md:18、:21。
3. **出力 directory を用意。** `output/env/pegasus/floor-pair/t2288-f1/` を非 symlink directory として作り、3 spec を同居させる。9 個の予定出力と集約 leaf が既存物と衝突しないことを確認する。F:517。
4. **3 spec を一括作成。** `source_commit=P`、最終 relpath から seed を計算し、§1 の直列化で bytes を確定する。P が現在値と違えば掲載 seed/hash は全件再計算する。
5. **spec 外で hash を計算。** 凍結前の実 bytes から各 hash を求め、decisions の対応表に記録する。spec 自身には spec hash や凍結 commit OID を入れない。
6. **3 spec と決定記録を同じ凍結 commit C に入れる。** `C^ == P` を確認する。凍結前には存在しない C をその本文へ書かない。これで F36 の自己参照を作らない。
7. **C 上で実 bytes・tracked blob を確認し、`--validate-only` を 3 本実行。** 再計算 hash と、凍結した decisions の期待値が一致してから期待値を CLI に渡す。
8. **実走結果を insight/worklog に記録して後続 commit。** 凍結 spec は変更しない。C の OID はこの後続記録に書ける。失敗した検査を成功扱いにせず、原因を記録する。
9. **最終文書検査・既存受入を実施。** 実装面差分 0 byte、§5 値セル不変を最終 diff で確認する。wave 側では fold 本実行をしない。

CLI は各 spec について次の形です。

```bash
python3 -m orchestrator.campaign.floor_pair_driver \
  --repo-root /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-a5-freeze \
  --spec '<§1の完全なspec relpath>' \
  --expected-sha256 '<凍結した期待hash>' \
  --validate-only
```

`--validate-only` は F:3123 の loader と plan 生成を呼び、F:1666 の live site 検査や `run_window` を呼びません。成功しても計算ノード admission や実測成功の証拠ではありません。T:3401 も出力ファイルを予約しない境界を確認しています。

親の検査列は以下です。

| 検査 | 期待結果・確認内容 |
|---|---|
| `--validate-only` rr95/rr50/rr5 | 各 rc=0、stderr 空、schema `floor-pair-plan/v2` |
| 各 stdout の集計 | `len(sessions)=248`、各 session に測定 2 件、合計 496、window ごと 124 session。candidate/reference 各 248 |
| `python3 tools/check_docs.py` | rc=0。記録の形式検査 |
| `python3 -m orchestrator.campaign.s8b_holdout_freeze search` | rc=0、spec・insight に conjunction hit なし |
| spec・insight の仮置き語走査 | `placeholder`、旧 precheck ID、2030 年の日時、ゼロ seed 等が混入していないこと。三軸 search とは別の確認 |
| `python3 tools/spool_fold.py --dry-run --show-diff` | rc=0、予定 D と T 更新を目視。canonical は変更しない |
| 親の既存受入手順 | 必須 checker・provenance 監査を既存経路で実行。新しい test・gate は追加しない |

plan に件数の専用 top-level field があると仮定せず、`sessions` と各 `measurements` から集計してください。F:1459。

main が後に進んでも、**spec bytes と計画生成実装が変わらず、loader が引き続き通るなら** plan bytes は不変です。HMAC 入力と plan payload は `spec_sha256` を含み、loaded HEAD は含みません。実装変更まで含めて不変とは主張しません。F:1356、F:1460、T:509。

三軸走査については特に次を訂正します。

- S:65 の正規表現は具体的な key/value 表記を探し、S:120 の規則で同一ファイル内の三軸 conjunction を判定します。**三軸 key の存在自体は禁止ではありません。**
- receipt path 中の `rr20--stock_common.json` は、それだけでは read-ratio の正規表現に一致しません。正しい receipt path を改名して回避する必要はありません。
- insight に別用途の具体的 workload JSON、取得 argv、過去の説明文を貼ると、別々の箇所から三軸 conjunction が成立し得ます。今回に不要な対象値の列挙を持ち込まないでください。
- `placeholder` という一般語をこの search が検査する、という brief の説明は誤りです。記録側では「事前点検」「仮置き」等で説明し、旧 JSON や brief を丸ごと転載しません。scanner の規則・除外を変えません。

## 6. 記録の骨子

decisions fragment は次の 1 件を提案します。

```text
docs/spool/decisions/2026-09-18-dev-wave-t2288-a5-freeze-1.md
```

frontmatter は `schema: izanagi-spool-v1`、`ledger: decisions`、`authored: 2026-09-18`、`wave: dev-wave-t2288-a5-freeze`、`seq: 1`。`title` は付けません。H2 は例えば次です。

```text
## {{D:b4-floor-a5-freeze}}. B-4 床値の A-5 と集約対象を測定前に固定する
```

本文に含める骨子:

- **決定:** D2120 項 4 の委任、3 spec、窓日時、6 campaign、ID・命名、seed 式、実行設定。
- **集約対応:** 3 組の完全な `(relpath, sha256)`、summary 3 path、output_dir、予測集約名。
- **理由:** 8 日窓は運用上の選択、開始時刻帯の分離、設定と既決値の区別。
- **主張しないこと:** 事前性の機械証明、独立性、終了から開始の分離保証、将来環境の同一性、実走成功、binary 可用性、床値生成・採用・§5 発効。
- **却下した選択肢:** summary から期待集合を導出、仮置き seed の継承、未知 schema key の追加、結果を見ての窓・対象・seed 選別、新 manifest。

形式根拠は `docs/spool/README.md:28`、`:35`、`:55`、`docs/spool/decisions/README.md:5`、`:30`。新 D の数字を先に振らず、題末尾の日付も付けません。

insight は以下です。

```text
output/insights/2026-09-18/t2288-a5-freeze/README.md
```

節構成案:

1. `authority: none`、`default_effect: no-state-change`、依頼と今回の到達点。
2. 採用した値と既裁定の対応。
3. 3 spec の path/hash、親 OID、凍結 commit。
4. 集約入力と出力名の対応・計算法。
5. 実走した validate-only の結果表、plan 件数・hash。
6. 窓と時間費用の説明、後続で人手確認する事項。
7. 主張しないこと。
8. 検査と後続 wave の残件。

D 番号は未採番のため、insight からは decisions fragment の path を参照します。spool 用の未解決 token を一般 insight へ持ち込まない方が明確です。

worklog fragment は次です。

```text
docs/spool/worklog/2026-09-18-dev-wave-t2288-a5-freeze-1.md
```

`title` を持たせ、H2 は `## 本文`、`## 次の一手差分` のちょうど 2 つにします。本文は段 3 の協議・採否、実走の成否、設計判断への参照、未実施事項を中心にします。T-2288 全体に測定等が残るため、**原則 `更新` とし、凍結だけで `完了` にしません。** 現在の item の範囲が凍結だけに限定されている場合に限り親が再判断します。

`base` は main を取り込んだ指定 worktree 内で既存 lookup から取得し、land 前の dry-run で再確認します。共有 checkout を読みに行く手順は提案しません。形式根拠は `docs/spool/worklog/README.md:5`、`:65`、`:79`。

## 総括

**(a) 採用すべき spec 値**

| 項目 | 採用値 |
|---|---|
| schema | `floor-pair-spec/v3`、3 本を一括凍結 |
| 配置 directory | `output/env/pegasus/floor-pair/t2288-f1/` |
| spec 命名 | §1 の完全名。campaign 成分を追加 |
| source_commit | 凍結 commit の親。現在案は `d2ebef7a407dc6be61622ed596cf08b8b518f606` |
| 第 1 窓 | `[2026-09-19T00:00:00Z, 2026-09-27T00:00:00Z)` |
| 第 2 窓 | `[2026-09-28T00:00:00Z, 2026-10-06T00:00:00Z)` |
| campaign | `t2288-f1-<wl>-c1` / `-c2` |
| window / pair / cell | `<wl>-w1,w2` / `pair-<wl>` / `<wl>-t48-s0.9-rmw0` |
| sample_count | 各窓 62、各 spec 1 pair |
| seed | §3 の公開 SHA-256 式。現在親での実値は §1 |
| timeout / probe timeout | 120 / 30 秒。今回の運用選択として記録 |
| numactl / extra_env / perf | `[]` / `{}` / `false` |
| 既決 perf・較正・binary | §1 の値を維持 |
| 出力 | §1 の窓 6 path・summary 3 path |
| 集約 | 明示した期待 spec 3 組、全 summary 3 件、同 directory、§4 の予測名 |

**(b) 親 brief を訂正した点**

- spec 名へ campaign 成分を追加。ただし元案を D1641 違反とは断定しない。
- 24 h の隙間は開始時刻帯の性質。D1974 の人手確認を完了扱いにしない。
- randomization は sample・side・session 内測定順の三箇所。「有利な選択は存在しない」を削除。
- 1.6 h、NUMA 1 node、120 秒の説明を、将来実測の保証へ一般化しない。
- 共通窓は別 node 並走を保証しない。
- 三軸 search と仮置き語の走査を区別する。
- plan 不変は spec bytes・計画生成実装・束縛成功を条件とする。
- 非保証説明を unknown JSON field として追加せず、decisions/insight に置く。

**(c) 段 3 の敵対相談へ回す論点**

1. **窓分離:** 開始時刻帯の 24 h 分離と実 campaign 分離を区別した記録で D1974 の人手責任を保てるか。終了→開始の確認方法を後続へ明確に渡せているか。
2. **日程:** job body 未着地の状態で、9 月 19 日開始・8 日幅の固定が妥当か。未実施のまま窓を失った場合の扱いが事後選択を許さないか。
3. **実行設定:** 120/30 秒と空 numactl argv の選択を、較正由来の確定値と誤表示していないか。
4. **seed と凍結順序:** 親 OID 確定、最終 path、seed、bytes、外部 hash、commit の順が循環せず、順序を見て再選別する余地を残していないか。
5. **集約:** 期待 spec 3 組を summary から独立して固定し、全 6 campaign・3 cell・2 窓の対応を保っているか。予測 filename の newline・sort 規則が issuer と一致するか。
6. **記録整合:** D2088 の非保証欄という表現を schema 変更なしで扱うこと、T-2288 を部分完了として更新することが適切か。