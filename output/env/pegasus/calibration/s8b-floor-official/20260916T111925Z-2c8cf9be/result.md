# 8b floor campaign result — pegasus / mode=official

> floor **案** (何も発効させていない)。freeze への floor 書込みは親が行う。
> 単一 campaign 内 session dispersion に基づく記述的下限 (別 run 間の変動は含まない)。
> eligible_for_refreeze (producer-reported): True

- formula: `s8b-floor-stats/v2`
- ccbench_pin: `511c9538e4e8efa54b45cda62e72389ed3b706ec`
- protocol_sha256: `2c8cf9be929d83653814ecf5f2d5ed134a2af89686d796b8144da2fd45dfa58a`
- freeze_sha256: `315b1eb83d6fbdc525448c3c96c66ab6013df72487f35d8fa519c27ba34bc688`
- manifest_sha256: `50af60db9c489a2b06a9baa2970cc29903b619102578991c25ff3714c1a5ae2a`
- perf: mode=disabled, reason=nonzero-rc, receipt_sha256=`c3d47f345075f0cfb93db01ee53f1097dc096707b1806384613df5141d9fb4d0`
- stock_configuration: `stock_common`
- wired_min_rel_floor: 0.03
- scale_adequacy_rel_tolerance: 0.10

## セル統計 (session-median の散らばり)

| cell | valid | n_valid | m (median) | s (stdev) | cv |
|---|:---:|---:|---:|---:|---:|
| `rr20::backoff_fixed_best` | True | 8 | 3.605e+06 | 1.056e+04 | 0.002929 |
| `rr20::ident_all` | True | 8 | 1.173e+06 | 1.079e+04 | 0.009177 |
| `rr20::p2_2_flag_opt` | True | 8 | 2.616e+06 | 2.534e+04 | 0.009705 |
| `rr20::sort_best` | True | 8 | 1.205e+06 | 7,388 | 0.006142 |
| `rr20::stock_common` | True | 8 | 1.194e+06 | 1.403e+04 | 0.01179 |
| `rr20::system_gate` | True | 8 | 1.258e+06 | 8,381 | 0.006664 |
| `rr80::backoff_fixed_best` | True | 8 | 6.849e+06 | 1.549e+04 | 0.002262 |
| `rr80::ident_all` | True | 8 | 1.522e+06 | 1.088e+04 | 0.007138 |
| `rr80::p2_2_flag_opt` | True | 8 | 7.312e+06 | 1.994e+04 | 0.002727 |
| `rr80::sort_best` | True | 8 | 1.522e+06 | 1.286e+04 | 0.008451 |
| `rr80::stock_common` | True | 8 | 1.536e+06 | 1.9e+04 | 0.01236 |
| `rr80::system_gate` | True | 8 | 3.143e+06 | 8,565 | 0.002726 |

## floor 案 (holdout 別, pair = configuration_id)

### rr20

- scalar_alt (全 pair の max): 3.582e+04
- scale_ref (m_stock): 1.194e+06
- machine_anomaly セル: (なし)

| pair (configuration_id) | floor_pair |
|---|---:|
| `backoff_fixed_best` | 3.582e+04 |
| `ident_all` | 3.582e+04 |
| `p2_2_flag_opt` | 3.582e+04 |
| `sort_best` | 3.582e+04 |
| `system_gate` | 3.582e+04 |

### rr80

- scalar_alt (全 pair の max): 4.607e+04
- scale_ref (m_stock): 1.536e+06
- machine_anomaly セル: (なし)

| pair (configuration_id) | floor_pair |
|---|---:|
| `backoff_fixed_best` | 4.607e+04 |
| `ident_all` | 4.607e+04 |
| `p2_2_flag_opt` | 4.607e+04 |
| `sort_best` | 4.607e+04 |
| `system_gate` | 4.607e+04 |

## 除外 session (理由別件数)

(なし)

## 全 attempt 台帳 (CV / median / valid)

| seq | cell | kind | round | valid | reason | cv | median | dur(s) |
|---:|---|---|---:|:---:|---|---:|---:|---:|
| 0 | `rr80::p2_2_flag_opt` | planned | 1 | True | None | 0.01176 | 7.327e+06 | 26.95 |
| 1 | `rr20::sort_best` | planned | 1 | True | None | 0.01987 | 1.204e+06 | 26.96 |
| 2 | `rr20::stock_common` | planned | 1 | True | None | 0.01617 | 1.185e+06 | 27.09 |
| 3 | `rr80::stock_common` | planned | 1 | True | None | 0.02229 | 1.538e+06 | 27.14 |
| 4 | `rr20::system_gate` | planned | 1 | True | None | 0.01012 | 1.252e+06 | 27.16 |
| 5 | `rr20::backoff_fixed_best` | planned | 1 | True | None | 0.005635 | 3.606e+06 | 27.22 |
| 6 | `rr80::backoff_fixed_best` | planned | 1 | True | None | 0.008172 | 6.846e+06 | 27.37 |
| 7 | `rr80::system_gate` | planned | 1 | True | None | 0.008083 | 3.143e+06 | 27.49 |
| 8 | `rr80::sort_best` | planned | 1 | True | None | 0.01821 | 1.514e+06 | 27.44 |
| 9 | `rr20::p2_2_flag_opt` | planned | 1 | True | None | 0.01113 | 2.634e+06 | 27.55 |
| 10 | `rr80::ident_all` | planned | 1 | True | None | 0.01562 | 1.528e+06 | 27.59 |
| 11 | `rr20::ident_all` | planned | 1 | True | None | 0.01984 | 1.176e+06 | 27.62 |
| 12 | `rr20::ident_all` | planned | 2 | True | None | 0.01105 | 1.185e+06 | 27.68 |
| 13 | `rr20::stock_common` | planned | 2 | True | None | 0.0201 | 1.207e+06 | 27.82 |
| 14 | `rr80::backoff_fixed_best` | planned | 2 | True | None | 0.007664 | 6.856e+06 | 27.92 |
| 15 | `rr80::p2_2_flag_opt` | planned | 2 | True | None | 0.01223 | 7.326e+06 | 27.96 |
| 16 | `rr80::ident_all` | planned | 2 | True | None | 0.01274 | 1.52e+06 | 27.95 |
| 17 | `rr20::system_gate` | planned | 2 | True | None | 0.01105 | 1.269e+06 | 28.08 |
| 18 | `rr20::p2_2_flag_opt` | planned | 2 | True | None | 0.01001 | 2.617e+06 | 28.14 |
| 19 | `rr80::system_gate` | planned | 2 | True | None | 0.004024 | 3.144e+06 | 28.25 |
| 20 | `rr20::backoff_fixed_best` | planned | 2 | True | None | 0.004332 | 3.609e+06 | 28.21 |
| 21 | `rr20::sort_best` | planned | 2 | True | None | 0.02 | 1.206e+06 | 28.32 |
| 22 | `rr80::sort_best` | planned | 2 | True | None | 0.02455 | 1.522e+06 | 28.5 |
| 23 | `rr80::stock_common` | planned | 2 | True | None | 0.02251 | 1.531e+06 | 28.64 |
| 24 | `rr80::ident_all` | planned | 3 | True | None | 0.02825 | 1.519e+06 | 28.48 |
| 25 | `rr80::system_gate` | planned | 3 | True | None | 0.001806 | 3.143e+06 | 28.52 |
| 26 | `rr20::backoff_fixed_best` | planned | 3 | True | None | 0.005456 | 3.601e+06 | 28.59 |
| 27 | `rr20::ident_all` | planned | 3 | True | None | 0.01239 | 1.186e+06 | 28.83 |
| 28 | `rr20::p2_2_flag_opt` | planned | 3 | True | None | 0.02667 | 2.556e+06 | 28.73 |
| 29 | `rr80::backoff_fixed_best` | planned | 3 | True | None | 0.004607 | 6.852e+06 | 28.81 |
| 30 | `rr80::p2_2_flag_opt` | planned | 3 | True | None | 0.00671 | 7.302e+06 | 28.88 |
| 31 | `rr20::system_gate` | planned | 3 | True | None | 0.01022 | 1.262e+06 | 28.92 |
| 32 | `rr80::stock_common` | planned | 3 | True | None | 0.01353 | 1.533e+06 | 28.98 |
| 33 | `rr20::sort_best` | planned | 3 | True | None | 0.01777 | 1.199e+06 | 29.03 |
| 34 | `rr80::sort_best` | planned | 3 | True | None | 0.01063 | 1.523e+06 | 29.12 |
| 35 | `rr20::stock_common` | planned | 3 | True | None | 0.01092 | 1.199e+06 | 29.27 |
| 36 | `rr20::sort_best` | planned | 4 | True | None | 0.01095 | 1.205e+06 | 29.24 |
| 37 | `rr80::stock_common` | planned | 4 | True | None | 0.01843 | 1.549e+06 | 29.3 |
| 38 | `rr80::backoff_fixed_best` | planned | 4 | True | None | 0.007431 | 6.87e+06 | 29.41 |
| 39 | `rr20::system_gate` | planned | 4 | True | None | 0.005876 | 1.255e+06 | 29.48 |
| 40 | `rr20::ident_all` | planned | 4 | True | None | 0.02228 | 1.171e+06 | 29.58 |
| 41 | `rr80::p2_2_flag_opt` | planned | 4 | True | None | 0.007968 | 7.32e+06 | 29.59 |
| 42 | `rr20::stock_common` | planned | 4 | True | None | 0.01474 | 1.178e+06 | 29.61 |
| 43 | `rr20::backoff_fixed_best` | planned | 4 | True | None | 0.004968 | 3.587e+06 | 29.66 |
| 44 | `rr80::sort_best` | planned | 4 | True | None | 0.01938 | 1.543e+06 | 29.67 |
| 45 | `rr80::system_gate` | planned | 4 | True | None | 0.006966 | 3.154e+06 | 29.81 |
| 46 | `rr80::ident_all` | planned | 4 | True | None | 0.01076 | 1.519e+06 | 29.83 |
| 47 | `rr20::p2_2_flag_opt` | planned | 4 | True | None | 0.03323 | 2.601e+06 | 29.92 |
| 48 | `rr20::p2_2_flag_opt` | planned | 5 | True | None | 0.02143 | 2.616e+06 | 30.11 |
| 49 | `rr20::sort_best` | planned | 5 | True | None | 0.01958 | 1.214e+06 | 30.5 |
| 50 | `rr20::system_gate` | planned | 5 | True | None | 0.01223 | 1.265e+06 | 30.3 |
| 51 | `rr20::backoff_fixed_best` | planned | 5 | True | None | 0.003856 | 3.604e+06 | 30.46 |
| 52 | `rr80::ident_all` | planned | 5 | True | None | 0.02008 | 1.508e+06 | 30.4 |
| 53 | `rr20::ident_all` | planned | 5 | True | None | 0.02609 | 1.164e+06 | 30.59 |
| 54 | `rr80::system_gate` | planned | 5 | True | None | 0.004849 | 3.14e+06 | 30.31 |
| 55 | `rr20::stock_common` | planned | 5 | True | None | 0.01619 | 1.189e+06 | 30.41 |
| 56 | `rr80::stock_common` | planned | 5 | True | None | 0.02662 | 1.559e+06 | 30.53 |
| 57 | `rr80::backoff_fixed_best` | planned | 5 | True | None | 0.008502 | 6.817e+06 | 30.6 |
| 58 | `rr80::sort_best` | planned | 5 | True | None | 0.02151 | 1.507e+06 | 30.75 |
| 59 | `rr80::p2_2_flag_opt` | planned | 5 | True | None | 0.01187 | 7.304e+06 | 30.68 |
| 60 | `rr20::stock_common` | planned | 6 | True | None | 0.01667 | 1.2e+06 | 30.79 |
| 61 | `rr80::ident_all` | planned | 6 | True | None | 0.03113 | 1.545e+06 | 30.88 |
| 62 | `rr20::p2_2_flag_opt` | planned | 6 | True | None | 0.01265 | 2.622e+06 | 30.98 |
| 63 | `rr20::ident_all` | planned | 6 | True | None | 0.01739 | 1.165e+06 | 31.1 |
| 64 | `rr20::backoff_fixed_best` | planned | 6 | True | None | 0.00443 | 3.623e+06 | 31.07 |
| 65 | `rr20::sort_best` | planned | 6 | True | None | 0.007107 | 1.207e+06 | 31.1 |
| 66 | `rr20::system_gate` | planned | 6 | True | None | 0.008621 | 1.264e+06 | 31.22 |
| 67 | `rr80::p2_2_flag_opt` | planned | 6 | True | None | 0.01298 | 7.285e+06 | 31.26 |
| 68 | `rr80::stock_common` | planned | 6 | True | None | 0.01225 | 1.562e+06 | 31.32 |
| 69 | `rr80::system_gate` | planned | 6 | True | None | 0.007348 | 3.124e+06 | 31.36 |
| 70 | `rr80::backoff_fixed_best` | planned | 6 | True | None | 0.006314 | 6.84e+06 | 31.53 |
| 71 | `rr80::sort_best` | planned | 6 | True | None | 0.007323 | 1.506e+06 | 31.53 |
| 72 | `rr20::system_gate` | planned | 7 | True | None | 0.008837 | 1.246e+06 | 31.59 |
| 73 | `rr80::stock_common` | planned | 7 | True | None | 0.02385 | 1.508e+06 | 31.88 |
| 74 | `rr80::system_gate` | planned | 7 | True | None | 0.005515 | 3.142e+06 | 31.89 |
| 75 | `rr20::ident_all` | planned | 7 | True | None | 0.01147 | 1.194e+06 | 32.08 |
| 76 | `rr20::backoff_fixed_best` | planned | 7 | True | None | 0.006276 | 3.605e+06 | 31.78 |
| 77 | `rr20::p2_2_flag_opt` | planned | 7 | True | None | 0.01976 | 2.636e+06 | 31.96 |
| 78 | `rr20::stock_common` | planned | 7 | True | None | 0.02188 | 1.2e+06 | 32.01 |
| 79 | `rr80::ident_all` | planned | 7 | True | None | 0.01983 | 1.528e+06 | 31.98 |
| 80 | `rr80::backoff_fixed_best` | planned | 7 | True | None | 0.01261 | 6.84e+06 | 32.09 |
| 81 | `rr20::sort_best` | planned | 7 | True | None | 0.0128 | 1.198e+06 | 32.15 |
| 82 | `rr80::p2_2_flag_opt` | planned | 7 | True | None | 0.01099 | 7.341e+06 | 32.22 |
| 83 | `rr80::sort_best` | planned | 7 | True | None | 0.009639 | 1.535e+06 | 32.32 |
| 84 | `rr80::sort_best` | planned | 8 | True | None | 0.01384 | 1.521e+06 | 32.3 |
| 85 | `rr20::system_gate` | planned | 8 | True | None | 0.01162 | 1.248e+06 | 32.52 |
| 86 | `rr80::backoff_fixed_best` | planned | 8 | True | None | 0.01484 | 6.855e+06 | 32.46 |
| 87 | `rr20::stock_common` | planned | 8 | True | None | 0.01212 | 1.165e+06 | 32.48 |
| 88 | `rr20::sort_best` | planned | 8 | True | None | 0.008304 | 1.19e+06 | 32.56 |
| 89 | `rr80::ident_all` | planned | 8 | True | None | 0.03352 | 1.523e+06 | 32.65 |
| 90 | `rr80::stock_common` | planned | 8 | True | None | 0.01201 | 1.517e+06 | 32.7 |
| 91 | `rr20::p2_2_flag_opt` | planned | 8 | True | None | 0.01936 | 2.607e+06 | 32.74 |
| 92 | `rr80::system_gate` | planned | 8 | True | None | 0.003652 | 3.145e+06 | 32.82 |
| 93 | `rr80::p2_2_flag_opt` | planned | 8 | True | None | 0.01392 | 7.289e+06 | 32.97 |
| 94 | `rr20::ident_all` | planned | 8 | True | None | 0.01632 | 1.169e+06 | 33.03 |
| 95 | `rr20::backoff_fixed_best` | planned | 8 | True | None | 0.002963 | 3.616e+06 | 33.09 |
