# [T-282] 残留の検出 — 全走前後の prefix 別実測

- 日時: 2026-08-03 / HEAD `e0b9073ade90dc59578ad30fa8c8ffbe312b9b4e`
- 実行: Pegasus gen_S 計算ノード `bnode005`、PBS request `878402`
- 手段: 恒久 tool は置かず、job tmp の一回限り PBS script で
  「全走前 snapshot → `IZANAGI_TEST_TRIGGER=final ... tools/run_tests.py` → 全走後 snapshot」を
  **同一 job・同一ノード**で実行した (段 2 プラン §6 の「実測だけで閉じる」案)
- 全走結果: **5,226 passed / 19 skipped / rc=0** (222.08s)
- snapshot 対象: (i) `/tmp` 直下の自 UID entry を `(st_dev, st_ino, path)` で採取、
  (ii) repo の `git status --porcelain=v1 -uall`
- bytes は `du -sb --apparent-size --one-file-system`

## 結果 1 — repo には残留しない

`git status --porcelain=v1 -uall` の**全走前後で差分ゼロ**。全走は worktree に untracked を
1 件も残さない。clean-tree gate と `git add -A` は汚れない。

## 結果 2 — `/tmp` には 226 entry / 約 5.74 GB が残る

全走前 0 entry (job 開始時点の `/tmp` は自 UID entry を持たない) → 全走後 226 entry。

| prefix | entries | bytes |
|---|---:|---:|
| `pytest-of-` | 1 | 5,701,129,893 |
| `izanagi-t126-submit-stage.` | 5 | 39,509,276 |
| `izanagi_s8atrigloop_` | 73 | 68,989 |
| `izanagi-t057-receipt-` | 2 | 25,489 |
| `izanagi_s4loop_` | 32 | 23,120 |
| `izanagi_s5sortloop_` | 15 | 12,777 |
| `izanagi_s6sweep_` | 10 | 11,142 |
| `izanagi_projection_` | 20 | 9,962 |
| `izanagi_s8a_` | 10 | 8,858 |
| `izanagi_s8ascreen_` | 1 | 3,276 |
| `izanagi_s5sortprop_` | 7 | 2,857 |
| `izanagi_s8asweep_` | 2 | 1,466 |
| `izanagi_s8afreq_` | 6 | 1,204 |
| `izanagi_s8aprov_` | 1 | 1,144 |
| `izanagi_s8atrigprop_` | 3 | 1,108 |
| `izanagi_p3-` | 3 | 408 |
| `izanagi_s6_` | 4 | 196 |
| `izanagi_apply_` (lock) | 3 | 0 |
| `izanagi-mutation-` (lock) | 28 | 0 |
| **合計** | **226** | **5,740,811,165** |

`<unclassified>` は 0 件。全 entry が既知の prefix に入った。

**99.3% は pytest 自身の `tmp_path` 木 (`/tmp/pytest-of-tanab`)** である。izanagi 側の寄与は
`izanagi-t126-submit-stage.*` の 39.5 MB (5 件 × 約 7.9 MB) が支配的で、残り 186 件は合計 166 KB。
lock ファイル 31 件は 0 bytes だが削除されずに残る。

## 結果 3 — job を跨いでは持ち越さない

全走の直後に**別 job** (`878404`) を同じ `bnode005` へ投入して確認したところ、
`/tmp/pytest-of-tanab` は**存在しなかった**。3 回の全走 (`bnode007` / `bnode042` / `bnode005`) は
いずれも全走前 snapshot が 0 entry である。したがって `/tmp` 残留は **job 内に閉じており、
ノードにも次の job にも持ち越さない**。

計算ノードの `/tmp` は tmpfs ではなく nvme 上の xfs (200 GB、空き 129 GB) であり、
5.74 GB の一時使用はメモリを圧迫しない。

## 判定

**[T-282] は閉じてよい。** 「残留の検出手段が無い」に対する答えは次である。

1. **repo 残留はゼロ** — 恒久 gate を置く動機が無い
2. **`/tmp` 残留は 1 全走あたり約 5.74 GB / 226 entry** だが **job 内に閉じる**ため、
   ノード運用上の危険は現時点で無い
3. 恒久 tool (`tools/measure_test_residue.py`) は**置かない**。段 2 プランと段 3 の両レンズが
   一致して過剰と判定した — `tools/pegasus/dispatch_compute.py` の task enum は
   `{tests, provenance}` の閉集合で、login node から計算ノードの `/tmp` は測れない。
   自動化には D105 supersede を伴う 4〜6 ファイル変更が要る (規律 5「盛らない」)
4. 再測が要るときは本 insight の PBS script (`t282-residue.sh`、
   `/work/1/SFC/tanab/dev-wave-jobs/t328-docs-externalize/`) を再利用する

## 測定中に踏んだ罠 (恒久対応が要る)

生 `qsub` から `python3 tools/run_tests.py` を呼ぶと、計算ノードの既定 `python3` が 3.10 未満のため
`TypeError: dataclass() got an unexpected keyword argument 'slots'` が nested subprocess で発生し、
**116 failed / 2,085 errors の偽赤**になった (request `878392`)。
interpreter を `python3.10` に固定しても、テストが `bash` 経由で起動する孫 process が
PATH の `python3` を拾うため **19 failed** が残った (request `878395`)。
`PATH` の先頭へ `python3` → `python3.10` の shim を置いて初めて緑になった (request `878402`)。

正規経路 (`python3 tools/run_tests.py <file>` の自動 dispatch) で
`orchestrator/tests/test_t126_pegasus_tools.py` を単独再走すると **248 passed / rc=0** であり、
19 赤は再現しない。`DW-O18` の「nested subprocess の import path による偽赤を差分の回帰として
扱わない」に該当する型であり、**生 qsub 側に interpreter 契約が無い**ことが原因である。
