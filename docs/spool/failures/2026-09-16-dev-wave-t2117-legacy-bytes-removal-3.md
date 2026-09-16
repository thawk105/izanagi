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

### F300

- **再発: 2026-09-16** — `共有木の事後検査に失敗: source/main 共有木の観測 bytes が変化した` を
  再び踏んだ。親は走行中に repo へ 1 byte も書いていない。原因は 2026-08-25 の 2 件と同じ
  **並行 wave の churn** である (この機体では wave worktree が 89 本)。
  **本エントリの 2026-08-25 追補 (対象 commit だけを持つ独立 clone を `--source-repo` へ渡す) を
  適用していれば防げた。** 適用しなかったのは、追補が予算超過で reference へ入らず
  本台帳だけに在るためである。追補が実務へ伝わっていないことの実例として記録する。
