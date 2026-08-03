---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-03
wave: dev-wave-t328-docs-externalize
seq: 2
---

## 新規

### {{F:raw-qsub-interpreter-false-red}}. 生 qsub の全走が interpreter 差で 2,201 件の偽赤を出した [計測汚染] [手順漏れ]

- 事象: [T-282] の残留計測で、job tmp の PBS script から
  `IZANAGI_TEST_TRIGGER=final python3 tools/run_tests.py` を直接呼んだところ、
  **116 failed / 2,085 errors** (request `878392`) になった。原因は計算ノードの既定 `python3` が
  3.10 未満で、`@dataclass(frozen=True, slots=True)` が
  `TypeError: dataclass() got an unexpected keyword argument 'slots'` で落ちること。
  interpreter を `python3.10` に固定しても、テストが `bash` 経由で起動する孫 process が
  PATH の `python3` を拾うため **19 failed** が残った (request `878395`)。
  `PATH` 先頭へ `python3` → `python3.10` の shim を置いて初めて **5,226 passed / rc=0**
  (request `878402`) になった。
- 根本原因: `tools/pegasus/dispatch_compute.py` は `_INTERPRETER_CANDIDATES`
  (`python3.10` 優先) で interpreter を選び `PATH` を張り替えてから子を起動するが、
  **その契約は dispatcher の内側にしか無く、生 qsub 経路には無い**。
  `DW-O18` は「nested subprocess の import path による偽赤を差分の回帰として扱わない」と
  結果側の規律を定めるだけで、投入側に interpreter を固定する義務が無い。
- 恒久対応: `tools/pegasus/dispatch_compute.py:122-126` の `_INTERPRETER_CANDIDATES` と
  `:407` の `export PATH="$(dirname "$selected"):$PATH"` を唯一の正規経路とし、
  親が計算ノードで pytest を走らせるときは `tools/run_tests.py` の自動 dispatch を使う。
  生 qsub を使う測定 script は同じ interpreter 選択と PATH 張り替えを写す。
  逐語の追加先は `DW-O18` だが、`docs/dev-wave/**` の予算逼迫 ([T-328]) で本 wave では入らない
  — 本エントリを暫定の正本とする。
- 再発検知: 生 qsub の全走が赤になったら、同じ対象を `tools/run_tests.py` の正規 dispatch で
  単独再走する (本件では `orchestrator/tests/test_t126_pegasus_tools.py` が
  **248 passed / rc=0** で、19 赤は再現しなかった)。再現しない赤は差分へ帰属しない。
