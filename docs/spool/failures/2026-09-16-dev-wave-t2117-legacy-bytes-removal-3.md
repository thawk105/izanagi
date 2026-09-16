---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-16
wave: dev-wave-t2117-legacy-bytes-removal
seq: 3
---

## 新規

### {{F:mutation-worktree-submodule-uninitialized}}. 変異 wrapper が作る使い捨て worktree は submodule が未初期化で baseline が全滅する [手順漏れ]

- 事象: `tools/mutation_worktree.py --commit <commit>` が作った使い捨て worktree で
  baseline が `27 errors` になり、harness が
  `baseline が緑でないため production write を開始しない: status=PARSE_ERROR` で中止した。
  失敗本文は `ValidationError: submodule is not initialized:
  external/ccbench/third_party/shirakami`。同じ spec・同じ runner が、submodule を初期化した
  wave worktree では baseline PASSED で完走している。
- 根本原因: `DW-C01` は「全新規 worktree を
  `python3 tools/dev_wave_submodule_init.py --worktree <ABSOLUTE>` で再帰初期化する」と定めるが、
  wrapper は worktree を**自分で作る**ため、親がその存在を知る前に harness が走り出す。
  親が初期化を挟む隙が手順上に無い。
- あわせて `--resume` は baseline を再走しない (`baseline=0 run(s)`)。前回の `PARSE_ERROR` を
  そのまま使うため、container を初期化してから resume しても回復しない。
- 恒久対応: `DW-C01` の初期化 tool を**wrapper が保持した container**
  (`<scratch-root>/.izanagi-mutation-worktree/repo`) へ当て、`--resume` ではなく
  `tools/mutation_harness.py --repo <container>` を**直接**起動する。
  container は wrapper が中止時に保持するので作り直しは要らない。
  DW-M05 が定める harness の固定 HEAD 束縛・`flock` 単一走行・signal 復元はこの経路でも効く。
- 再発検知: baseline の `status` が `PARSE_ERROR` で、job stdout に
  `submodule is not initialized:` が literal で出る。

## 再発

### F945

- **再発: 2026-09-16** — [T-2117] wave (test 1 file のみ変更) の受入で 2 走続けて同型が出た。
  1 走目 (tip `7d19ffbe4`) は 3 error (t1259 の `git ls-files --others` 30 秒 timeout 2 件、
  `test_s8c_preregistration_predicates.py` の real-repo lock 期限超過 1 件)、単独再走 8 passed。
  2 走目 (tip `6ae8d06da`) は **34 error** (t1259 が 29 件、s8c predicates が 5 件。原因は
  `git ls-files` / `git archive` の 30 秒 timeout と real-repo lock 期限超過)、同 tip の 2 file
  単独再走 (1578.nqsv) は **269 passed / 121.41 秒 / rc=0** で非再現。2 走目の投入時は同時受入が
  他に 1 本だったが、走行中に増えて終了時は 3 本だった。恒久対応は既報のまま変えず、
  timeout 拡大・stub 化・除外・gate 新設はしていない。

### F300

- **再発: 2026-09-16** — `共有木の事後検査に失敗: source/main 共有木の観測 bytes が変化した` を
  再び踏んだ。親は走行中に repo へ 1 byte も書いていない。原因は 2026-08-25 の 2 件と同じ
  **並行 wave の churn** である (この機体では wave worktree が 89 本)。
  **本エントリの 2026-08-25 追補 (対象 commit だけを持つ独立 clone を `--source-repo` へ渡す) を
  適用していれば防げた。** 適用しなかったのは、追補が予算超過で reference へ入らず
  本台帳だけに在るためである。追補が実務へ伝わっていないことの実例として記録する。
