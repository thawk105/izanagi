# Q2 の再分類後集計 (job dir arm-B/summary-q2.json)

sha256 `1ef9af1773a828a26d5280e3a49cacd9c39397e0c91997fc49dda4180539872d`、17877 byte。

```json
{
  "schema_version": "t2774-summary/v1",
  "arms": {
    "p058-plain": {
      "N": 40,
      "m": 40,
      "k": 2,
      "failure": 0,
      "indeterminate": 38,
      "decisive_m": 2,
      "k_over_m": 0.05,
      "cp95": [
        0.006113646599350894,
        0.16919686395941713
      ],
      "k_over_decisive_m": 1.0,
      "decisive_cp95": [
        0.15811388300841894,
        1.0
      ],
      "all_submitted_rate_bounds": [
        0.05,
        1.0
      ],
      "discriminator_counts": {
        "supported": 0,
        "contradicted": 0,
        "indeterminate": 0,
        "no-g2": 0,
        "input-rejected": 0,
        "not-run": 40
      },
      "comparisons": [],
      "identification": {
        "g2_runs": 2,
        "identified_g2_runs": 0,
        "rate": 0.0
      }
    },
    "e9-plain-nowit": {
      "N": 40,
      "m": 40,
      "k": 3,
      "failure": 0,
      "indeterminate": 37,
      "decisive_m": 3,
      "k_over_m": 0.075,
      "cp95": [
        0.01574217985104165,
        0.20386474873289845
      ],
      "k_over_decisive_m": 1.0,
      "decisive_cp95": [
        0.2924017738212866,
        1.0
      ],
      "all_submitted_rate_bounds": [
        0.075,
        1.0
      ],
      "discriminator_counts": {
        "supported": 0,
        "contradicted": 0,
        "indeterminate": 0,
        "no-g2": 0,
        "input-rejected": 0,
        "not-run": 40
      },
      "comparisons": [],
      "identification": {
        "g2_runs": 3,
        "identified_g2_runs": 0,
        "rate": 0.0
      }
    },
    "e9-instr-nowit": {
      "N": 40,
      "m": 40,
      "k": 2,
      "failure": 0,
      "indeterminate": 0,
      "decisive_m": 40,
      "k_over_m": 0.05,
      "cp95": [
        0.006113646599350894,
        0.16919686395941713
      ],
      "k_over_decisive_m": 0.05,
      "decisive_cp95": [
        0.006113646599350894,
        0.16919686395941713
      ],
      "all_submitted_rate_bounds": [
        0.05,
        0.05
      ],
      "discriminator_counts": {
        "supported": 0,
        "contradicted": 0,
        "indeterminate": 0,
        "no-g2": 0,
        "input-rejected": 0,
        "not-run": 40
      },
      "comparisons": [],
      "identification": {
        "g2_runs": 2,
        "identified_g2_runs": 0,
        "rate": 0.0
      }
    },
    "e9-instr-wit": {
      "N": 40,
      "m": 40,
      "k": 0,
      "failure": 0,
      "indeterminate": 0,
      "decisive_m": 40,
      "k_over_m": 0.0,
      "cp95": [
        0.0,
        0.08809730287880241
      ],
      "k_over_decisive_m": 0.0,
      "decisive_cp95": [
        0.0,
        0.08809730287880241
      ],
      "all_submitted_rate_bounds": [
        0.0,
        0.0
      ],
      "discriminator_counts": {
        "supported": 0,
        "contradicted": 0,
        "indeterminate": 0,
        "no-g2": 0,
        "input-rejected": 0,
        "not-run": 40
      },
      "comparisons": [],
      "identification": {
        "g2_runs": 0,
        "identified_g2_runs": 0,
        "rate": null
      }
    },
    "e9-diag-wit": {
      "N": 40,
      "m": 40,
      "k": 0,
      "failure": 0,
      "indeterminate": 0,
      "decisive_m": 40,
      "k_over_m": 0.0,
      "cp95": [
        0.0,
        0.08809730287880241
      ],
      "k_over_decisive_m": 0.0,
      "decisive_cp95": [
        0.0,
        0.08809730287880241
      ],
      "all_submitted_rate_bounds": [
        0.0,
        0.0
      ],
      "discriminator_counts": {
        "supported": 0,
        "contradicted": 0,
        "indeterminate": 0,
        "no-g2": 0,
        "input-rejected": 0,
        "not-run": 40
      },
      "comparisons": [],
      "identification": {
        "g2_runs": 0,
        "identified_g2_runs": 0,
        "rate": null
      }
    }
  },
  "denominator": "m counts valid verifier verdicts, including indeterminate; decisive_m excludes zero-cycle indeterminate; neither failure nor indeterminate is no-g2",
  "interval_assumption": "independent Bernoulli trials; node dependence not modeled",
  "inputs": [
    {
      "path": "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2774-mocc-torn-read-probe/arm-B/Q1/result.json",
      "sha256": "3924064ae9be37b459266b54fb7de798972b73fb590609e27a7001110b3812d9",
      "reclassified": true,
      "status_changes": [
        {
          "block": "Q1",
          "ordinal": 1,
          "arm": "p058-plain",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q1",
          "ordinal": 2,
          "arm": "e9-plain-nowit",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q1",
          "ordinal": 6,
          "arm": "e9-plain-nowit",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q1",
          "ordinal": 14,
          "arm": "p058-plain",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q1",
          "ordinal": 15,
          "arm": "e9-plain-nowit",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q1",
          "ordinal": 18,
          "arm": "p058-plain",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q1",
          "ordinal": 19,
          "arm": "e9-plain-nowit",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q1",
          "ordinal": 22,
          "arm": "p058-plain",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q1",
          "ordinal": 23,
          "arm": "e9-plain-nowit",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q1",
          "ordinal": 26,
          "arm": "p058-plain",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q1",
          "ordinal": 27,
          "arm": "e9-plain-nowit",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q1",
          "ordinal": 31,
          "arm": "e9-plain-nowit",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q1",
          "ordinal": 35,
          "arm": "p058-plain",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q1",
          "ordinal": 39,
          "arm": "p058-plain",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q1",
          "ordinal": 40,
          "arm": "e9-plain-nowit",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q1",
          "ordinal": 43,
          "arm": "p058-plain",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q1",
          "ordinal": 44,
          "arm": "e9-plain-nowit",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q1",
          "ordinal": 47,
          "arm": "p058-plain",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q1",
          "ordinal": 48,
          "arm": "e9-plain-nowit",
          "before": "failure",
          "after": "indeterminate"
        }
      ]
    },
    {
      "path": "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2774-mocc-torn-read-probe/arm-B/Q2/result.json",
      "sha256": "e614077a493a2681d3690b3b843fa4ddf1c407b35d16c79b7cdea81de02f5004",
      "reclassified": true,
      "status_changes": [
        {
          "block": "Q2",
          "ordinal": 1,
          "arm": "p058-plain",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q2",
          "ordinal": 2,
          "arm": "e9-plain-nowit",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q2",
          "ordinal": 6,
          "arm": "e9-plain-nowit",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q2",
          "ordinal": 10,
          "arm": "p058-plain",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q2",
          "ordinal": 14,
          "arm": "p058-plain",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q2",
          "ordinal": 15,
          "arm": "e9-plain-nowit",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q2",
          "ordinal": 18,
          "arm": "p058-plain",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q2",
          "ordinal": 19,
          "arm": "e9-plain-nowit",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q2",
          "ordinal": 22,
          "arm": "p058-plain",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q2",
          "ordinal": 23,
          "arm": "e9-plain-nowit",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q2",
          "ordinal": 26,
          "arm": "p058-plain",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q2",
          "ordinal": 27,
          "arm": "e9-plain-nowit",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q2",
          "ordinal": 31,
          "arm": "e9-plain-nowit",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q2",
          "ordinal": 35,
          "arm": "p058-plain",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q2",
          "ordinal": 39,
          "arm": "p058-plain",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q2",
          "ordinal": 43,
          "arm": "p058-plain",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q2",
          "ordinal": 44,
          "arm": "e9-plain-nowit",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q2",
          "ordinal": 47,
          "arm": "p058-plain",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q2",
          "ordinal": 48,
          "arm": "e9-plain-nowit",
          "before": "failure",
          "after": "indeterminate"
        }
      ]
    },
    {
      "path": "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2774-mocc-torn-read-probe/arm-B/Q3/result.json",
      "sha256": "3d962055a6610e50c54aac83516830236e6740876434eda72aff650bac87101a",
      "reclassified": true,
      "status_changes": [
        {
          "block": "Q3",
          "ordinal": 1,
          "arm": "p058-plain",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q3",
          "ordinal": 2,
          "arm": "e9-plain-nowit",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q3",
          "ordinal": 6,
          "arm": "e9-plain-nowit",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q3",
          "ordinal": 10,
          "arm": "p058-plain",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q3",
          "ordinal": 14,
          "arm": "p058-plain",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q3",
          "ordinal": 15,
          "arm": "e9-plain-nowit",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q3",
          "ordinal": 18,
          "arm": "p058-plain",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q3",
          "ordinal": 19,
          "arm": "e9-plain-nowit",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q3",
          "ordinal": 22,
          "arm": "p058-plain",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q3",
          "ordinal": 23,
          "arm": "e9-plain-nowit",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q3",
          "ordinal": 26,
          "arm": "p058-plain",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q3",
          "ordinal": 27,
          "arm": "e9-plain-nowit",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q3",
          "ordinal": 31,
          "arm": "e9-plain-nowit",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q3",
          "ordinal": 35,
          "arm": "p058-plain",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q3",
          "ordinal": 39,
          "arm": "p058-plain",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q3",
          "ordinal": 40,
          "arm": "e9-plain-nowit",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q3",
          "ordinal": 43,
          "arm": "p058-plain",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q3",
          "ordinal": 44,
          "arm": "e9-plain-nowit",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q3",
          "ordinal": 47,
          "arm": "p058-plain",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q3",
          "ordinal": 48,
          "arm": "e9-plain-nowit",
          "before": "failure",
          "after": "indeterminate"
        }
      ]
    },
    {
      "path": "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2774-mocc-torn-read-probe/arm-B/Q4/result.json",
      "sha256": "69fa7f033117f090d2ec0214f077d8d13603dccd2044f4955993f41e466d9c3a",
      "reclassified": true,
      "status_changes": [
        {
          "block": "Q4",
          "ordinal": 1,
          "arm": "p058-plain",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q4",
          "ordinal": 2,
          "arm": "e9-plain-nowit",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q4",
          "ordinal": 6,
          "arm": "e9-plain-nowit",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q4",
          "ordinal": 10,
          "arm": "p058-plain",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q4",
          "ordinal": 14,
          "arm": "p058-plain",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q4",
          "ordinal": 15,
          "arm": "e9-plain-nowit",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q4",
          "ordinal": 18,
          "arm": "p058-plain",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q4",
          "ordinal": 19,
          "arm": "e9-plain-nowit",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q4",
          "ordinal": 22,
          "arm": "p058-plain",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q4",
          "ordinal": 23,
          "arm": "e9-plain-nowit",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q4",
          "ordinal": 26,
          "arm": "p058-plain",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q4",
          "ordinal": 27,
          "arm": "e9-plain-nowit",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q4",
          "ordinal": 31,
          "arm": "e9-plain-nowit",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q4",
          "ordinal": 35,
          "arm": "p058-plain",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q4",
          "ordinal": 39,
          "arm": "p058-plain",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q4",
          "ordinal": 47,
          "arm": "p058-plain",
          "before": "failure",
          "after": "indeterminate"
        },
        {
          "block": "Q4",
          "ordinal": 48,
          "arm": "e9-plain-nowit",
          "before": "failure",
          "after": "indeterminate"
        }
      ]
    }
  ]
}
```
