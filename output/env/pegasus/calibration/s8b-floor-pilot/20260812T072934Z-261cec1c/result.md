# 8b floor campaign result — pegasus / mode=pilot

> floor **案** (何も発効させていない)。freeze への floor 書込みは親が行う。
> 単一 campaign 内 session dispersion に基づく記述的下限 (別 run 間の変動は含まない)。
> eligible_for_refreeze: False

- formula: `s8b-floor-stats/v2`
- ccbench_pin: `d706650cdb31e442bef45b9b4216951d4fb40969`
- protocol_sha256: `261cec1c7f423b3eebff41ee716d2bfe2c6fa9a10a9dd86d91eaf71612e74aac`
- freeze_sha256: `315b1eb83d6fbdc525448c3c96c66ab6013df72487f35d8fa519c27ba34bc688`
- manifest_sha256: `80945db9ba5632ffefa8842fe9aea6494bfca60d678dccde5392845902af2254`
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
| 0 | `rr80::p2_2_flag_opt` | planned | 1 | False | launch_failure | n/a | n/a | 0.1721 |
| 1 | `rr20::sort_best` | planned | 1 | False | launch_failure | n/a | n/a | 0.1675 |
| 2 | `rr20::stock_common` | planned | 1 | False | launch_failure | n/a | n/a | 0.1668 |
| 3 | `rr80::stock_common` | planned | 1 | False | launch_failure | n/a | n/a | 0.1667 |
| 4 | `rr20::system_gate` | planned | 1 | False | launch_failure | n/a | n/a | 0.1663 |
| 5 | `rr20::backoff_fixed_best` | planned | 1 | False | launch_failure | n/a | n/a | 0.1653 |
| 6 | `rr80::backoff_fixed_best` | planned | 1 | False | launch_failure | n/a | n/a | 0.1646 |
| 7 | `rr80::system_gate` | planned | 1 | False | launch_failure | n/a | n/a | 0.1649 |
| 8 | `rr80::sort_best` | planned | 1 | False | launch_failure | n/a | n/a | 0.1647 |
| 9 | `rr20::p2_2_flag_opt` | planned | 1 | False | launch_failure | n/a | n/a | 0.1662 |
| 10 | `rr80::ident_all` | planned | 1 | False | launch_failure | n/a | n/a | 0.1658 |
| 11 | `rr20::ident_all` | planned | 1 | False | launch_failure | n/a | n/a | 0.1644 |
| 12 | `rr20::ident_all` | planned | 2 | False | launch_failure | n/a | n/a | 0.1659 |
| 13 | `rr20::stock_common` | planned | 2 | False | launch_failure | n/a | n/a | 0.1649 |
| 14 | `rr80::backoff_fixed_best` | planned | 2 | False | launch_failure | n/a | n/a | 0.1645 |
| 15 | `rr80::p2_2_flag_opt` | planned | 2 | False | launch_failure | n/a | n/a | 0.1648 |
| 16 | `rr80::ident_all` | planned | 2 | False | launch_failure | n/a | n/a | 0.1647 |
| 17 | `rr20::system_gate` | planned | 2 | False | launch_failure | n/a | n/a | 0.1649 |
| 18 | `rr20::p2_2_flag_opt` | planned | 2 | False | launch_failure | n/a | n/a | 0.1656 |
| 19 | `rr80::system_gate` | planned | 2 | False | launch_failure | n/a | n/a | 0.1641 |
| 20 | `rr20::backoff_fixed_best` | planned | 2 | False | launch_failure | n/a | n/a | 0.1654 |
| 21 | `rr20::sort_best` | planned | 2 | False | launch_failure | n/a | n/a | 0.1661 |
| 22 | `rr80::sort_best` | planned | 2 | False | launch_failure | n/a | n/a | 0.1655 |
| 23 | `rr80::stock_common` | planned | 2 | False | launch_failure | n/a | n/a | 0.166 |
| 24 | `rr80::ident_all` | planned | 3 | False | launch_failure | n/a | n/a | 0.1642 |
| 25 | `rr80::system_gate` | planned | 3 | False | launch_failure | n/a | n/a | 0.1646 |
| 26 | `rr20::backoff_fixed_best` | planned | 3 | False | launch_failure | n/a | n/a | 0.1666 |
| 27 | `rr20::ident_all` | planned | 3 | False | launch_failure | n/a | n/a | 0.1659 |
| 28 | `rr20::p2_2_flag_opt` | planned | 3 | False | launch_failure | n/a | n/a | 0.1652 |
| 29 | `rr80::backoff_fixed_best` | planned | 3 | False | launch_failure | n/a | n/a | 0.1642 |
| 30 | `rr80::p2_2_flag_opt` | planned | 3 | False | launch_failure | n/a | n/a | 0.1644 |
| 31 | `rr20::system_gate` | planned | 3 | False | launch_failure | n/a | n/a | 0.1645 |
| 32 | `rr80::stock_common` | planned | 3 | False | launch_failure | n/a | n/a | 0.1646 |
| 33 | `rr20::sort_best` | planned | 3 | False | launch_failure | n/a | n/a | 0.1645 |
| 34 | `rr80::sort_best` | planned | 3 | False | launch_failure | n/a | n/a | 0.1645 |
| 35 | `rr20::stock_common` | planned | 3 | False | launch_failure | n/a | n/a | 0.1647 |
| 36 | `rr20::sort_best` | planned | 4 | False | launch_failure | n/a | n/a | 0.165 |
| 37 | `rr80::stock_common` | planned | 4 | False | launch_failure | n/a | n/a | 0.1647 |
| 38 | `rr80::backoff_fixed_best` | planned | 4 | False | launch_failure | n/a | n/a | 0.1649 |
| 39 | `rr20::system_gate` | planned | 4 | False | launch_failure | n/a | n/a | 0.1644 |
| 40 | `rr20::ident_all` | planned | 4 | False | launch_failure | n/a | n/a | 0.1648 |
| 41 | `rr80::p2_2_flag_opt` | planned | 4 | False | launch_failure | n/a | n/a | 0.1666 |
| 42 | `rr20::stock_common` | planned | 4 | False | launch_failure | n/a | n/a | 0.1649 |
| 43 | `rr20::backoff_fixed_best` | planned | 4 | False | launch_failure | n/a | n/a | 0.1649 |
| 44 | `rr80::sort_best` | planned | 4 | False | launch_failure | n/a | n/a | 0.1649 |
| 45 | `rr80::system_gate` | planned | 4 | False | launch_failure | n/a | n/a | 0.1646 |
| 46 | `rr80::ident_all` | planned | 4 | False | launch_failure | n/a | n/a | 0.1649 |
| 47 | `rr20::p2_2_flag_opt` | planned | 4 | False | launch_failure | n/a | n/a | 0.165 |
| 48 | `rr20::p2_2_flag_opt` | planned | 5 | False | launch_failure | n/a | n/a | 0.1648 |
| 49 | `rr20::sort_best` | planned | 5 | False | launch_failure | n/a | n/a | 0.1648 |
| 50 | `rr20::system_gate` | planned | 5 | False | launch_failure | n/a | n/a | 0.1651 |
| 51 | `rr20::backoff_fixed_best` | planned | 5 | False | launch_failure | n/a | n/a | 0.1643 |
| 52 | `rr80::ident_all` | planned | 5 | False | launch_failure | n/a | n/a | 0.1645 |
| 53 | `rr20::ident_all` | planned | 5 | False | launch_failure | n/a | n/a | 0.1645 |
| 54 | `rr80::system_gate` | planned | 5 | False | launch_failure | n/a | n/a | 0.1644 |
| 55 | `rr20::stock_common` | planned | 5 | False | launch_failure | n/a | n/a | 0.1641 |
| 56 | `rr80::stock_common` | planned | 5 | False | launch_failure | n/a | n/a | 0.1648 |
| 57 | `rr80::backoff_fixed_best` | planned | 5 | False | launch_failure | n/a | n/a | 0.1643 |
| 58 | `rr80::sort_best` | planned | 5 | False | launch_failure | n/a | n/a | 0.1647 |
| 59 | `rr80::p2_2_flag_opt` | planned | 5 | False | launch_failure | n/a | n/a | 0.1648 |
| 60 | `rr20::stock_common` | planned | 6 | False | launch_failure | n/a | n/a | 0.1647 |
| 61 | `rr80::ident_all` | planned | 6 | False | launch_failure | n/a | n/a | 0.1644 |
| 62 | `rr20::p2_2_flag_opt` | planned | 6 | False | launch_failure | n/a | n/a | 0.1648 |
| 63 | `rr20::ident_all` | planned | 6 | False | launch_failure | n/a | n/a | 0.1646 |
| 64 | `rr20::backoff_fixed_best` | planned | 6 | False | launch_failure | n/a | n/a | 0.1643 |
| 65 | `rr20::sort_best` | planned | 6 | False | launch_failure | n/a | n/a | 0.1643 |
| 66 | `rr20::system_gate` | planned | 6 | False | launch_failure | n/a | n/a | 0.1647 |
| 67 | `rr80::p2_2_flag_opt` | planned | 6 | False | launch_failure | n/a | n/a | 0.1643 |
| 68 | `rr80::stock_common` | planned | 6 | False | launch_failure | n/a | n/a | 0.1643 |
| 69 | `rr80::system_gate` | planned | 6 | False | launch_failure | n/a | n/a | 0.1647 |
| 70 | `rr80::backoff_fixed_best` | planned | 6 | False | launch_failure | n/a | n/a | 0.1648 |
| 71 | `rr80::sort_best` | planned | 6 | False | launch_failure | n/a | n/a | 0.1652 |
| 72 | `rr20::system_gate` | planned | 7 | False | launch_failure | n/a | n/a | 0.1652 |
| 73 | `rr80::stock_common` | planned | 7 | False | launch_failure | n/a | n/a | 0.1648 |
| 74 | `rr80::system_gate` | planned | 7 | False | launch_failure | n/a | n/a | 0.1645 |
| 75 | `rr20::ident_all` | planned | 7 | False | launch_failure | n/a | n/a | 0.1641 |
| 76 | `rr20::backoff_fixed_best` | planned | 7 | False | launch_failure | n/a | n/a | 0.1664 |
| 77 | `rr20::p2_2_flag_opt` | planned | 7 | False | launch_failure | n/a | n/a | 0.165 |
| 78 | `rr20::stock_common` | planned | 7 | False | launch_failure | n/a | n/a | 0.1643 |
| 79 | `rr80::ident_all` | planned | 7 | False | launch_failure | n/a | n/a | 0.1643 |
| 80 | `rr80::backoff_fixed_best` | planned | 7 | False | launch_failure | n/a | n/a | 0.1665 |
| 81 | `rr20::sort_best` | planned | 7 | False | launch_failure | n/a | n/a | 0.1655 |
| 82 | `rr80::p2_2_flag_opt` | planned | 7 | False | launch_failure | n/a | n/a | 0.1652 |
| 83 | `rr80::sort_best` | planned | 7 | False | launch_failure | n/a | n/a | 0.1647 |
| 84 | `rr80::sort_best` | planned | 8 | False | launch_failure | n/a | n/a | 0.1641 |
| 85 | `rr20::system_gate` | planned | 8 | False | launch_failure | n/a | n/a | 0.1648 |
| 86 | `rr80::backoff_fixed_best` | planned | 8 | False | launch_failure | n/a | n/a | 0.1637 |
| 87 | `rr20::stock_common` | planned | 8 | False | launch_failure | n/a | n/a | 0.1644 |
| 88 | `rr20::sort_best` | planned | 8 | False | launch_failure | n/a | n/a | 0.1649 |
| 89 | `rr80::ident_all` | planned | 8 | False | launch_failure | n/a | n/a | 0.1641 |
| 90 | `rr80::stock_common` | planned | 8 | False | launch_failure | n/a | n/a | 0.1639 |
| 91 | `rr20::p2_2_flag_opt` | planned | 8 | False | launch_failure | n/a | n/a | 0.1643 |
| 92 | `rr80::system_gate` | planned | 8 | False | launch_failure | n/a | n/a | 0.1646 |
| 93 | `rr80::p2_2_flag_opt` | planned | 8 | False | launch_failure | n/a | n/a | 0.1644 |
| 94 | `rr20::ident_all` | planned | 8 | False | launch_failure | n/a | n/a | 0.1642 |
| 95 | `rr20::backoff_fixed_best` | planned | 8 | False | launch_failure | n/a | n/a | 0.1642 |
| 96 | `rr80::p2_2_flag_opt` | retry | 1 | False | launch_failure | n/a | n/a | 0.165 |
| 97 | `rr80::p2_2_flag_opt` | retry | 1 | False | launch_failure | n/a | n/a | 0.1654 |
| 98 | `rr20::sort_best` | retry | 1 | False | launch_failure | n/a | n/a | 0.1649 |
| 99 | `rr20::sort_best` | retry | 1 | False | launch_failure | n/a | n/a | 0.1649 |
| 100 | `rr20::stock_common` | retry | 1 | False | launch_failure | n/a | n/a | 0.1655 |
| 101 | `rr20::stock_common` | retry | 1 | False | launch_failure | n/a | n/a | 0.1641 |
| 102 | `rr80::stock_common` | retry | 1 | False | launch_failure | n/a | n/a | 0.1646 |
| 103 | `rr80::stock_common` | retry | 1 | False | launch_failure | n/a | n/a | 0.1649 |
| 104 | `rr20::system_gate` | retry | 1 | False | launch_failure | n/a | n/a | 0.1653 |
| 105 | `rr20::system_gate` | retry | 1 | False | launch_failure | n/a | n/a | 0.1646 |
| 106 | `rr20::backoff_fixed_best` | retry | 1 | False | launch_failure | n/a | n/a | 0.1648 |
| 107 | `rr20::backoff_fixed_best` | retry | 1 | False | launch_failure | n/a | n/a | 0.165 |
| 108 | `rr80::backoff_fixed_best` | retry | 1 | False | launch_failure | n/a | n/a | 0.1652 |
| 109 | `rr80::backoff_fixed_best` | retry | 1 | False | launch_failure | n/a | n/a | 0.1661 |
| 110 | `rr80::system_gate` | retry | 1 | False | launch_failure | n/a | n/a | 0.1655 |
| 111 | `rr80::system_gate` | retry | 1 | False | launch_failure | n/a | n/a | 0.1675 |
| 112 | `rr80::sort_best` | retry | 1 | False | launch_failure | n/a | n/a | 0.1665 |
| 113 | `rr80::sort_best` | retry | 1 | False | launch_failure | n/a | n/a | 0.1662 |
| 114 | `rr20::p2_2_flag_opt` | retry | 1 | False | launch_failure | n/a | n/a | 0.1662 |
| 115 | `rr20::p2_2_flag_opt` | retry | 1 | False | launch_failure | n/a | n/a | 0.1652 |
| 116 | `rr80::ident_all` | retry | 1 | False | launch_failure | n/a | n/a | 0.1662 |
| 117 | `rr80::ident_all` | retry | 1 | False | launch_failure | n/a | n/a | 0.1653 |
| 118 | `rr20::ident_all` | retry | 1 | False | launch_failure | n/a | n/a | 0.1653 |
| 119 | `rr20::ident_all` | retry | 1 | False | launch_failure | n/a | n/a | 0.1654 |
