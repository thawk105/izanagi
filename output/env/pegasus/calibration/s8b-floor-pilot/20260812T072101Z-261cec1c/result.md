# 8b floor campaign result — pegasus / mode=pilot

> floor **案** (何も発効させていない)。freeze への floor 書込みは親が行う。
> 単一 campaign 内 session dispersion に基づく記述的下限 (別 run 間の変動は含まない)。
> eligible_for_refreeze: False

- formula: `s8b-floor-stats/v2`
- ccbench_pin: `d706650cdb31e442bef45b9b4216951d4fb40969`
- protocol_sha256: `261cec1c7f423b3eebff41ee716d2bfe2c6fa9a10a9dd86d91eaf71612e74aac`
- freeze_sha256: `315b1eb83d6fbdc525448c3c96c66ab6013df72487f35d8fa519c27ba34bc688`
- manifest_sha256: `b5337437e5ed52f09ff0eb592f7e21576f8802fab3d93c2be2729cf42bac54c2`
- stock_configuration: `stock_common`
- wired_min_rel_floor: 0.03
- scale_adequacy_rel_tolerance: 0.10

## セル統計 (session-median の散らばり)

| cell | valid | n_valid | m (median) | s (stdev) | cv |
|---|:---:|---:|---:|---:|---:|
| `rr20::backoff_fixed_best` | False | 0 | n/a | n/a | n/a |
| `rr20::ident_all` | False | 0 | n/a | n/a | n/a |
| `rr20::p2_2_flag_opt` | False | 0 | n/a | n/a | n/a |
| `rr20::sort_best` | False | 0 | n/a | n/a | n/a |
| `rr20::stock_common` | False | 0 | n/a | n/a | n/a |
| `rr20::system_gate` | False | 0 | n/a | n/a | n/a |
| `rr80::backoff_fixed_best` | False | 0 | n/a | n/a | n/a |
| `rr80::ident_all` | False | 0 | n/a | n/a | n/a |
| `rr80::p2_2_flag_opt` | False | 0 | n/a | n/a | n/a |
| `rr80::sort_best` | False | 0 | n/a | n/a | n/a |
| `rr80::stock_common` | False | 0 | n/a | n/a | n/a |
| `rr80::system_gate` | False | 0 | n/a | n/a | n/a |

## floor 案 (holdout 別, pair = configuration_id)

### rr20

- scalar_alt (全 pair の max): n/a
- scale_ref (m_stock): n/a
- machine_anomaly セル: (なし)

| pair (configuration_id) | floor_pair |
|---|---:|
| `backoff_fixed_best` | n/a |
| `ident_all` | n/a |
| `p2_2_flag_opt` | n/a |
| `sort_best` | n/a |
| `system_gate` | n/a |

### rr80

- scalar_alt (全 pair の max): n/a
- scale_ref (m_stock): n/a
- machine_anomaly セル: (なし)

| pair (configuration_id) | floor_pair |
|---|---:|
| `backoff_fixed_best` | n/a |
| `ident_all` | n/a |
| `p2_2_flag_opt` | n/a |
| `sort_best` | n/a |
| `system_gate` | n/a |

## 除外 session (理由別件数)

| reason | count |
|---|---:|
| launch_failure | 120 |

## 全 attempt 台帳 (CV / median / valid)

| seq | cell | kind | round | valid | reason | cv | median | dur(s) |
|---:|---|---|---:|:---:|---|---:|---:|---:|
| 0 | `rr80::p2_2_flag_opt` | planned | 1 | False | launch_failure | n/a | n/a | 0.1744 |
| 1 | `rr20::sort_best` | planned | 1 | False | launch_failure | n/a | n/a | 0.1692 |
| 2 | `rr20::stock_common` | planned | 1 | False | launch_failure | n/a | n/a | 0.1675 |
| 3 | `rr80::stock_common` | planned | 1 | False | launch_failure | n/a | n/a | 0.1673 |
| 4 | `rr20::system_gate` | planned | 1 | False | launch_failure | n/a | n/a | 0.1684 |
| 5 | `rr20::backoff_fixed_best` | planned | 1 | False | launch_failure | n/a | n/a | 0.1665 |
| 6 | `rr80::backoff_fixed_best` | planned | 1 | False | launch_failure | n/a | n/a | 0.1671 |
| 7 | `rr80::system_gate` | planned | 1 | False | launch_failure | n/a | n/a | 0.1661 |
| 8 | `rr80::sort_best` | planned | 1 | False | launch_failure | n/a | n/a | 0.1664 |
| 9 | `rr20::p2_2_flag_opt` | planned | 1 | False | launch_failure | n/a | n/a | 0.1658 |
| 10 | `rr80::ident_all` | planned | 1 | False | launch_failure | n/a | n/a | 0.1664 |
| 11 | `rr20::ident_all` | planned | 1 | False | launch_failure | n/a | n/a | 0.1669 |
| 12 | `rr20::ident_all` | planned | 2 | False | launch_failure | n/a | n/a | 0.1665 |
| 13 | `rr20::stock_common` | planned | 2 | False | launch_failure | n/a | n/a | 0.1657 |
| 14 | `rr80::backoff_fixed_best` | planned | 2 | False | launch_failure | n/a | n/a | 0.1656 |
| 15 | `rr80::p2_2_flag_opt` | planned | 2 | False | launch_failure | n/a | n/a | 0.166 |
| 16 | `rr80::ident_all` | planned | 2 | False | launch_failure | n/a | n/a | 0.1654 |
| 17 | `rr20::system_gate` | planned | 2 | False | launch_failure | n/a | n/a | 0.1655 |
| 18 | `rr20::p2_2_flag_opt` | planned | 2 | False | launch_failure | n/a | n/a | 0.1659 |
| 19 | `rr80::system_gate` | planned | 2 | False | launch_failure | n/a | n/a | 0.1655 |
| 20 | `rr20::backoff_fixed_best` | planned | 2 | False | launch_failure | n/a | n/a | 0.1652 |
| 21 | `rr20::sort_best` | planned | 2 | False | launch_failure | n/a | n/a | 0.1661 |
| 22 | `rr80::sort_best` | planned | 2 | False | launch_failure | n/a | n/a | 0.1666 |
| 23 | `rr80::stock_common` | planned | 2 | False | launch_failure | n/a | n/a | 0.1666 |
| 24 | `rr80::ident_all` | planned | 3 | False | launch_failure | n/a | n/a | 0.1661 |
| 25 | `rr80::system_gate` | planned | 3 | False | launch_failure | n/a | n/a | 0.1658 |
| 26 | `rr20::backoff_fixed_best` | planned | 3 | False | launch_failure | n/a | n/a | 0.1655 |
| 27 | `rr20::ident_all` | planned | 3 | False | launch_failure | n/a | n/a | 0.1653 |
| 28 | `rr20::p2_2_flag_opt` | planned | 3 | False | launch_failure | n/a | n/a | 0.1662 |
| 29 | `rr80::backoff_fixed_best` | planned | 3 | False | launch_failure | n/a | n/a | 0.1655 |
| 30 | `rr80::p2_2_flag_opt` | planned | 3 | False | launch_failure | n/a | n/a | 0.165 |
| 31 | `rr20::system_gate` | planned | 3 | False | launch_failure | n/a | n/a | 0.1657 |
| 32 | `rr80::stock_common` | planned | 3 | False | launch_failure | n/a | n/a | 0.1654 |
| 33 | `rr20::sort_best` | planned | 3 | False | launch_failure | n/a | n/a | 0.1649 |
| 34 | `rr80::sort_best` | planned | 3 | False | launch_failure | n/a | n/a | 0.1662 |
| 35 | `rr20::stock_common` | planned | 3 | False | launch_failure | n/a | n/a | 0.1659 |
| 36 | `rr20::sort_best` | planned | 4 | False | launch_failure | n/a | n/a | 0.1653 |
| 37 | `rr80::stock_common` | planned | 4 | False | launch_failure | n/a | n/a | 0.1662 |
| 38 | `rr80::backoff_fixed_best` | planned | 4 | False | launch_failure | n/a | n/a | 0.165 |
| 39 | `rr20::system_gate` | planned | 4 | False | launch_failure | n/a | n/a | 0.1657 |
| 40 | `rr20::ident_all` | planned | 4 | False | launch_failure | n/a | n/a | 0.1678 |
| 41 | `rr80::p2_2_flag_opt` | planned | 4 | False | launch_failure | n/a | n/a | 0.1673 |
| 42 | `rr20::stock_common` | planned | 4 | False | launch_failure | n/a | n/a | 0.1662 |
| 43 | `rr20::backoff_fixed_best` | planned | 4 | False | launch_failure | n/a | n/a | 0.1669 |
| 44 | `rr80::sort_best` | planned | 4 | False | launch_failure | n/a | n/a | 0.1663 |
| 45 | `rr80::system_gate` | planned | 4 | False | launch_failure | n/a | n/a | 0.166 |
| 46 | `rr80::ident_all` | planned | 4 | False | launch_failure | n/a | n/a | 0.1655 |
| 47 | `rr20::p2_2_flag_opt` | planned | 4 | False | launch_failure | n/a | n/a | 0.1663 |
| 48 | `rr20::p2_2_flag_opt` | planned | 5 | False | launch_failure | n/a | n/a | 0.166 |
| 49 | `rr20::sort_best` | planned | 5 | False | launch_failure | n/a | n/a | 0.1657 |
| 50 | `rr20::system_gate` | planned | 5 | False | launch_failure | n/a | n/a | 0.1655 |
| 51 | `rr20::backoff_fixed_best` | planned | 5 | False | launch_failure | n/a | n/a | 0.165 |
| 52 | `rr80::ident_all` | planned | 5 | False | launch_failure | n/a | n/a | 0.1658 |
| 53 | `rr20::ident_all` | planned | 5 | False | launch_failure | n/a | n/a | 0.1655 |
| 54 | `rr80::system_gate` | planned | 5 | False | launch_failure | n/a | n/a | 0.1673 |
| 55 | `rr20::stock_common` | planned | 5 | False | launch_failure | n/a | n/a | 0.1659 |
| 56 | `rr80::stock_common` | planned | 5 | False | launch_failure | n/a | n/a | 0.1685 |
| 57 | `rr80::backoff_fixed_best` | planned | 5 | False | launch_failure | n/a | n/a | 0.1672 |
| 58 | `rr80::sort_best` | planned | 5 | False | launch_failure | n/a | n/a | 0.1666 |
| 59 | `rr80::p2_2_flag_opt` | planned | 5 | False | launch_failure | n/a | n/a | 0.1672 |
| 60 | `rr20::stock_common` | planned | 6 | False | launch_failure | n/a | n/a | 0.168 |
| 61 | `rr80::ident_all` | planned | 6 | False | launch_failure | n/a | n/a | 0.1658 |
| 62 | `rr20::p2_2_flag_opt` | planned | 6 | False | launch_failure | n/a | n/a | 0.1658 |
| 63 | `rr20::ident_all` | planned | 6 | False | launch_failure | n/a | n/a | 0.166 |
| 64 | `rr20::backoff_fixed_best` | planned | 6 | False | launch_failure | n/a | n/a | 0.1658 |
| 65 | `rr20::sort_best` | planned | 6 | False | launch_failure | n/a | n/a | 0.1655 |
| 66 | `rr20::system_gate` | planned | 6 | False | launch_failure | n/a | n/a | 0.1665 |
| 67 | `rr80::p2_2_flag_opt` | planned | 6 | False | launch_failure | n/a | n/a | 0.1658 |
| 68 | `rr80::stock_common` | planned | 6 | False | launch_failure | n/a | n/a | 0.1652 |
| 69 | `rr80::system_gate` | planned | 6 | False | launch_failure | n/a | n/a | 0.1654 |
| 70 | `rr80::backoff_fixed_best` | planned | 6 | False | launch_failure | n/a | n/a | 0.1659 |
| 71 | `rr80::sort_best` | planned | 6 | False | launch_failure | n/a | n/a | 0.1665 |
| 72 | `rr20::system_gate` | planned | 7 | False | launch_failure | n/a | n/a | 0.1658 |
| 73 | `rr80::stock_common` | planned | 7 | False | launch_failure | n/a | n/a | 0.1671 |
| 74 | `rr80::system_gate` | planned | 7 | False | launch_failure | n/a | n/a | 0.1653 |
| 75 | `rr20::ident_all` | planned | 7 | False | launch_failure | n/a | n/a | 0.1653 |
| 76 | `rr20::backoff_fixed_best` | planned | 7 | False | launch_failure | n/a | n/a | 0.1656 |
| 77 | `rr20::p2_2_flag_opt` | planned | 7 | False | launch_failure | n/a | n/a | 0.1651 |
| 78 | `rr20::stock_common` | planned | 7 | False | launch_failure | n/a | n/a | 0.1654 |
| 79 | `rr80::ident_all` | planned | 7 | False | launch_failure | n/a | n/a | 0.1658 |
| 80 | `rr80::backoff_fixed_best` | planned | 7 | False | launch_failure | n/a | n/a | 0.1655 |
| 81 | `rr20::sort_best` | planned | 7 | False | launch_failure | n/a | n/a | 0.1655 |
| 82 | `rr80::p2_2_flag_opt` | planned | 7 | False | launch_failure | n/a | n/a | 0.1661 |
| 83 | `rr80::sort_best` | planned | 7 | False | launch_failure | n/a | n/a | 0.1666 |
| 84 | `rr80::sort_best` | planned | 8 | False | launch_failure | n/a | n/a | 0.1657 |
| 85 | `rr20::system_gate` | planned | 8 | False | launch_failure | n/a | n/a | 0.166 |
| 86 | `rr80::backoff_fixed_best` | planned | 8 | False | launch_failure | n/a | n/a | 0.1655 |
| 87 | `rr20::stock_common` | planned | 8 | False | launch_failure | n/a | n/a | 0.1658 |
| 88 | `rr20::sort_best` | planned | 8 | False | launch_failure | n/a | n/a | 0.1665 |
| 89 | `rr80::ident_all` | planned | 8 | False | launch_failure | n/a | n/a | 0.1657 |
| 90 | `rr80::stock_common` | planned | 8 | False | launch_failure | n/a | n/a | 0.1652 |
| 91 | `rr20::p2_2_flag_opt` | planned | 8 | False | launch_failure | n/a | n/a | 0.1654 |
| 92 | `rr80::system_gate` | planned | 8 | False | launch_failure | n/a | n/a | 0.1653 |
| 93 | `rr80::p2_2_flag_opt` | planned | 8 | False | launch_failure | n/a | n/a | 0.1654 |
| 94 | `rr20::ident_all` | planned | 8 | False | launch_failure | n/a | n/a | 0.1658 |
| 95 | `rr20::backoff_fixed_best` | planned | 8 | False | launch_failure | n/a | n/a | 0.1663 |
| 96 | `rr80::p2_2_flag_opt` | retry | 1 | False | launch_failure | n/a | n/a | 0.1665 |
| 97 | `rr80::p2_2_flag_opt` | retry | 1 | False | launch_failure | n/a | n/a | 0.1668 |
| 98 | `rr20::sort_best` | retry | 1 | False | launch_failure | n/a | n/a | 0.1668 |
| 99 | `rr20::sort_best` | retry | 1 | False | launch_failure | n/a | n/a | 0.1668 |
| 100 | `rr20::stock_common` | retry | 1 | False | launch_failure | n/a | n/a | 0.1677 |
| 101 | `rr20::stock_common` | retry | 1 | False | launch_failure | n/a | n/a | 0.1676 |
| 102 | `rr80::stock_common` | retry | 1 | False | launch_failure | n/a | n/a | 0.1658 |
| 103 | `rr80::stock_common` | retry | 1 | False | launch_failure | n/a | n/a | 0.166 |
| 104 | `rr20::system_gate` | retry | 1 | False | launch_failure | n/a | n/a | 0.1661 |
| 105 | `rr20::system_gate` | retry | 1 | False | launch_failure | n/a | n/a | 0.1662 |
| 106 | `rr20::backoff_fixed_best` | retry | 1 | False | launch_failure | n/a | n/a | 0.1656 |
| 107 | `rr20::backoff_fixed_best` | retry | 1 | False | launch_failure | n/a | n/a | 0.1664 |
| 108 | `rr80::backoff_fixed_best` | retry | 1 | False | launch_failure | n/a | n/a | 0.1668 |
| 109 | `rr80::backoff_fixed_best` | retry | 1 | False | launch_failure | n/a | n/a | 0.1658 |
| 110 | `rr80::system_gate` | retry | 1 | False | launch_failure | n/a | n/a | 0.166 |
| 111 | `rr80::system_gate` | retry | 1 | False | launch_failure | n/a | n/a | 0.166 |
| 112 | `rr80::sort_best` | retry | 1 | False | launch_failure | n/a | n/a | 0.1663 |
| 113 | `rr80::sort_best` | retry | 1 | False | launch_failure | n/a | n/a | 0.1664 |
| 114 | `rr20::p2_2_flag_opt` | retry | 1 | False | launch_failure | n/a | n/a | 0.1661 |
| 115 | `rr20::p2_2_flag_opt` | retry | 1 | False | launch_failure | n/a | n/a | 0.166 |
| 116 | `rr80::ident_all` | retry | 1 | False | launch_failure | n/a | n/a | 0.1655 |
| 117 | `rr80::ident_all` | retry | 1 | False | launch_failure | n/a | n/a | 0.1659 |
| 118 | `rr20::ident_all` | retry | 1 | False | launch_failure | n/a | n/a | 0.1655 |
| 119 | `rr20::ident_all` | retry | 1 | False | launch_failure | n/a | n/a | 0.1658 |
