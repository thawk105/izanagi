# [T-1431] 床値 pilot が完走し、床値の実測値が得られた (request 945229.nqsv)

## 要約

到達不能述語の修正 (worklog 916) を local main へ land した直後に床値 pilot を再投入し、
**12 セル全部が計測へ到達して完走した (driver_rc=0)。床値の実測値が初めて得られた。**

これまでの 3 回 (`926261` / `940170` / `944884`) はいずれも計測到達セル 0 だった。

## 環境・実行パラメータ

- **実行環境**: Pegasus, queue=gen_S, nodes=1, elapstim_req=10:00:00
- **投入元 commit**: `e540eca316ef4086847c797fb97fa312f02168c1` (land 直後の local main)
- **submission nonce**: `5dfef3f7f1981b5694889f7a0f9f270b`、request ID = `945229.nqsv`
- **投入コマンド**: `tools/pegasus/submit_floor.sh --confirm-irreversible-pilot-holdout`
  (先に `--dry-run` で qsub argv を確認した)
- **ccbench pin**: `511c9538e4e8efa54b45cda62e72389ed3b706ec`
- **protocol**: `protocol_sha256=2c8cf9be929d83653814ecf5f2d5ed134a2af89686d796b8144da2fd45dfa58a`
  (`n_sessions=8` / `reps=5` / `retry_slots_per_cell=2` / `extime_s=5` / `env_tag=pegasus` /
  `stock_configuration=stock_common` / `schedule_algorithm=round-permutation/v2`)
- **freeze**: `freeze_sha256=315b1eb83d6fbdc525448c3c96c66ab6013df72487f35d8fa519c27ba34bc688`
- **manifest**: `manifest_sha256=0e88486edfe47944f4d75f139860283132c60096c01d12eef25e92f737a309b8`
- **formula**: `s8b-floor-stats/v2`、`wired_min_rel_floor=0.03`、
  `scale_adequacy_rel_tolerance=0.10`
- **perf**: `mode=disabled, reason=nonzero-rc`。本機で perf を要求しない既定方針どおり
  blocker としない
- **所要**: job の Elapse で約 48 分 (待ち手の最終 poll で 2894 秒を観測)。
  driver 完了 epoch は 1787607728

## 床値の実測値 (floor 案)

**これは floor の「案」であって、何も発効していない。** `eligible_for_refreeze=false` は
`mode=pilot` によるもので、freeze への floor 書込みは別途の判断による。

| holdout | scalar_alt (全 pair の max) | scale_ref (m_stock) | machine_anomaly |
|---|---:|---:|---|
| `rr20` | 3.555e+04 | 1.185e+06 | (なし) |
| `rr80` | 4.551e+04 | 1.517e+06 | (なし) |

floor_pair は両 holdout とも全 5 pair
(`backoff_fixed_best` / `ident_all` / `p2_2_flag_opt` / `sort_best` / `system_gate`)
で scalar_alt と同値である。

## セル統計 (session-median の散らばり、n_valid は全セル 8)

| cell | m (median) | s (stdev) | cv |
|---|---:|---:|---:|
| `rr20::backoff_fixed_best` | 3.581e+06 | 9,511 | 0.002658 |
| `rr20::ident_all` | 1.183e+06 | 1.505e+04 | 0.01268 |
| `rr20::p2_2_flag_opt` | 2.555e+06 | 2.201e+04 | 0.008607 |
| `rr20::sort_best` | 1.204e+06 | 9,929 | 0.008259 |
| `rr20::stock_common` | 1.185e+06 | 6,434 | 0.00543 |
| `rr20::system_gate` | 1.259e+06 | 6,953 | 0.005529 |
| `rr80::backoff_fixed_best` | 6.845e+06 | 1.051e+04 | 0.001536 |
| `rr80::ident_all` | 1.526e+06 | 1.345e+04 | 0.008836 |
| `rr80::p2_2_flag_opt` | 7.206e+06 | 3.051e+04 | 0.004232 |
| `rr80::sort_best` | 1.528e+06 | 1.588e+04 | 0.01038 |
| `rr80::stock_common` | 1.517e+06 | 1.302e+04 | 0.008562 |
| `rr80::system_gate` | 3.132e+06 | 1.35e+04 | 0.004314 |

## 走行の健全性

- **12 セル × 8 session = 96 attempt がすべて `valid=True`。**
- **除外 session は 0 件** (理由別内訳も空)。
- **retry は 0 件。** 台帳の 96 行はすべて `kind=planned` で round 1〜8 に均等である。
  `retry_slots_per_cell=2` は 1 枠も使っていない。
- 各 attempt の所要は 26.79〜26.93 秒に収まっており、外乱の兆候はない。
- attempt 単位の CV は最大 0.03175 (`rr80::ident_all` round 4)、最小 0.001581。
- `machine_anomaly` セルは両 holdout とも無し。

## 一回性 key の消費

**今回は消費した。** admission root
(`.git/izanagi/s8b-holdout-admission-v1`) 配下に 2026-08-25 以降の file が 118 件できた。
計測に到達した以上これは設計どおりである。過去 3 回の試行はいずれも計測前に停止したため
消費が 0 枚であり、本試行が初の消費である。

## 直前の 3 回との違い

停止していた実体は、build 後検査が現行 CCBench pin では出現しえない
`CMakeCache.txt` の `masstree_SOURCE_DIR` を要求していたことだった (worklog 916)。
権威を「cache 入力 (A)」と「生成された build system の解決済み root (B)」の一致へ
張り替えた修正が入ったことで、`sort_best` セルが初めて build 後検査を通過した。
`sort-swo-oracle-pass-*.json` が 2 件 (rr20 / rr80 の sort_best) 発行されている。

## 証拠の所在

将来の official 床値 job の起動証明を止める holdout clean-scan の汚染を避けるため、
repo 外へ退避した。

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1431-floor-pilot-submit/evidence-bundle-945229/`
  - `run-dir/` = `result.json` / `result.md` / `manifest.json` / `journal.jsonl`
  - `job-staging/` = checkpoint、toolchain 実測値、SWO PASS receipt
  - `submission/` = 投入 receipt
  - `s8b-build-cache/` / `binaries/` = build 成果物
