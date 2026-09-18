# Q1 の集計 (job dir arm-B/summary-q1.json)

sha256 `d1722280f515b6d23e41847a090b5b438a78a3c78b624eaff3cf6396e467ece1`、2592 byte。

```json
{
  "schema_version": "t2774-summary/v1",
  "arms": {
    "instr": {
      "N": 56,
      "m": 56,
      "k": 0,
      "failure": 0,
      "indeterminate": 0,
      "decisive_m": 56,
      "k_over_m": 0.0,
      "cp95": [
        0.0,
        0.0637500966623622
      ],
      "k_over_decisive_m": 0.0,
      "decisive_cp95": [
        0.0,
        0.0637500966623622
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
        "not-run": 56
      },
      "comparisons": [],
      "identification": {
        "g2_runs": 0,
        "identified_g2_runs": 0,
        "rate": null
      }
    },
    "diag": {
      "N": 56,
      "m": 56,
      "k": 0,
      "failure": 0,
      "indeterminate": 0,
      "decisive_m": 56,
      "k_over_m": 0.0,
      "cp95": [
        0.0,
        0.0637500966623622
      ],
      "k_over_decisive_m": 0.0,
      "decisive_cp95": [
        0.0,
        0.0637500966623622
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
        "not-run": 56
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
      "path": "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2774-mocc-torn-read-probe/arm-B/B1/result.json",
      "sha256": "b07640a2ccdfe119a524d1109cf1a91202265bfb1fe20076161fe849b328faad"
    },
    {
      "path": "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2774-mocc-torn-read-probe/arm-B/B2/result.json",
      "sha256": "68a4aaa6e004a2cef8de1d017dac133b201026382f00a7ae1e98df2de8292858"
    },
    {
      "path": "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2774-mocc-torn-read-probe/arm-B/B3/result.json",
      "sha256": "2b3e102f4235a0cf08e14a785294db7a7a3f6020705e8413906ba01411be29fd"
    },
    {
      "path": "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2774-mocc-torn-read-probe/arm-B/B4/result.json",
      "sha256": "57b3431ded5c7a5a1b45ce08d4ffb5c408d289082dfe6821cbcc98f51908bc2f"
    }
  ]
}
```
