# 発行 child の CPU profile (段 1 前の実測、2026-09-28)

- 取得: `tools/pegasus/dispatch_compute.py --task generic` (request 32525.nqsv、bnode、Elapse 212 秒) で
  `py-spy record --subprocesses --rate 50 --format raw` の下に
  `/usr/bin/python3.10 <~/.local/bin/pytest> -o pythonpath=. -q -p no:cacheprovider -p no:xdist
  orchestrator/tests/test_s8b_oracle_driver.py::test_t080_failed_launch_preserves_receipt_refusal` を単独走 (tree = local main 51f896352)。
  単独走なので共有 base は process 内 memo 経路、active_v2 key の builder が 1 回走る。
- 生データ: `prof-l-node-3.txt` (collapsed stack)、child の行だけ `child.txt` (process 名に `t080-current-runtime [` を含む行)。
- child 総 sample 4,313 (50 Hz ≈ 86 秒。D2253 診断の約 87 秒と一致)。

| 包含 sample | 関数 |
|---:|---|
| 4,280 | `search_repository` (s8b_holdout_freeze.py) — child CPU の 99 % |
| 3,280 | `_scan_one` |
| 465 | `_read_search_text` |
| 15 | `enumerate_repository_files` |
| 1,030 | draft_receipt |
| 1,985 | validate_draft (finalize 内の呼出しを含む) |
| 1,287 | finalize_receipt |
| 651 | verify_receipt |
| 631 | gate_check |

自己時間の上位 (child):

| sample | 行 |
|---:|---|
| 2,311 | `_scan_one` s8b_holdout_freeze.py:564 `if compiled[axis].search(text):` |
| 806 | `_scan_one` :559 `if required_literal is not None and required_literal not in text:` |
| 229 | `_read_search_text` :491 |
| 154 | `_scan_one` :562 `if axis_literal is not None and axis_literal not in text:` |
| 125+29 | `pathlib.read_bytes` |

## 再 profile (事前登録 1、実装後の最終 commit ad8c91ecf、2026-09-29)

- request 33654.nqsv、Elapse 165 秒 (段 1 前 212 秒)、`1 passed in 158.67s`。生データ `prof-b-node-2.txt`、child の行 `child-b.txt`。
- **child 総 sample 1,583 (≈ 32 秒) = 段 1 前 4,313 の 36.7 %** → 事前登録 1 の条件 (70 % 以下) を満たす。系列へ進む。
- 包含: search_repository 1,549、`_scan_one` 500 (前 3,280)、`_search_localized` 149、`_read_search_text` 509 (前 465)。
  phase: draft 359 (前 1,030)・validate 728 (前 1,985)・finalize 461 (前 1,287)・verify 233 (前 651)・gate_check 246 (前 631)。
- 自己時間上位: `_read_search_text` :492 250、`_text_contains` :519 164、pathlib.read_bytes 152、`_scan_one` :600 151、`_search_localized` :536 136。
  残る最大項は D512 が維持を定める全 file の read・decode。

## 段 1 前の読み

読み: child 内の `search_repository` 呼出しは約 13 回 (draft 3・validate 3・finalize 4 (validate 内包)・verify 1・gate_check 2 の見込み。
1 回 ≈ 6.6 秒)。1 回の中で `_scan_one` の軸 pass は 5 回 (rratio は holdout 2 + 陽性対照 1 で式が違い memo が効かない 3 回、skew・rmw は memo で各 1 回)。
fixture は計算ノード /tmp 上なので、D512 が実測した律速 (共有 FS の metadata 遅延) ではなく正規表現照合が支配する。
